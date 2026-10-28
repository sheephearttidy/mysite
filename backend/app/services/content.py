"""内容服务:通用 CRUD,按表配置驱动。

对应原 db.py 的 TABLE_SPECS 工厂化思路,但用 SQLAlchemy 表达更直接。
"""

from __future__ import annotations

import time
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import models as m

T = TypeVar("T")

# 表名 -> (模型, 排序键列表)
REGISTRY: dict[str, tuple[type, tuple[str, ...]]] = {
    "skills": (m.Skill, ("sort", "id")),
    "timeline": (m.TimelineItem, ("sort", "id")),
    "stats": (m.Stat, ("sort", "id")),
    "works": (m.Work, ("sort", "id")),
    "profile": (m.ProfileItem, ("sort", "id")),
    "honors": (m.Honor, ("sort", "id")),
    "notes": (m.Note, ("sort", "id")),
    "friendlinks": (m.FriendLink, ("sort", "id")),
    "songs": (m.Song, ("sort", "id")),
    "photos": (m.Photo, ("sort", "ts")),
}

# 页面 -> 需要的字段(与原 PAGE_FIELDS 一致)
PAGE_FIELDS: dict[str, tuple[str, ...]] = {
    "index": ("site", "stats", "onthisday"),
    "about": ("site", "profile", "honors", "songs"),
    "skills": ("site", "skills"),
    "works": ("site", "works"),
    "campus": ("site", "timeline", "notes"),
    "contact": ("site", "friendlinks"),
    "map": ("site",),
    "gallery": ("site",),
}


def list_items(db: Session, name: str, *, only_shown: bool = False) -> list[Any]:
    model, order = REGISTRY[name]
    stmt = select(model)
    if only_shown and hasattr(model, "shown"):
        stmt = stmt.where(model.shown == 1)
    for col in order:
        stmt = stmt.order_by(getattr(model, col))
    return list(db.scalars(stmt))


def get_item(db: Session, name: str, item_id: int) -> Any | None:
    model, _ = REGISTRY[name]
    return db.get(model, item_id)


def create_item(db: Session, name: str, data: dict[str, Any]) -> Any:
    model, _ = REGISTRY[name]
    payload = dict(data)
    # notes 与 photos 的时间戳由服务端生成,不接受客户端伪造
    if name == "notes":
        payload.setdefault("ts", int(time.time()))
    if name == "photos":
        payload.setdefault("ts", int(time.time()))
    obj = model(**payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_item(db: Session, name: str, item_id: int, data: dict[str, Any]) -> Any | None:
    obj = get_item(db, name, item_id)
    if obj is None:
        return None
    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_item(db: Session, name: str, item_id: int) -> bool:
    obj = get_item(db, name, item_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
