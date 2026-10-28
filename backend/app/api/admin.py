"""后台运维:图片上传、数据导入导出、特效设置、面板聚合。

上传接口按真实文件头校验类型(防改扩展名传 webshell),与原实现一致。
"""

from __future__ import annotations

import io
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..core.deps import audit, require_admin
from ..models import models as m
from ..services import site as site_svc

router = APIRouter()

# 真实文件头 -> 扩展名
MAGIC = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
}
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
UPLOAD_DIR = Path(settings.upload_dir)


def _sniff_ext(head: bytes) -> str | None:
    for magic, ext in MAGIC.items():
        if head.startswith(magic):
            return ext
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


def _image_size(data: bytes) -> tuple[int, int]:
    """纯标准库读 PNG/JPEG/GIF/WebP 像素尺寸,不引 Pillow。"""
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) > 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) > 10:
        return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h = int.from_bytes(data[i + 5:i + 7], "big")
                w = int.from_bytes(data[i + 7:i + 9], "big")
                return w, h
            if marker in (0xD8, 0xD9):
                i += 2
                continue
            seg = int.from_bytes(data[i + 2:i + 4], "big")
            i += 2 + seg
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) > 30:
        fmt = data[12:16]
        if fmt == b"VP8 ":
            w = int.from_bytes(data[26:28], "little") & 0x3FFF
            h = int.from_bytes(data[28:30], "little") & 0x3FFF
            return w, h
        if fmt == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if fmt == b"VP8X":
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return w, h
    return 0, 0


@router.post("/upload", tags=["后台"], dependencies=[Depends(require_admin)])
async def upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "文件超过 8MB")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "空文件")

    # 以真实文件头为准,扩展名与内容不符时以内容为准
    real_ext = _sniff_ext(data[:16])
    if real_ext is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "只支持 PNG / JPEG / GIF / WebP")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d')}-{secrets.token_hex(6)}{real_ext}"
    target = UPLOAD_DIR / name
    target.write_bytes(data)

    width, height = _image_size(data)
    audit(db, request, "upload", name)
    return {
        "ok": True,
        "file": name,
        "path": f"/assets/uploads/{name}",
        "width": width,
        "height": height,
        "size": len(data),
    }


@router.get("/uploads", tags=["后台"], dependencies=[Depends(require_admin)])
def list_uploads() -> list[dict[str, Any]]:
    if not UPLOAD_DIR.is_dir():
        return []
    out = []
    for p in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            st = p.stat()
            out.append({
                "file": p.name,
                "path": f"/assets/uploads/{p.name}",
                "size": st.st_size,
                "mtime": int(st.st_mtime),
            })
    return out


@router.delete("/uploads/{name}", tags=["后台"], dependencies=[Depends(require_admin)])
def delete_upload(
    name: str, request: Request, db: Session = Depends(get_db)
) -> dict[str, bool]:
    # 防路径穿越:只允许纯文件名
    if "/" in name or "\\" in name or name.startswith("."):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "非法文件名")
    target = UPLOAD_DIR / name
    if not target.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    target.unlink()
    audit(db, request, "upload_delete", name)
    return {"ok": True}


# ---------------- 数据备份 ----------------


@router.get("/backup/export", tags=["后台"], dependencies=[Depends(require_admin)])
def export_data(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """全量导出 JSON。"""
    from ..services import content as content_svc

    out: dict[str, Any] = {
        "version": 5,
        "exported_at": int(time.time()),
        "site": site_svc.get_site(db).model_dump(),
        "settings": {
            r.key: r.value
            for r in db.scalars(select(m.Setting)).all()
            # 敏感项不导出:密码哈希、验证码临时答案、2FA 密钥
            if not r.key.startswith(("pass_hash", "cap:", "totp_"))
        },
    }
    for kind in content_svc.REGISTRY:
        rows = content_svc.list_items(db, kind)
        out[kind] = [
            {c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows
        ]
    out["messages"] = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in db.scalars(select(m.Message)).all()
    ]
    out["questions"] = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in db.scalars(select(m.Question)).all()
    ]
    out["doodles"] = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in db.scalars(select(m.Doodle)).all()
    ]
    out["notices"] = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in db.scalars(select(m.Notice)).all()
    ]
    out["countdowns"] = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in db.scalars(select(m.Countdown)).all()
    ]
    audit(db, request, "export", "")
    return out


@router.post("/backup/import", tags=["后台"], dependencies=[Depends(require_admin)])
def import_data(
    payload: dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """从 JSON 恢复:先清空再写入,单事务。"""
    if not isinstance(payload, dict):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "格式错误")

    from ..services import content as content_svc

    counts: dict[str, int] = {}
    try:
        for kind, (model, _) in content_svc.REGISTRY.items():
            if kind not in payload:
                continue
            db.query(model).delete()
            cols = {c.name for c in model.__table__.columns}
            n = 0
            for row in payload[kind]:
                if not isinstance(row, dict):
                    continue
                clean = {k: v for k, v in row.items() if k in cols}
                db.add(model(**clean))
                n += 1
            counts[kind] = n
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"导入失败:{exc}") from exc

    audit(db, request, "import", json.dumps(counts, ensure_ascii=False))
    return {"ok": True, "counts": counts}


# ---------------- 特效设置 ----------------


FX_KEYS = ("fx_enabled", "fx_mode", "fx_manual", "fx_motion")


@router.get("/fx", tags=["后台"], dependencies=[Depends(require_admin)])
def get_fx(db: Session = Depends(get_db)) -> dict[str, str]:
    return {k: site_svc.get_setting(db, k, d) for k, d in (
        ("fx_enabled", "1"), ("fx_mode", "auto"), ("fx_manual", ""), ("fx_motion", "1"),
    )}


@router.put("/fx", tags=["后台"], dependencies=[Depends(require_admin)])
def set_fx(payload: dict[str, Any], request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    for key in FX_KEYS:
        if key in payload:
            site_svc.set_setting(db, key, str(payload[key])[:20])
    audit(db, request, "fx_settings", "")
    return get_fx(db)


# ---------------- 面板聚合 ----------------


@router.get("/alerts", tags=["后台"], dependencies=[Depends(require_admin)])
def alerts(db: Session = Depends(get_db)) -> dict[str, int]:
    """侧边栏角标:待处理数量。"""
    def count(model, *where) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(model)
        for w in where:
            stmt = stmt.where(w)
        return db.scalar(stmt) or 0

    return {
        "messages": count(m.Message, m.Message.shown == 0),
        "questions": count(m.Question, m.Question.answer == ""),
        "doodles": count(m.Doodle, m.Doodle.shown == 0),
        "notices": count(m.Notice, m.Notice.active == 1),
    }
