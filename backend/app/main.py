"""FastAPI 应用入口。

设计:
- 纯 REST,JSON 进出;前台静态资源与 SPA 由 nginx / StaticFiles 托管
- CORS 仅开发放开(线上同源)
- 统一错误形状 {"error": "..."},与原 Flask 版兼容
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import admin, auth, content, interact, stats
from .core.config import REPO_ROOT, settings

app = FastAPI(
    title="至尊杰的小窝 API",
    description="个人主页 REST 后端(FastAPI)",
    version="5.2.0",
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


# ---------------- 安全响应头 ----------------

# 前端是纯静态 SPA,样式在外部 CSS,脚本在外部 bundle,
# 所以可以收紧 CSP(不放行 inline script)。内联 style 由 React 生成,需保留 unsafe-inline。
_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob:; "
    "connect-src 'self'; "
    "frame-src https://i.y.qq.com; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'"
)

_SECURITY_HEADERS = {
    "Content-Security-Policy": _CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    """给响应加安全头。

    nginx 已在每个 location 统一下发同源安全头(HTML 由 nginx 直出,
    不经过本服务),线上若再发一份会出现重复头,浏览器取更严格的值,
    虽然安全但响应不规范。所以线上交给 nginx,本中间件只在
    直连 5200 调试(MYSITE_EMIT_SECURITY_HEADERS=1)时生效。
    """
    response = await call_next(request)
    if settings.emit_security_headers:
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
    return response


# ---------------- CSRF 防护 ----------------

# 只对这些方法校验 Origin/Referer(读操作无副作用)
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# 公开写接口不要求同源(访客从任意页面留言/提问都可能),但要求带 JSON Content-Type,
# 浏览器跨站表单无法伪造 application/json,天然挡住 CSRF。
_PUBLIC_WRITE = {
    "/api/track",
    "/api/track/dur",
    "/api/messages",
    "/api/questions",
    "/api/likes",
    "/api/login",
    "/api/logout",
    "/api/captcha.svg",
}


def _same_origin(request: Request) -> bool:
    """校验 Origin(优先)或 Referer 是否同源。

    同源判定按主机名:Origin 的主机必须与请求的 Host 一致。
    这样 imyxj.xyz 与 www.imyxj.xyz 各自访问各自都成立,
    而任何第三方域名的表单/脚本发起的写请求都会被拒。
    """
    from urllib.parse import urlparse

    host = (request.headers.get("host") or "").lower().split(":")[0]

    origin = request.headers.get("origin")
    if origin:
        try:
            o = urlparse(origin)
            origin_host = (o.hostname or "").lower()
        except ValueError:
            return False
        if not origin_host:
            return False
        # 同机不同端口(本地 Vite 5173 -> API 5100)也算同源
        if origin_host == host:
            return True
        # 回环地址等价:localhost 与 127.0.0.1 指向同一台机器,
        # 攻击者无法让浏览器产生跨站到回环的 Origin,放行安全
        if origin_host in ("127.0.0.1", "localhost", "::1") and host in (
            "127.0.0.1", "localhost", "::1"
        ):
            return True
        return False

    referer = request.headers.get("referer")
    if referer:
        try:
            r = urlparse(referer)
            referer_host = (r.hostname or "").lower()
        except ValueError:
            return False
        if referer_host == host:
            return True
        # 回环等价,同上
        return referer_host in ("127.0.0.1", "localhost", "::1") and host in (
            "127.0.0.1", "localhost", "::1"
        )

    # 两者都没有:可能是 curl / 脚本。写操作要求必须有之一,直接拒绝。
    return False


@app.middleware("http")
async def _csrf_guard(request: Request, call_next):
    """后台写操作强制同源,防跨站请求伪造。"""
    if request.method in _UNSAFE_METHODS:
        path = request.url.path
        # 公开互动接口 + 登录登出不校验 Origin(它们靠 JSON Content-Type 与限流防护)
        if path not in _PUBLIC_WRITE and not path.startswith("/api/messages/"):
            if not _same_origin(request):
                return JSONResponse(
                    status_code=403,
                    content={"error": "跨站请求被拒绝(Origin 校验失败)"},
                )
    return await call_next(request)


@app.exception_handler(HTTPException)
async def _http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    """统一错误形状 {"error": "..."},与原 Flask 版兼容。

    detail 是 dict 时(比如强制改密的 MUST_CHANGE_PASSWORD)原样透出,
    前端才能据此区分「没登录」和「必须改密」。
    """
    if isinstance(exc.detail, dict):
        body = dict(exc.detail)
        body.setdefault("error", body.get("message", "请求失败"))
        return JSONResponse(status_code=exc.status_code, content=body)
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """参数校验失败返回 422 + 可读文案,不吐堆栈。"""
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
    msg = first.get("msg", "参数不合法")
    return JSONResponse(
        status_code=422,
        content={"error": (loc + ": " if loc else "") + msg},
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
