"""认证:登录(密码 + 图形验证码)、登出、改密、会话与安全设置。

键名与线上历史库严格一致(pass_hash / must_change_pass / sec_captcha),
这样从 Flask 版本迁移过来时站主无需重置密码。
"""

from __future__ import annotations

import random
import secrets
import time
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core import keys as K
from ..core.config import settings
from ..core.db import get_db
from ..core.deps import (
    _client_ip,
    audit,
    current_sid,
    must_change_password,
    require_admin,
    require_login,
)
from ..core.security import (
    captcha_code,
    captcha_digest,
    hash_password,
    new_session_id,
    password_strength_error,
    verify_password,
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
def captcha_svg(request: Request, db: Session = Depends(get_db)) -> Response:
    """纯标准库 SVG 验证码:一次性、3 分钟过期、答案哈希存储。"""
    length = int(site_svc.get_setting(db, K.KEY_CAPTCHA_LEN, "4") or "4")
    length = max(3, min(length, 6))
    code = captcha_code(length)

    sid = current_sid(request) or new_session_id()
    site_svc.set_setting(
        db, K.CAPTCHA_PREFIX + sid, captcha_digest(code) + "|" + str(int(time.time()))
    )

    rnd = random.Random(secrets.randbits(64))
    chars = []
    for i, ch in enumerate(code):
        x = 20 + i * 26 + rnd.randint(-3, 3)
        y = 34 + rnd.randint(-5, 5)
        rot = rnd.randint(-22, 22)
        size = rnd.randint(24, 30)
        chars.append(
            '<text x="%d" y="%d" font-size="%d" font-weight="700" fill="#2d2a32" '
            'font-family="monospace" transform="rotate(%d %d %d)">%s</text>'
            % (x, y, size, rot, x, y, ch)
        )

    lines = []
    for _ in range(4):
        x1, y1 = rnd.randint(0, 140), rnd.randint(0, 50)
        x2, y2 = rnd.randint(0, 140), rnd.randint(0, 50)
        cx, cy = rnd.randint(0, 140), rnd.randint(0, 50)
        lines.append(
            '<path d="M%d %d Q%d %d %d %d" stroke="#ff6b9d" stroke-width="1.2" '
            'fill="none" opacity="0.55"/>' % (x1, y1, cx, cy, x2, y2)
        )

    dots = []
    for _ in range(26):
        dots.append(
            '<circle cx="%d" cy="%d" r="1.1" fill="#8a8494" opacity="0.5"/>'
            % (rnd.randint(2, 138), rnd.randint(2, 48))
        )

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="50" viewBox="0 0 140 50">'
        '<rect width="140" height="50" rx="10" fill="#fff8ee"/>'
        + "".join(lines) + "".join(dots) + "".join(chars) + "</svg>"
    )

    resp = Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )
    resp.set_cookie(
        settings.session_cookie, sid,
        max_age=settings.session_max_age,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )
    return resp


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
            status.HTTP_403_FORBIDDEN, "失败次数过多,请 %d 分钟后再试" % left
        )

    password = str(payload.get("password") or "")
    captcha = str(payload.get("captcha") or "")

    if site_svc.get_setting(db, K.KEY_CAPTCHA_ON, "1") == "1":
        sid = current_sid(request) or ""
        stored = site_svc.get_setting(db, K.CAPTCHA_PREFIX + sid, "")
        if not stored or "|" not in stored:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码已过期,请刷新")
        digest, issued = stored.split("|", 1)
        # 一次性:校验后立即删除
        db.query(m.Setting).filter(
            m.Setting.key == K.CAPTCHA_PREFIX + sid
        ).delete()
        db.commit()
        if now - int(issued) > CAPTCHA_TTL_S:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码已过期,请刷新")
        if not secrets.compare_digest(digest, captcha_digest(captcha)):
            _bump_fail(db, state, ip, now)
            audit(db, request, "captcha_fail", "ip=" + ip)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码错误")

    stored_hash = site_svc.get_setting(db, K.KEY_PASS_HASH, "")
    if not stored_hash or not verify_password(password, stored_hash):
        _bump_fail(db, state, ip, now)
        audit(db, request, "login_fail", "ip=" + ip)
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
    audit(db, request, "login_ok", "ip=" + ip)

    response.set_cookie(
        settings.session_cookie, sid,
        max_age=settings.session_max_age,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )
    return {"ok": True, "must_change": must_change_password(db)}


def _bump_fail(db: Session, state: m.LoginFail, ip: str, now: int) -> None:
    """失败计数落库,达阈值封锁 IP。"""
    state.count += 1
    state.last_ts = now
    threshold = int(site_svc.get_setting(db, K.KEY_FAIL_THRESHOLD, "5") or "5")
    minutes = int(site_svc.get_setting(db, K.KEY_BLOCK_MINUTES, "15") or "15")
    if state.count >= threshold:
        state.blocked_until = now + minutes * 60
        state.count = 0
    db.commit()


@router.post("/logout", tags=["认证"])
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, bool]:
    sid = current_sid(request)
    if sid:
        sess = db.get(m.LoginSession, sid)
        if sess is not None:
            sess.revoked = 1
            db.commit()
    response.delete_cookie(settings.session_cookie, path="/")
    return {"ok": True}


