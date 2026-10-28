"""内容接口:前台按页取数 + 后台通用 CRUD。

CRUD 挂在 `/api/content/{kind}`,与 `/api/messages`、`/api/health` 等
具体路径不冲突(泛型段不放在根上)。
新增类型只需在 services.content.REGISTRY 与下方 SCHEMAS 各加一行。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import require_admin
from ..schemas import schemas as s
from ..services import content as content_svc
from ..services import site as site_svc

router = APIRouter()

# 内容类型 -> (输入模型, 输出模型)
SCHEMAS: dict[str, tuple[type, type]] = {
    "skills": (s.SkillIn, s.SkillOut),
    "timeline": (s.TimelineIn, s.TimelineOut),
    "stats": (s.StatIn, s.StatOut),
    "works": (s.WorkIn, s.WorkOut),
    "profile": (s.ProfileIn, s.ProfileOut),
    "honors": (s.HonorIn, s.HonorOut),
    "notes": (s.NoteIn, s.NoteOut),
    "friendlinks": (s.FriendLinkIn, s.FriendLinkOut),
    "songs": (s.SongIn, s.SongOut),
    "photos": (s.PhotoIn, s.PhotoOut),
}


def _schema_pair(kind: str) -> tuple[type, type]:
    if kind not in SCHEMAS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"未知内容类型:{kind}")
    return SCHEMAS[kind]


# ---------------- 前台:按页取数 ----------------


@router.get("/page/{name}", tags=["前台"])
def api_page(name: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """只返回该页用到的字段,省流量。"""
    if name not in content_svc.PAGE_FIELDS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "未知页面")

    out: dict[str, Any] = {}
    for field in content_svc.PAGE_FIELDS[name]:
        if field == "site":
            out["site"] = site_svc.get_site(db).model_dump()
        elif field == "onthisday":
            out["onthisday"] = site_svc.get_on_this_day(db)
        else:
            items = content_svc.list_items(db, field, only_shown=(field == "photos"))
            _, out_cls = SCHEMAS[field]
            out[field] = [out_cls.model_validate(i).model_dump() for i in items]
    return out


@router.get("/content", tags=["前台"])
def api_content(db: Session = Depends(get_db)) -> dict[str, Any]:
    """全量内容:后台首屏一次拉齐。"""
    out: dict[str, Any] = {"site": site_svc.get_site(db).model_dump()}
    for kind, (_, out_cls) in SCHEMAS.items():
        items = content_svc.list_items(db, kind, only_shown=(kind == "photos"))
        out[kind] = [out_cls.model_validate(i).model_dump() for i in items]
    return out


# ---------------- 通用 CRUD ----------------


@router.get("/content/{kind}", tags=["内容"])
def list_kind(kind: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """公开列表(相册只返回已展示的)。"""
    _, out_cls = _schema_pair(kind)
    items = content_svc.list_items(db, kind, only_shown=(kind == "photos"))
    return [out_cls.model_validate(i).model_dump() for i in items]


@router.post(
    "/content/{kind}",
    status_code=status.HTTP_201_CREATED,
    tags=["后台"],
    dependencies=[Depends(require_admin)],
)
def create_kind(
    kind: str,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    in_cls, out_cls = _schema_pair(kind)
    try:
        parsed = in_cls.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    obj = content_svc.create_item(db, kind, parsed.model_dump())
    return out_cls.model_validate(obj).model_dump()


@router.put(
    "/content/{kind}/{item_id}",
    tags=["后台"],
    dependencies=[Depends(require_admin)],
)
def update_kind(
    kind: str,
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """部分更新:只校验并覆盖请求里出现的字段。"""
    in_cls, out_cls = _schema_pair(kind)

    obj = content_svc.get_item(db, kind, item_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")

    # 只对提交的字段做类型/范围校验:把现有值当作底稿合并后再验证
    merged = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    merged.update(payload)
    merged.pop("id", None)
    try:
        parsed = in_cls.model_validate(merged)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    # 仅写回请求里出现的字段,避免把未提交字段覆盖成默认值
    updates = {k: v for k, v in parsed.model_dump().items() if k in payload}
    obj = content_svc.update_item(db, kind, item_id, updates)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    return out_cls.model_validate(obj).model_dump()


@router.delete(
    "/content/{kind}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["后台"],
    dependencies=[Depends(require_admin)],
)
def delete_kind(kind: str, item_id: int, db: Session = Depends(get_db)) -> None:
    _schema_pair(kind)
    if not content_svc.delete_item(db, kind, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")


# ---------------- 站点信息 ----------------


@router.get("/site", tags=["前台"])
def get_site(db: Session = Depends(get_db)) -> dict[str, Any]:
    return site_svc.get_site(db).model_dump()


@router.put("/site", tags=["后台"], dependencies=[Depends(require_admin)])
def put_site(payload: dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        info = s.SiteInfo.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return site_svc.save_site(db, info).model_dump()
