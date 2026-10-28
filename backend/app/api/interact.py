"""互动接口:留言墙(多轮对话)、提问箱、涂鸦墙、点赞。

公开写入接口全部带限流 + 审核默认不展示,防刷防垃圾。
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import _client_ip, audit, require_admin
from ..core.security import limiter, new_guest_token
from ..models import models as m
from ..schemas import schemas as s
from ..services import site as site_svc

router = APIRouter()

MSG_COLORS = ("pink", "yellow", "teal", "purple", "orange", "blue")


def _clean(text: str, limit: int) -> str:
    return " ".join(text.split())[:limit]


# ---------------- 留言墙 ----------------


@router.get("/messages", tags=["互动"])
def list_messages(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """只返回审核通过的留言,附公开的对话线程。"""
    msgs = db.scalars(
        select(m.Message).where(m.Message.shown == 1).order_by(m.Message.ts.desc()).limit(200)
    ).all()
    out: list[dict[str, Any]] = []
    for msg in msgs:
        threads = db.scalars(
            select(m.MessageThread)
            .where(m.MessageThread.msg_id == msg.id, m.MessageThread.shown == 1)
            .order_by(m.MessageThread.ts)
        ).all()
        item = s.MessageOut.model_validate(msg).model_dump()
        item["threads"] = [s.ThreadOut.model_validate(t).model_dump() for t in threads]
        # 游客凭证绝不下发
        item.pop("ip", None)
        out.append(item)
    return out


@router.post("/messages", status_code=status.HTTP_201_CREATED, tags=["互动"])
def create_message(
    payload: s.MessageIn,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ip = _client_ip(request)
    if not limiter.allow(f"msg:{ip}", limit=3, window_s=120):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "发言太快,歇一会儿")

    body = _clean(payload.body, 140)
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "留言不能为空")

    color = payload.color if payload.color in MSG_COLORS else "pink"
    msg = m.Message(
        name=_clean(payload.name, 20) or "匿名",
        body=body,
        color=color,
        ts=int(time.time()),
        ip=ip,
        shown=0,  # 默认待审核
        token=new_guest_token(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    # 凭证只在这里下发一次,留言人凭它追问
    return {"ok": True, "id": msg.id, "token": msg.token, "pending": True}


@router.post("/messages/{mid}/follow", status_code=status.HTTP_201_CREATED, tags=["互动"])
def follow_up(
    mid: int,
    payload: s.ThreadIn,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """留言人凭凭证追问。"""
    ip = _client_ip(request)
    if not limiter.allow(f"follow:{ip}", limit=5, window_s=300):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "操作太频繁")

    msg = db.get(m.Message, mid)
    if msg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "留言不存在")
    if not msg.token or msg.token != payload.token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "凭证无效")

    body = _clean(payload.body, 140)
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "内容不能为空")

    thread = m.MessageThread(
        msg_id=mid, role="guest", body=body, ts=int(time.time()), ip=ip, shown=0
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return {"ok": True, "id": thread.id, "pending": True}


# ---------------- 提问箱 ----------------


@router.get("/questions", tags=["互动"])
def list_questions(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """只返回已回答并公开的问题。"""
    rows = db.scalars(
        select(m.Question)
        .where(m.Question.shown == 1, m.Question.answer != "")
        .order_by(m.Question.answered_ts.desc())
        .limit(100)
    ).all()
    return [s.QuestionOut.model_validate(q).model_dump() for q in rows]


@router.post("/questions", status_code=status.HTTP_201_CREATED, tags=["互动"])
def create_question(
    payload: s.QuestionIn,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ip = _client_ip(request)
    if not limiter.allow(f"q:{ip}", limit=1, window_s=60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "60 秒内只能提一个问题")

    body = _clean(payload.body, 200)
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "问题不能为空")

    q = m.Question(body=body, ts=int(time.time()), ip=ip, shown=0, answer="")
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"ok": True, "id": q.id, "pending": True}


# ---------------- 点赞 ----------------


@router.get("/likes", tags=["互动"])
def get_likes(db: Session = Depends(get_db)) -> dict[str, int]:
    rows = db.scalars(select(m.Like)).all()
    return {r.page: r.n for r in rows}


@router.post("/likes", tags=["互动"])
def add_like(payload: s.LikeIn, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    ip = _client_ip(request)
    if not limiter.allow(f"like:{ip}", limit=20, window_s=60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "太频繁了")

    row = db.get(m.Like, payload.page)
    if row is None:
        row = m.Like(page=payload.page, n=1)
        db.add(row)
    else:
        row.n += 1
    db.commit()
    return {"ok": True, "page": row.page, "n": row.n}


# ---------------- 公告与倒计时 ----------------


@router.get("/notices/active", tags=["互动"])
def active_notices(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(m.Notice).where(m.Notice.active == 1).order_by(m.Notice.ts.desc())
    ).all()
    return [{"id": r.id, "body": r.body, "ts": r.ts} for r in rows]


@router.get("/countdowns/active", tags=["互动"])
def active_countdowns(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(m.Countdown).where(m.Countdown.active == 1).order_by(m.Countdown.target)
    ).all()
    return [{"id": r.id, "title": r.title, "target": r.target, "emoji": r.emoji} for r in rows]


# ---------------- 后台:审核 ----------------


@router.get("/messages/admin", tags=["后台"], dependencies=[Depends(require_admin)])
def admin_messages(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(m.Message).order_by(m.Message.ts.desc()).limit(300)).all()
    return [
        {
            "id": r.id, "name": r.name, "body": r.body, "color": r.color,
            "ts": r.ts, "shown": r.shown, "ip": r.ip, "reply": r.reply,
        }
        for r in rows
    ]


@router.post(
    "/messages/{mid}/mod", tags=["后台"], dependencies=[Depends(require_admin)]
)
def mod_message(
    mid: int, request: Request, action: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """action: approve / hide / delete"""
    msg = db.get(m.Message, mid)
    if msg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "留言不存在")
    if action == "approve":
        msg.shown = 1
    elif action == "hide":
        msg.shown = 2
    elif action == "delete":
        db.query(m.MessageThread).filter(m.MessageThread.msg_id == mid).delete()
        db.delete(msg)
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "未知操作")
    db.commit()
    audit(db, request, f"message_{action}", f"id={mid}")
    return {"ok": True}


@router.get("/questions/admin", tags=["后台"], dependencies=[Depends(require_admin)])
def admin_questions(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(m.Question).order_by(m.Question.ts.desc()).limit(300)).all()
    return [
        {
            "id": r.id, "body": r.body, "ts": r.ts, "shown": r.shown,
            "answer": r.answer, "answered_ts": r.answered_ts, "ip": r.ip,
        }
        for r in rows
    ]


@router.post(
    "/questions/{qid}/mod", tags=["后台"], dependencies=[Depends(require_admin)]
)
def answer_question(
    qid: int,
    request: Request,
    answer: str = "",
    action: str = "approve",
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    q = db.get(m.Question, qid)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "问题不存在")
    if action == "delete":
        db.delete(q)
    else:
        if answer:
            q.answer = _clean(answer, 500)
            q.answered_ts = int(time.time())
        if action == "approve" and q.answer:
            q.shown = 1
        elif action == "hide":
            q.shown = 2
    db.commit()
    audit(db, request, f"question_{action}", f"id={qid}")
    return {"ok": True}
