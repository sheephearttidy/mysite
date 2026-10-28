"""认证:登录(密码 + 图形验证码)、登出、改密、会话管理。

沿用原库的密码哈希格式与 settings 键名,站主无需重置密码。
"""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..core.deps import _client_ip, audit, current_sid, require_admin
from ..core.security import (
    captcha_code,
    captcha_digest,
    new_session_id,
    password_strength_error,
    verify_password,
    hash_password,
)
from ..models import models as m
from ..services import site as site_svc

router = APIRouter()

CAPTCHA_TTL_S = 180


def _fail_state(db: Session, ip: str) -> m.LoginFail:
    row = db.get(m.LoginFail, ip)
    if row is None:
        row = m.LoginFail(ip=ip, count=0, blocked_until=0, last_ts=0)
        db.add(row)
        db.commit()
    return row


@router.get("/captcha.svg", tags=["认证"])
def captcha_svg(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    """纯标准库 SVG 验证码:一次性、3 分钟过期、答案哈希存 session。"""
    length = int(site_svc.get_setting(db, "sec_captcha_len", "4") or "4")
    length = max(3, min(length, 6))
    code = captcha_code(length)

    sid = current_sid(request) or new_session_id()
    # 答案存进 settings 表(按会话指纹索引),避免引入额外 session 中间件
    key = f"cap:{sid}"
    site_svc.set_setting(db, key, f"{captcha_digest(code)}|{int(time.time())}")

    import random

    rnd = random.Random(secrets.randbits(64))
    chars = []
    for i, ch in enumerate(code):
        x = 20 + i * 26 + rnd.randint(-3, 3)
        y = 34 + rnd.randint(-5, 5)
        rot = rnd.randint(-22, 22)
        size = rnd.randint(24, 30)
        chars.append(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="700" '
            f'fill="#2d2a32" font-family="monospace" '
            f'transform="rotate({rot} {x} {y})">{ch}</text>'
        )
    lines = []
    for _ in range(4):
        x1, y1 = rnd.randint(0, 140), rnd.randint(0, 50)
        x2, y2 = rnd.randint(0, 140), rnd.randint(0, 50)
        lines.append(
            f'<path d="M{x1} {y1} Q{rnd.randint(0,140)} {rnd.randint(0,50)} {x2} {y2}" '
            f'stroke="#ff6b9d" stroke-width="1.2" fill="none" opacity="0.55"/>'
        )
    dots = [
        f'<circle cx="{rnd.randint(2,138)}" cy="{rnd.randint(2,48)}" r="1.1" fill="#8a8494" opacity="0.5"/>'
        for _ in range(26)
    ]

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="50" viewBox="0 0 140 50">'
        '<rect width="140" height="50" rx="10" fill="#fff8ee"/>'
        + "".join(lines) + "".join(dots) + "".join(chars) + "</svg>"
    )
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Set-Cookie": (
                f"{settings.session_cookie}={sid}; Path=/; HttpOnly; "
                f"SameSite=Lax" + ("; Secure" if settings.cookie_secure else "")
            ),
        },
    )


@router.post("/login", tags=["认证"])
def login(
    payload: dict[str, Any],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ip = _client_ip(request)
    state = _fail_state(db, ip)

    now = int(time.time())
    if state.blocked_until > now:
        left = int((state.blocked_until - now) / 60) + 1
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f"失败次数过多,请 {left} 分钟后再试"
        )

    password = str(payload.get("password") or "")
    captcha = str(payload.get("captcha") or "")

    # 验证码校验(可在后台关闭)
    if site_svc.get_setting(db, "sec_captcha_on", "1") == "1":
        sid = current_sid(request) or ""
        stored = site_svc.get_setting(db, f"cap:{sid}", "")
        if not stored or "|" not in stored:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码已过期,请刷新")
        digest, issued = stored.split("|", 1)
        # 一次性:校验后立即删除
        db.query(m.Setting).filter(m.Setting.key == f"cap:{sid}").delete()
        db.commit()
        if now - int(issued) > CAPTCHA_TTL_S:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码已过期,请刷新")
        if not secrets.compare_digest(digest, captcha_digest(captcha)):
            _bump_fail(db, state, ip, now)
            audit(db, request, "captcha_fail", f"ip={ip}")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码错误")

    stored_hash = site_svc.get_setting(db, "admin_password", "")
    if not stored_hash or not verify_password(password, stored_hash):
        _bump_fail(db, state, ip, now)
        audit(db, request, "login_fail", f"ip={ip}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "密码错误")

    # 登录成功:清失败计数、换新会话(防会话固定)
    state.count = 0
    state.blocked_until = 0
    sid = new_session_id()
    db.add(m.LoginSession(
        sid=sid, ip=ip, ua=request.headers.get("user-agent", "")[:300],
        created=now, last_seen=now, revoked=0,
    ))
    db.commit()
    audit(db, request, "login_ok", f"ip={ip}")

    must_change = site_svc.get_setting(db, "must_change_pwd", "1") == "1"
    response.set_cookie(
        settings.session_cookie, sid,
        max_age=settings.session_max_age,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )
    return {"ok": True, "must_change": must_change}


def _bump_fail(db: Session, state: m.LoginFail, ip: str, now: int) -> None:
    """失败计数落库,达阈值封锁 IP。"""
    state.count += 1
    state.last_ts = now
    threshold = int(site_svc.get_setting(db, "sec_fail_limit", "5") or "5")
    minutes = int(site_svc.get_setting(db, "sec_block_min", "15") or "15")
    if state.count >= threshold:
        state.blocked_until = now + minutes * 60
        state.count = 0
    db.commit()


@router.post("/logout", tags=["认证"])
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, bool]:
    sid = current_sid(request)
    if sid:
        sess = db.get(m.LoginSession, sid)
        if sess is not None:
            sess.revoked = 1
            db.commit()
    response.delete_cookie(settings.session_cookie, path="/")
    return {"ok": True}


