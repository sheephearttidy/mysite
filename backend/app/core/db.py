"""数据库引擎与会话。

沿用既有 SQLite 文件,只读复用原表结构 —— 不重建、不迁移、不丢数据。
SQLAlchemy 2.x 同步引擎(项目规模下同步足够,避免 async 复杂度)。
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# check_same_thread=False: FastAPI 线程池里跨线程使用同一连接池需要
# as_posix():Windows 路径的反斜杠在 SQLite URL 里会被当转义,必须转正斜杠
engine = create_engine(
    "sqlite:///" + Path(settings.db_file).as_posix(),
    connect_args={"check_same_thread": False, "timeout": 15},
    future=True,
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record):  # noqa: ANN001
    """WAL 提升并发读;外键约束打开;busy_timeout 避免锁冲突直接报错。"""
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=15000")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI 依赖:每请求一个会话,结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """脚本/后台任务用:自动提交与回滚。"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
