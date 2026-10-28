"""SQLAlchemy 模型 —— 与既有 SQLite 表结构一一对应。

原则:不改列名、不改类型、不加列。模型只是现有表的 Python 视图,
这样 FastAPI 可以直接读写老库,线上数据零迁移。
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ---------------- 内容类(后台可 CRUD) ----------------


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    percent: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    note: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(Text, nullable=False, default="serious")
    color: Mapped[str] = mapped_column(Text, nullable=False, default="teal")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TimelineItem(Base):
    __tablename__ = "timeline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(Text, nullable=False, default="🚀")
    time_label: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Stat(Base):
    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(Text, nullable=False, default="😄")
    number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(Text, nullable=False, default="")
    label: Mapped[str] = mapped_column(Text, nullable=False)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Work(Base):
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(Text, nullable=False, default="🛠️")
    cover: Mapped[str] = mapped_column(Text, nullable=False, default="pink")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    desc: Mapped[str] = mapped_column(Text, default="")
    pill: Mapped[str] = mapped_column(Text, default="进行中")
    link: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ProfileItem(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="info")
    emoji: Mapped[str] = mapped_column(Text, default="")
    label: Mapped[str] = mapped_column(Text, default="")
    value: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Honor(Base):
    __tablename__ = "honors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(Text, nullable=False, default="🏆")
    year: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    desc: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(Text, nullable=False, default="school")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(Text, nullable=False, default="✏️")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    mood: Mapped[str] = mapped_column(Text, default="teal")
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FriendLink(Base):
    __tablename__ = "friendlinks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    emoji: Mapped[str] = mapped_column(Text, default="🔗")
    desc: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    artist: Mapped[str] = mapped_column(Text, default="")
    emoji: Mapped[str] = mapped_column(Text, default="🎵")
    song_id: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------- 站点配置 ----------------


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


# ---------------- 相册 ----------------


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, default="")
    desc: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(Text, default="")
    shot_at: Mapped[str] = mapped_column(Text, default="")
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    shown: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------- 互动 ----------------


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, default="匿名")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, default="pink")
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(Text, default="")
    shown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reply: Mapped[str] = mapped_column(Text, default="")
    token: Mapped[str] = mapped_column(Text, default="")


class MessageThread(Base):
    __tablename__ = "message_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    msg_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="guest")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(Text, default="")
    shown: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(Text, default="")
    shown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answer: Mapped[str] = mapped_column(Text, default="")
    answered_ts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Doodle(Base):
    __tablename__ = "doodles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(Text, default="")
    shown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)


class Like(Base):
    __tablename__ = "likes"

    page: Mapped[str] = mapped_column(Text, primary_key=True)
    n: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Countdown(Base):
    __tablename__ = "countdowns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    emoji: Mapped[str] = mapped_column(Text, default="⏳")
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


# ---------------- 统计与安全 ----------------


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False, default="/")
    referer: Mapped[str] = mapped_column(Text, default="")
    ua: Mapped[str] = mapped_column(Text, default="")
    is_bot: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    city: Mapped[str] = mapped_column(Text, default="")
    is_new: Mapped[int] = mapped_column(Integer, default=1)
    dur_s: Mapped[int] = mapped_column(Integer, default=0)


class LoginFail(Base):
    __tablename__ = "login_fails"

    ip: Mapped[str] = mapped_column(Text, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocked_until: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_ts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AuditLog(Base):
    __tablename__ = "audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    ua: Mapped[str] = mapped_column(Text, default="")


class LoginSession(Base):
    __tablename__ = "sessions"

    sid: Mapped[str] = mapped_column(Text, primary_key=True)
    ip: Mapped[str] = mapped_column(Text, default="")
    ua: Mapped[str] = mapped_column(Text, default="")
    created: Mapped[int] = mapped_column(Integer, nullable=False)
    last_seen: Mapped[int] = mapped_column(Integer, nullable=False)
    revoked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
