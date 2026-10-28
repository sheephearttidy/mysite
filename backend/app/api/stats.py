"""访问统计:上报、看板聚合、CSV 导出。

口径与原实现一致:北京时间、趋势补零、爬虫单独计数、只存城市不存 IP。
"""

from __future__ import annotations

import csv
import io
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import _client_ip, require_admin
from ..models import models as m
from ..services.site import BEIJING, beijing_today

router = APIRouter()

# 只记录已知页面,防止扫描器刷爆库
KNOWN_PATHS = {
    "/", "/about.html", "/skills.html", "/works.html",
    "/campus.html", "/gallery.html", "/map.html", "/contact.html",
}

BOT_HINTS = (
    "bot", "spider", "crawl", "curl", "wget", "python-requests",
    "httpx", "go-http-client", "scrapy", "headless",
)


def _is_bot(ua: str) -> bool:
    low = ua.lower()
    return any(h in low for h in BOT_HINTS)


def _ua_label(ua: str) -> str:
    """极简浏览器/系统标签,不引第三方库。"""
    low = ua.lower()
    if "edg/" in low:
        browser = "Edge"
    elif "chrome/" in low:
        browser = "Chrome"
    elif "firefox/" in low:
        browser = "Firefox"
    elif "safari/" in low:
        browser = "Safari"
    else:
        browser = "其他"
    if "windows" in low:
        os_name = "Windows"
    elif "android" in low:
        os_name = "Android"
    elif "iphone" in low or "ipad" in low:
        os_name = "iOS"
    elif "mac os" in low:
        os_name = "macOS"
    elif "linux" in low:
        os_name = "Linux"
    else:
        os_name = "其他"
    return f"{browser} / {os_name}"


@router.post("/track", status_code=status.HTTP_202_ACCEPTED, tags=["统计"])
async def track(request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    """前台用 sendBeacon 上报,同一标签页会话只报一次。"""
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    path = str(payload.get("path") or "/")[:200]
    if path not in KNOWN_PATHS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "未知路径")

    ua = request.headers.get("user-agent", "")
    referer = str(payload.get("referer") or "")[:200]
    if referer:
        try:
            referer = referer.split("//", 1)[-1].split("/", 1)[0]
        except Exception:  # noqa: BLE001
            referer = ""

    now = int(time.time())
    db.add(m.Visit(
        day=beijing_today(),
        ts=now,
        path=path,
        referer=referer,
        ua=_ua_label(ua),
        is_bot=1 if _is_bot(ua) else 0,
        city="",
        is_new=int(payload.get("is_new", 1) or 1),
        dur_s=0,
    ))
    db.commit()
    return {"ok": True}


@router.post("/track/dur", status_code=status.HTTP_202_ACCEPTED, tags=["统计"])
async def track_duration(request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    """停留时长心跳。"""
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return {"ok": False}
    if not isinstance(payload, dict):
        return {"ok": False}
    dur = int(payload.get("dur") or 0)
    if dur <= 0 or dur > 86400:
        return {"ok": False}
    path = str(payload.get("path") or "/")[:200]
    row = db.scalars(
        select(m.Visit).where(m.Visit.path == path).order_by(m.Visit.ts.desc()).limit(1)
    ).first()
    if row is not None:
        row.dur_s = min(dur, 86400)
        db.commit()
    return {"ok": True}


@router.get("/stats/visits", tags=["后台"], dependencies=[Depends(require_admin)])
def visits_overview(days: int = 14, db: Session = Depends(get_db)) -> dict[str, Any]:
    """看板:今日/区间/累计、每日趋势(补零)、来源、UA、时段、城市。"""
    days = max(1, min(days, 365))
    today = beijing_today()
    since = (datetime.now(BEIJING) - timedelta(days=days - 1)).strftime("%Y-%m-%d")

    human = db.scalars(select(m.Visit).where(m.Visit.is_bot == 0)).all()
    bots = db.scalar(select(func.count()).select_from(m.Visit).where(m.Visit.is_bot == 1)) or 0

    today_n = sum(1 for v in human if v.day == today)
    range_n = sum(1 for v in human if v.day >= since)

    # 趋势补零:X 轴连续
    daily: list[dict[str, Any]] = []
    cursor = datetime.now(BEIJING) - timedelta(days=days - 1)
    by_day = Counter(v.day for v in human)
    for i in range(days):
        d = (cursor + timedelta(days=i)).strftime("%Y-%m-%d")
        daily.append({"day": d, "n": by_day.get(d, 0)})

    in_range = [v for v in human if v.day >= since]
    sources = Counter(v.referer or "直接访问" for v in in_range).most_common(8)
    uas = Counter(v.ua or "未知" for v in in_range).most_common(8)
    cities = Counter(v.city for v in in_range if v.city).most_common(10)

    hours = [0] * 24
    for v in in_range:
        try:
            hours[datetime.fromtimestamp(v.ts, BEIJING).hour] += 1
        except (OverflowError, OSError, ValueError):
            continue

    recent = sorted(human, key=lambda v: v.ts, reverse=True)[:20]

    return {
        "today": today_n,
        "range": range_n,
        "total": len(human),
        "bots": bots,
        "daily": daily,
        "sources": [{"name": k, "n": n} for k, n in sources],
        "agents": [{"name": k, "n": n} for k, n in uas],
        "hours": hours,
        "cities": [{"name": k, "n": n} for k, n in cities],
        "recent": [
            {
                "ts": v.ts, "path": v.path, "ua": v.ua,
                "referer": v.referer, "city": v.city, "dur_s": v.dur_s,
            }
            for v in recent
        ],
    }


@router.get("/stats/visits/csv", tags=["后台"], dependencies=[Depends(require_admin)])
def visits_csv(db: Session = Depends(get_db)) -> Response:
    """明细 CSV 导出。"""
    rows = db.scalars(select(m.Visit).order_by(m.Visit.ts.desc()).limit(5000)).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["时间", "日期", "路径", "来源", "浏览器/系统", "城市", "停留秒", "爬虫"])
    for v in rows:
        writer.writerow([
            datetime.fromtimestamp(v.ts, BEIJING).strftime("%Y-%m-%d %H:%M:%S"),
            v.day, v.path, v.referer, v.ua, v.city, v.dur_s, "是" if v.is_bot else "否",
        ])
    return Response(
        content="\ufeff" + buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="visits.csv"'},
    )


@router.get("/map", tags=["前台"])
def visit_map(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """来访地图:按城市聚合。"""
    rows = db.scalars(select(m.Visit).where(m.Visit.is_bot == 0)).all()
    counter = Counter(v.city for v in rows if v.city)
    return [{"city": k, "n": n} for k, n in counter.most_common()]
