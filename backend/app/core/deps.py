"""登录态依赖:会话校验 + 空闲超时 + 强制改密拦截。

cookie 里只放会话指纹,库里 sessions 表可撤销 —— 支持后台「踢下线」。
"""

from __future__ import annotations

import time

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core import keys as K
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


def must_change_password(db: Session) -> bool:
    """是否处于「必须先改密」状态。"""
    return site_svc.get_setting(db, K.KEY_MUST_CHANGE, "0") == "1"


def _validate_session(request: Request, db: Session) -> m.LoginSession:
    sid = current_sid(request)
    if not sid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")

    sess = db.get(m.LoginSession, sid)
    if sess is None or sess.revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "会话已失效")

    now = int(time.time())
    # 空闲超时(0 = 不自动登出)
    idle_min = int(site_svc.get_setting(db, K.KEY_IDLE_MINUTES, "60") or "60")
    if idle_min > 0 and now - sess.last_seen > idle_min * 60:
        sess.revoked = 1
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已超时")

    # 会话绝对有效期
    max_age = int(site_svc.get_setting(db, K.KEY_SESSION_HOURS, "168") or "168") * 3600
    if now - sess.created > max_age:
        sess.revoked = 1
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已过期")

    # 会话绑 IP(可在后台关闭)
    if site_svc.get_setting(db, K.KEY_BIND_IP, "0") == "1":
        if sess.ip and sess.ip != _client_ip(request):
            sess.revoked = 1
            db.commit()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录环境变化,请重新登录")

    sess.last_seen = now
    db.commit()
    return sess


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> m.LoginSession:
    """后台接口守卫:未登录 401,未改初始密码 403。

    强制改密在后端拦截 —— 前端跳转只是体验,真正拦住越权的是这里。
    使用 403 + 固定错误码,前端据此跳到改密页。
    """
    sess = _validate_session(request, db)

    if must_change_password(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "MUST_CHANGE_PASSWORD",
                "message": "首次登录必须修改密码后才能使用后台",
            },
        )
    return sess


def require_login(
    request: Request,
    db: Session = Depends(get_db),
) -> m.LoginSession:
    """仅要求登录,不检查改密状态(改密接口与 /me 用)。"""
    return _validate_session(request, db)


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
