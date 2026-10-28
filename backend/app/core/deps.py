"""登录态依赖:会话校验 + 空闲超时 + 远程踢下线。

cookie 里只放会话指纹,库里 sessions 表可撤销 —— 支持后台「踢下线」。
"""

from __future__ import annotations

import time

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..models import models as m
from ..services import site as site_svc


def _client_ip(request: Request) -> str:
    """nginx 已用 $remote_addr 覆盖 X-Forwarded-For,这里取它即可。"""
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""


def current_sid(request: Request) -> str | None:
    return request.cookies.get(settings.session_cookie)


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> m.LoginSession:
    """未登录或会话失效一律 401,不做重定向(纯 API)。"""
    sid = current_sid(request)
    if not sid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")

    sess = db.get(m.LoginSession, sid)
    if sess is None or sess.revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "会话已失效")

    now = int(time.time())
    # 空闲超时(0 = 不自动登出)
    idle_min = int(site_svc.get_setting(db, "sec_idle_min", "60") or "60")
    if idle_min > 0 and now - sess.last_seen > idle_min * 60:
        sess.revoked = 1
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已超时")

    # 会话绝对有效期
    max_age = int(site_svc.get_setting(db, "sec_session_hours", "168") or "168") * 3600
    if now - sess.created > max_age:
        sess.revoked = 1
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已过期")

    # 会话绑 IP:IP 变了视为会话被搬走
    if sess.ip and sess.ip != _client_ip(request):
        sess.revoked = 1
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录环境变化,请重新登录")

    sess.last_seen = now
    db.commit()
    return sess


def audit(db: Session, request: Request, action: str, detail: str = "") -> None:
    """敏感操作留痕。"""
    db.add(m.AuditLog(
        ts=int(time.time()),
        ip=_client_ip(request),
        action=action,
        detail=detail[:500],
        ua=request.headers.get("user-agent", "")[:300],
    ))
    db.commit()