@router.get("/me", tags=["认证"])
def me(sess: m.LoginSession = Depends(require_admin)) -> dict[str, Any]:
    return {
        "ok": True,
        "sid": sess.sid,
        "ip": sess.ip,
        "created": sess.created,
        "last_seen": sess.last_seen,
    }


@router.post("/password", tags=["认证"])
def change_password(
    payload: dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
    sess: m.LoginSession = Depends(require_admin),
) -> dict[str, Any]:
    old = str(payload.get("old") or "")
    new = str(payload.get("new") or "")

    stored = site_svc.get_setting(db, "admin_password", "")
    if not verify_password(old, stored):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "原密码错误")
    err = password_strength_error(new)
    if err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, err)

    site_svc.set_setting(db, "admin_password", hash_password(new))
    site_svc.set_setting(db, "must_change_pwd", "0")
    # 改密后踢掉其他会话
    db.query(m.LoginSession).filter(m.LoginSession.sid != sess.sid).update({"revoked": 1})
    db.commit()
    audit(db, request, "password_change", "")
    return {"ok": True}


# ---------------- 会话管理 ----------------


@router.get("/security/sessions", tags=["后台"], dependencies=[Depends(require_admin)])
def list_sessions(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(m.LoginSession).where(m.LoginSession.revoked == 0).order_by(m.LoginSession.last_seen.desc())
    ).all()
    return [
        {"sid": r.sid[:8] + "…", "ip": r.ip, "ua": r.ua, "created": r.created, "last_seen": r.last_seen}
        for r in rows
    ]


@router.post("/security/revoke", tags=["后台"], dependencies=[Depends(require_admin)])
def revoke_session(request: Request, sid: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    sess = db.get(m.LoginSession, sid)
    if sess is not None:
        sess.revoked = 1
        db.commit()
        audit(db, request, "session_revoke", sid[:8])
    return {"ok": True}


@router.post("/security/revoke-all", tags=["后台"], dependencies=[Depends(require_admin)])
def revoke_all(request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    me_sid = current_sid(request)
    db.query(m.LoginSession).filter(m.LoginSession.sid != me_sid).update({"revoked": 1})
    db.commit()
    audit(db, request, "session_revoke_all", "")
    return {"ok": True}


# ---------------- 审计与封锁名单 ----------------


@router.get("/security/audit", tags=["后台"], dependencies=[Depends(require_admin)])
def audit_log(limit: int = 100, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    cap = int(site_svc.get_setting(db, "sec_audit_keep", "500") or "500")
    limit = max(1, min(limit, cap))
    rows = db.scalars(select(m.AuditLog).order_by(m.AuditLog.ts.desc()).limit(limit)).all()
    return [
        {"id": r.id, "ts": r.ts, "ip": r.ip, "action": r.action, "detail": r.detail}
        for r in rows
    ]


@router.delete("/security/audit", tags=["后台"], dependencies=[Depends(require_admin)])
def clear_audit(request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    db.query(m.AuditLog).delete()
    db.commit()
    audit(db, request, "audit_clear", "")
    return {"ok": True}


@router.get("/security/blocked", tags=["后台"], dependencies=[Depends(require_admin)])
def blocked_ips(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    now = int(time.time())
    rows = db.scalars(select(m.LoginFail).where(m.LoginFail.blocked_until > now)).all()
    return [
        {"ip": r.ip, "until": r.blocked_until, "left_s": r.blocked_until - now}
        for r in rows
    ]


@router.post("/security/unblock", tags=["后台"], dependencies=[Depends(require_admin)])
def unblock(request: Request, ip: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    row = db.get(m.LoginFail, ip)
    if row is not None:
        row.blocked_until = 0
        row.count = 0
        db.commit()
        audit(db, request, "unblock", ip)
    return {"ok": True}
