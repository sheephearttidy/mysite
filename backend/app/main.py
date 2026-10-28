"""FastAPI 应用入口。

设计:
- 纯 REST,JSON 进出;前台静态资源与 SPA 由 nginx / StaticFiles 托管
- CORS 仅开发放开(线上同源)
- 统一错误形状 {"error": "..."},与原 Flask 版兼容
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import admin, auth, content, interact, stats
from .core.config import REPO_ROOT, settings

app = FastAPI(
    title="至尊杰的小窝 API",
    description="个人主页 REST 后端(FastAPI)",
    version="5.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
    """不把堆栈泄露给客户端。"""
    return JSONResponse(status_code=500, content={"error": "服务器内部错误"})


# ---------------- 路由挂载 ----------------

app.include_router(content.router, prefix="/api", tags=["内容"])
app.include_router(interact.router, prefix="/api", tags=["互动"])
app.include_router(stats.router, prefix="/api", tags=["统计"])
app.include_router(auth.router, prefix="/api", tags=["认证"])
app.include_router(admin.router, prefix="/api/admin", tags=["后台"])


@app.get("/api/health", tags=["运维"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}


# ---------------- 静态资源 ----------------

# 上传的图片(由 nginx 直出也可以,这里兜底)
_uploads = Path(settings.upload_dir)
if _uploads.is_dir():
    app.mount("/assets/uploads", StaticFiles(directory=str(_uploads)), name="uploads")

# 前端构建产物。注意:SPA 需要「深链回退」——
# 直接 StaticFiles(html=True) 只会把 / 映射到 index.html,
# /about 这类 history 路由会 404。所以这里用自定义路由:
# 先尝试命中真实文件,找不到就返回 index.html 交给前端路由处理。
_dist = Path(settings.frontend_dist)

if _dist.is_dir():

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        # API 路径没匹配到路由时应该返回 JSON 404,而不是 HTML
        if full_path.startswith(("api/", "admin/", "assets/uploads/")):
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = (_dist / full_path).resolve()
        # 防路径穿越:必须仍在 dist 目录内
        if (
            full_path
            and candidate.is_file()
            and str(candidate).startswith(str(_dist.resolve()))
        ):
            return FileResponse(candidate)

        index = _dist / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