@router.get("/me", tags=["认证"])
def me(
    sess: m.LoginSession = Depends(require_login),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """当前会话。未改密也能调 —— 前端据此决定是否跳改密页。"""
    return {
        "ok": True,
        "sid": sess.sid[:8] + "...",
        "ip": sess.ip,
        "created": sess.created,
        "last_seen": sess.last_seen,
        "must_change": must_change_password(db),
    }


@router.post("/password", tags=["认证"])
def change_password(
    payload: dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
    sess: m.LoginSession = Depends(require_login),
) -> dict[str, Any]:
    """修改密码。

    用 require_login 而非 require_admin —— 否则「必须改密」状态下
    连改密接口自己都会被拦死,用户永远出不来。
    """
    old = str(payload.get("old") or "")
    new = str(payload.get("new") or "")

    stored = site_svc.get_setting(db, K.KEY_PASS_HASH, "")
    if not verify_password(old, stored):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "原密码错误")

    min_len = int(site_svc.get_setting(db, K.KEY_PASS_MINLEN, "8") or "8")
    err = password_strength_error(new, min_len=min_len)
    if err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, err)

    if verify_password(new, stored):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "新密码不能与当前密码相同")

    site_svc.set_setting(db, K.KEY_PASS_HASH, hash_password(new))
    site_svc.set_setting(db, K.KEY_MUST_CHANGE, "0")
    # 改密后踢掉其他会话
    db.query(m.LoginSession).filter(m.LoginSession.sid != sess.sid).update({"revoked": 1})
    db.commit()
    audit(db, request, "password_change", "")
    return {"ok": True}


# ---------------- 会话管理 ----------------


@router.get("/security/sessions", tags=["后台"], dependencies=[Depends(require_admin)])
def list_sessions(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(m.LoginSession)
        .where(m.LoginSession.revoked == 0)
        .order_by(m.LoginSession.last_seen.desc())
    ).all()
    return [
        {
            "sid": r.sid[:8] + "...", "ip": r.ip, "ua": r.ua,
            "created": r.created, "last_seen": r.last_seen,
        }
        for r in rows
    ]


@router.post("/security/revoke", tags=["后台"], dependencies=[Depends(require_admin)])
def revoke_session(
    request: Request, sid: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
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


# ---------------- 审计与封锁 ----------------


@router.get("/security/audit", tags=["后台"], dependencies=[Depends(require_admin)])
def audit_log(limit: int = 100, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    cap = int(site_svc.get_setting(db, K.KEY_AUDIT_KEEP, "500") or "500")
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


# ---------------- 安全设置 ----------------

# 对外字段名(前端用) -> (settings 键, 最小值, 最大值)
# 必须显式映射:GET 返回短名,POST 若直接拿短名去查 settings 会永远匹配不上,
# 接口返回 200 但一个字段都没写进去。
SEC_NUMERIC_FIELDS: dict[str, tuple[str, int, int]] = {
    "captcha_len": (K.KEY_CAPTCHA_LEN, 3, 6),
    "fail_threshold": (K.KEY_FAIL_THRESHOLD, 1, 50),
    "block_minutes": (K.KEY_BLOCK_MINUTES, 1, 1440),
    "session_hours": (K.KEY_SESSION_HOURS, 1, 720),
    "idle_minutes": (K.KEY_IDLE_MINUTES, 0, 1440),
    "audit_keep": (K.KEY_AUDIT_KEEP, 50, 5000),
    "pass_minlen": (K.KEY_PASS_MINLEN, 6, 64),
    "pass_classes": (K.KEY_PASS_CLASSES, 1, 4),
}

# 开关型字段:短名 -> settings 键
SEC_BOOL_FIELDS: dict[str, str] = {
    "captcha": K.KEY_CAPTCHA_ON,
    "bind_ip": K.KEY_BIND_IP,
}


def _read_security(db: Session) -> dict[str, Any]:
    """读出全部安全设置,键名用前端短名。"""
    out: dict[str, Any] = {
        name: site_svc.get_setting(db, key, str(default))
        for name, (key, default) in {
            "captcha_len": (K.KEY_CAPTCHA_LEN, 4),
            "fail_threshold": (K.KEY_FAIL_THRESHOLD, 5),
            "block_minutes": (K.KEY_BLOCK_MINUTES, 15),
            "session_hours": (K.KEY_SESSION_HOURS, 168),
            "idle_minutes": (K.KEY_IDLE_MINUTES, 60),
            "audit_keep": (K.KEY_AUDIT_KEEP, 500),
            "pass_minlen": (K.KEY_PASS_MINLEN, 8),
            "pass_classes": (K.KEY_PASS_CLASSES, 2),
        }.items()
    }
    out["captcha"] = site_svc.get_setting(db, K.KEY_CAPTCHA_ON, "1")
    out["bind_ip"] = site_svc.get_setting(db, K.KEY_BIND_IP, "0")
    return out


@router.get("/security/settings", tags=["后台"], dependencies=[Depends(require_admin)])
def security_settings(db: Session = Depends(get_db)) -> dict[str, Any]:
    """安全设置一览(后台面板用)。"""
    return _read_security(db)


@router.post("/security/settings", tags=["后台"], dependencies=[Depends(require_admin)])
def update_security_settings(
    request: Request,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """更新安全设置,带范围校验。

    只处理 payload 里出现的字段,未提交的保持不变。
    """
    changed: list[str] = []

    for name, (key, lo, hi) in SEC_NUMERIC_FIELDS.items():
        if name not in payload:
            continue
        try:
            val = int(payload[name])
        except (TypeError, ValueError):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "%s 必须是数字" % name
            )
        if not lo <= val <= hi:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "%s 必须在 %d~%d 之间" % (name, lo, hi)
            )
        site_svc.set_setting(db, key, str(val))
        changed.append(name)

    for name, key in SEC_BOOL_FIELDS.items():
        if name not in payload:
            continue
        raw = payload[name]
        on = str(raw) in ("1", "true", "True", "on", "yes")
        site_svc.set_setting(db, key, "1" if on else "0")
        changed.append(name)

    if not changed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "没有可更新的字段"
        )

    audit(db, request, "security_settings", ",".join(changed))
    return _read_security(db)
