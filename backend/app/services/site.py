"""站点配置与「那年今日」。"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import models as m
from ..schemas.schemas import SiteInfo

# 北京时间:所有时间口径统一,不依赖服务器时区
BEIJING = timezone(timedelta(hours=8))

SITE_DEFAULTS = SiteInfo()


def get_site(db: Session) -> SiteInfo:
    """settings 表里没有的键用默认值补,保证老站升级不变样。"""
    rows = db.scalars(
        select(m.Setting).where(m.Setting.key.like("site_%"))
    ).all()
    stored = {r.key: r.value for r in rows}
    data = SITE_DEFAULTS.model_dump()
    for key in data:
        if key in stored and stored[key]:
            data[key] = stored[key]
    return SiteInfo(**data)


def save_site(db: Session, info: SiteInfo) -> SiteInfo:
    for key, value in info.model_dump().items():
        row = db.get(m.Setting, key)
        if row is None:
            db.add(m.Setting(key=key, value=str(value)))
        else:
            row.value = str(value)
    db.commit()
    return get_site(db)


def get_setting(db: Session, key: str, default: str = "") -> str:
    row = db.get(m.Setting, key)
    return row.value if row else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(m.Setting, key)
    if row is None:
        db.add(m.Setting(key=key, value=value))
    else:
        row.value = value
    db.commit()


def get_on_this_day(db: Session, *, now: datetime | None = None) -> list[dict]:
    """往年同月日的随手记与相册照片(没数据就返回空,前台自然隐藏)。"""
    now = now or datetime.now(BEIJING)
    month, day = now.month, now.day
    out: list[dict] = []

    notes = db.scalars(select(m.Note).order_by(m.Note.ts.desc())).all()
    for note in notes:
        dt = datetime.fromtimestamp(note.ts, BEIJING)
        if dt.month == month and dt.day == day and dt.year < now.year:
            out.append({
                "kind": "note",
                "years_ago": now.year - dt.year,
                "emoji": note.emoji,
                "text": note.text,
                "mood": note.mood,
            })

    photos = db.scalars(
        select(m.Photo).where(m.Photo.shown == 1).order_by(m.Photo.ts.desc())
    ).all()
    for photo in photos:
        if not photo.shot_at:
            continue
        try:
            dt = datetime.strptime(photo.shot_at, "%Y-%m-%d")
        except ValueError:
            continue
        if dt.month == month and dt.day == day and dt.year < now.year:
            out.append({
                "kind": "photo",
                "years_ago": now.year - dt.year,
                "file": photo.file,
                "title": photo.title,
            })

    return out


def beijing_today() -> str:
    return datetime.now(BEIJING).strftime("%Y-%m-%d")


def now_ts() -> int:
    return int(time.time())
