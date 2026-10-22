# ============================================================
# 我的小窝 · 后台管理系统
# Flask + SQLite,轻量零依赖数据库
# ============================================================

import os
import io
import json
import re
import time
import uuid
import shutil
import base64
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, flash, send_from_directory,
                   make_response)

import db
import captcha
import geo
import totp as totp_mod

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 后台静态资源(CSS/JS)放在 admin/static,不经过 Jinja 渲染。
# 必须作为构造参数传入:Flask 在 __init__ 里就注册了静态路由,
# 之后再改 app.static_url_path 是无效的。
app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, "static"),
            static_url_path="/admin/static")

app.secret_key = os.environ.get("MYSITE_SECRET_KEY", os.urandom(24))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True      # 只走 HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True    # 禁止 JS 读取
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
# 全局上限按上传放宽,但普通 JSON 接口另有更严格的检查(见 before_request)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

JSON_MAX_BYTES = 64 * 1024   # 普通 JSON 请求体上限 64KB

# 本站对外域名(v2.3 Origin/Referer 校验用,防跨站伪造写请求)
SITE_ORIGIN = os.environ.get("MYSITE_SITE_ORIGIN", "https://imyxj.xyz")


@app.before_request
def verify_write_origin():
    """写操作(POST/PUT/DELETE)必须来自本站:Origin 优先,Referer 兜底。

    浏览器发起的跨站表单/请求一定会带 Origin 或 Referer,两者都缺失的
    只有服务器间的调用(curl 等),这类请求本来就没有浏览器会话,直接放行
    (真正的写接口还有 @login_required 挡着)。
    """
    if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
        return None
    origin = request.headers.get("Origin", "")
    if origin:
        if origin.rstrip("/") != SITE_ORIGIN:
            db.add_audit("csrf_block", client_ip(),
                         f"跨站写被拒:{origin} {request.path}")
            return jsonify(error="非法来源(Origin 校验失败)"), 403
        return None
    ref = request.headers.get("Referer", "")
    if ref:
        m = re.match(r"^[a-z]+://([^/]+)", ref)
        host = m.group(1) if m else ""
        if host and host != request.host:
            db.add_audit("csrf_block", client_ip(),
                         f"跨站写被拒:{ref[:80]} {request.path}")
            return jsonify(error="非法来源(Referer 校验失败)"), 403
    return None


@app.before_request
def limit_json_body():
    """除图片上传外,请求体一律不得超过 64KB(防内存放大)"""
    if request.path == "/api/upload":
        return None
    if request.content_length and request.content_length > JSON_MAX_BYTES:
        return jsonify(error="请求体太大了"), 413
    return None


@app.after_request
def security_headers(resp):
    """Flask 渲染页统一加安全响应头(前台静态页由 nginx 的 snippet 负责)"""
    from flask import g
    if resp.mimetype and resp.mimetype.startswith("text/html"):
        resp.headers.setdefault(
            "Content-Security-Policy",
            CSP_POLICY.format(nonce=getattr(g, "csp_nonce", "")))
        # 后台页绝不能进任何缓存,否则 nonce 会串页
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

ADMIN_USER = os.environ.get("MYSITE_ADMIN_USER", "admin")

DB_PATH = os.path.join(BASE_DIR, "data", "mysite.db")


@app.context_processor
def inject_asset_ver():
    """给静态资源加版本号,改了 CSS/JS 后浏览器能立刻拿到新的。

    取 app.py + 静态文件的最大 mtime,任何一次部署都会让版本号变化。
    """
    return {"asset_ver": ASSET_VER}


def _compute_asset_ver() -> str:
    newest = 0.0
    watch = [os.path.abspath(__file__),
             os.path.join(BASE_DIR, "db.py"),
             os.path.join(BASE_DIR, "captcha.py")]
    for root, _dirs, files in os.walk(app.static_folder):
        watch.extend(os.path.join(root, f) for f in files)
    for p in watch:
        try:
            newest = max(newest, os.path.getmtime(p))
        except OSError:
            pass
    return str(int(newest))


ASSET_VER = _compute_asset_ver()

# ---------------- v2.3 CSP nonce 基建 ----------------
# 每个请求一把随机 nonce,模板内联 <script nonce="{{ csp_nonce }}"> 放行,
# 其余内联/外站脚本一律被 CSP 拦下。页面不缓存 → nonce 不会复用。


@app.before_request
def make_csp_nonce():
    from flask import g
    g.csp_nonce = base64.b64encode(os.urandom(18)).decode()


@app.context_processor
def inject_csp_nonce():
    from flask import g
    return {"csp_nonce": getattr(g, "csp_nonce", "")}


# 前台静态站由 nginx 直出,CSP 只需要罩住 Flask 渲染的后台页
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'"
)

# 上传目录:放在静态站下面,前台可直接引用
WEBROOT = os.path.dirname(BASE_DIR)                       # /var/www/mysite
UPLOAD_DIR = os.path.join(WEBROOT, "assets", "uploads")
UPLOAD_URL = "/assets/uploads"

# 只允许这几种图片,且校验真实文件头(防改扩展名的 webshell)
ALLOWED_EXT = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg",
               "gif": "gif", "webp": "webp"}
MAGIC = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 单张图 5MB

# 简单防爆破:失败次数落库(重启不丢),阈值和封锁时长可在后台调
# 旧的内存版 _failed 已废弃,统一走 db.get_fail / db.bump_fail


def client_ip() -> str:
    """取真实客户端 IP。

    nginx 用 `proxy_set_header X-Real-IP $remote_addr` 覆盖写入(客户端伪造无效),
    X-Forwarded-For 已被 nginx 改为 $remote_addr,这里只作兜底。
    """
    ip = request.headers.get("X-Real-IP")
    if ip:
        return ip.strip()
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # 取最后一跳(由可信代理追加),而不是客户端可伪造的第一段
        return xff.split(",")[-1].strip()
    return request.remote_addr or "x"


# ---------------- 鉴权 ----------------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            if request.path.startswith("/api/"):
                return jsonify(error="unauthorized"), 401
            return redirect(url_for("login", next=request.path))

        # 会话是否被远程踢下线
        sid = session.get("sid")
        if sid and db.session_revoked(sid):
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify(error="session_revoked"), 401
            flash("这个登录已被踢下线,请重新登录", "error")
            return redirect(url_for("login"))

        # v2.3 可选:会话绑定登录 IP,cookie 被偷到别的网络也用不了
        if sid and db.get_sec("sec_bind_ip") == "1":
            bound = session.get("ip")
            if bound and bound != client_ip():
                db.revoke_session(sid)
                session.clear()
                db.add_audit("ip_mismatch", client_ip(),
                             f"会话 IP 不一致(登录于 {bound}),已作废")
                if request.path.startswith("/api/"):
                    return jsonify(error="ip_mismatch"), 401
                flash("登录环境变了,为了安全请重新登录", "error")
                return redirect(url_for("login"))

        # 空闲超时自动登出
        try:
            idle_limit = int(db.get_sec("sec_idle_minutes")) * 60
        except (TypeError, ValueError):
            idle_limit = 3600
        now = int(time.time())
        last = session.get("last_seen", now)
        if idle_limit > 0 and now - last > idle_limit:
            if sid:
                db.revoke_session(sid)
            session.clear()
            db.add_audit("session_idle", client_ip(), "空闲超时自动登出",
                         request.headers.get("User-Agent", ""))
            if request.path.startswith("/api/"):
                return jsonify(error="idle_timeout"), 401
            flash("太久没操作,已经自动登出了", "error")
            return redirect(url_for("login"))

        session["last_seen"] = now
        if sid:
            db.touch_session(sid)
        return f(*args, **kwargs)
    return wrapper


def check_admin_password(pwd: str) -> bool:
    """密码哈希存在数据库 settings 表里"""
    return db.verify_password(pwd, db.get_pass_hash() or "")


def rate_limit_ok(ip: str) -> bool:
    """是否未被封锁"""
    _, blocked_until = db.get_fail(ip)
    return blocked_until <= time.time()


def record_fail(ip: str, reason: str = "密码错误"):
    """记一次失败,达到阈值就封锁"""
    try:
        threshold = int(db.get_sec("sec_fail_threshold"))
        minutes = int(db.get_sec("sec_block_minutes"))
    except (TypeError, ValueError):
        threshold, minutes = 5, 15
    threshold = max(1, threshold)
    cnt, blocked = db.bump_fail(ip, threshold, minutes * 60)
    ua = request.headers.get("User-Agent", "")
    if blocked > time.time():
        db.add_audit("login_block", ip, f"失败 {threshold} 次,封锁 {minutes} 分钟", ua)
    else:
        db.add_audit("login_fail", ip, f"{reason}({cnt}/{threshold})", ua)


def clear_fail(ip: str):
    db.clear_fails(ip)


# ---------------- 前台 API(公开,只读) ----------------

@app.get("/api/content")
def api_content():
    """前台一次性拉取所有可管理内容"""
    return jsonify(
        skills=db.get_skills(),
        timeline=db.get_timeline(),
        stats=db.get_stats(),
        works=db.get_works(),
        profile=db.get_profile(),
        honors=db.get_honors(),
        notes=db.get_notes(),
        friendlinks=db.get_friendlinks(),
    )


# 每个页面需要的数据:拆分多页后,各页只拉自己那部分
PAGE_FIELDS = {
    "index": ("stats",),
    "about": ("profile", "honors"),
    "skills": ("skills",),
    "works": ("works",),
    "campus": ("timeline", "notes"),
    "contact": ("friendlinks",),
}


@app.get("/api/page/<name>")
def api_page(name: str):
    """按页拉取数据:只返回该页用到的字段,省流量"""
    if name not in PAGE_FIELDS:
        return jsonify(error="未知页面"), 404
    out = {}
    for f in PAGE_FIELDS[name]:
        out[f] = getattr(db, f"get_{f}")()
    return jsonify(**out)


@app.get("/api/health")
def api_health():
    return jsonify(ok=True, time=datetime.now(timezone.utc).isoformat())


# ---------------- 访问统计 ----------------

# 只记这些页面路径,避免被扫描器刷爆数据库
TRACK_PATHS = {
    "/", "/index.html",
    "/about", "/about.html",
    "/skills", "/skills.html",
    "/works", "/works.html",
    "/campus", "/campus.html",
    "/map", "/map.html",
    "/contact", "/contact.html",
}
_BEIJING = timezone(timedelta(hours=8))


def _clean_referer(raw: str) -> str:
    """把 referer 裁成域名,顺便过滤掉自己站内跳转"""
    if not raw:
        return ""
    try:
        from urllib.parse import urlparse
        host = (urlparse(raw).hostname or "").lower()
    except Exception:
        return ""
    if not host:
        return ""
    # 自己站内的跳转不算来源
    if host in ("imyxj.xyz", "www.imyxj.xyz", "SERVER_IP", "127.0.0.1", "localhost"):
        return ""
    return host[:100]


@app.post("/api/track")
def track_visit():
    """前台每次打开页面调一次。公开接口,只记已知页面,防扫描器刷库。
    v1.10:返回 vid 供停留时长补报;接收 is_new(前端 localStorage 匿名标识)。"""
    body = request.get_json(silent=True) or {}
    path = (body.get("path") or "/")[:100]
    if path not in TRACK_PATHS:
        return jsonify(ok=False, error="只统计首页"), 400

    ua = request.headers.get("User-Agent", "")[:300]
    ref = _clean_referer(request.headers.get("Referer", ""))

    # 城市:geo 有内存缓存(同 IP 只查一次),未命中时首次查库可能慢几十毫秒,
    # 但 track 是 sendBeacon 异步发的,不阻塞页面
    ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() \
        or request.remote_addr or ""
    city = geo.locate(ip) if ip else ""
    now = datetime.now(_BEIJING)
    try:
        vid = db.record_visit(path=path, referer=ref, ua=ua,
                              day=now.strftime("%Y-%m-%d"), ts=int(time.time()),
                              city=city,
                              is_new=1 if body.get("is_new", 1) else 0,
                              dur_s=0)
    except Exception:
        return jsonify(ok=False), 200   # 统计失败不影响用户
    return jsonify(ok=True, vid=vid)


@app.post("/api/track/dur")
def track_duration():
    """v1.10:离开/隐藏时补报停留时长。vid + dur_s,轻校验。"""
    body = request.get_json(silent=True) or {}
    try:
        vid = int(body.get("vid") or 0)
    except (TypeError, ValueError):
        vid = 0
    if vid <= 0:
        return jsonify(ok=False), 400
    db.update_visit_dur(vid, body.get("dur_s") or 0)
    return jsonify(ok=True)


@app.get("/api/map")
def api_map():
    """访客城市分布(公开):返回 [{city, count}],不暴露 IP"""
    return jsonify(cities=db.get_visit_cities())


# ---------------- 留言板(公开) ----------------

@app.get("/api/messages")
def api_messages_public():
    """前台留言墙:只返回展示中的,新的在前"""
    return jsonify(messages=db.list_messages_public(30))


@app.post("/api/messages")
def api_messages_post():
    """写留言:公开,带轻防刷(同 IP 60 秒只能发一条)"""
    body = request.get_json(silent=True) or {}
    ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() \
        or request.remote_addr or ""
    # 轻防刷:同 IP 60s 一条(内存表,重启清零,够用)
    import time as _t
    now = _t.time()
    last = _MSG_LAST.get(ip, 0)
    if now - last < 60:
        wait = int(60 - (now - last))
        return jsonify(ok=False, error=f"发太快啦,休息 {wait} 秒再发~"), 429
    _MSG_LAST[ip] = now

    r = db.add_message(name=body.get("name") or "",
                       body=body.get("body") or "",
                       color=body.get("color") or "",
                       ip=ip)
    if not r.get("ok"):
        return jsonify(r), 400
    db.add_audit("message_new", ip,
                 f"留言 id={r['id']}",
                 request.headers.get("User-Agent", "")[:200])
    return jsonify(r)


# 进程内防刷表(ip -> 上次发留言时间)
_MSG_LAST = {}


@app.get("/api/likes")
def api_likes_get():
    """全部页面点赞数(公开)"""
    return jsonify(likes=db.like_counts(), total=db.like_total())


@app.post("/api/likes")
def api_likes_post():
    """点赞 +1(公开;同一浏览器会话对同一页只加一次,由前端 localStorage 控制)"""
    body = request.get_json(silent=True) or {}
    r = db.add_like(body.get("page") or "")
    if not r.get("ok"):
        return jsonify(r), 400
    return jsonify(r)


# ---------------- 公告与倒计时(公开) ----------------

@app.get("/api/notices/active")
def api_notices_active():
    """前台:获取当前生效的公告"""
    return jsonify(notice=db.get_active_notice())


@app.get("/api/countdowns/active")
def api_countdowns_active():
    """前台:获取当前生效的倒计时"""
    return jsonify(countdown=db.get_active_countdown())


@app.get("/api/stats/visits")
@login_required
def visit_stats():
    days = request.args.get("days", 30, type=int)
    days = max(1, min(days, 365))
    return jsonify(db.get_visit_stats(days))


# ---------------- 后台页面 ----------------

@app.get("/admin/login")
def login():
    if session.get("user"):
        return redirect(url_for("admin"))
    # 初始密码还没改过 → 登录页显示初始密码提示
    return render_template("login.html",
                           initial=db.must_change_password(),
                           captcha_on=_captcha_on(),
                           ip=client_ip())


@app.get("/admin/static/js/login.js")
def _no_store_login_js():
    """login.js 引用了带 nonce 的内联数据源,v2.3 起禁缓存"""
    resp = send_from_directory(os.path.join(BASE_DIR, "static", "js"), "login.js")
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _captcha_on() -> bool:
    return db.get_sec("sec_captcha") == "1"


@app.get("/admin/captcha.svg")
def captcha_image():
    """生成一张新验证码,答案摘要和签发时间写进 session"""
    try:
        length = int(db.get_sec("sec_captcha_len"))
    except (TypeError, ValueError):
        length = 4
    length = max(3, min(length, 6))

    cap = captcha.make_captcha(length)
    session["cap_digest"] = captcha.answer_digest(cap["text"])
    session["cap_at"] = time.time()
    session["cap_token"] = cap["token"]

    resp = app.response_class(cap["svg"], mimetype="image/svg+xml")
    # 绝不能缓存验证码,否则刷新拿到同一张
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.post("/admin/login")
def login_post():
    ip = client_ip()
    ua = request.headers.get("User-Agent", "")
    pwd = request.form.get("password", "")
    given = request.form.get("captcha", "")

    # 1. 是否在封锁中
    if not rate_limit_ok(ip):
        _, blocked_until = db.get_fail(ip)
        left = int(blocked_until - time.time())
        db.add_audit("login_blocked", ip, "封锁期内尝试登录", ua)
        flash(f"尝试太频繁啦,请 {max(1, left // 60)} 分钟后再来", "error")
        return redirect(url_for("login"))

    # 2. 验证码(开关可关,但默认开)
    if _captcha_on():
        ok, why = captcha.verify_captcha(
            given, session.get("cap_digest"), session.get("cap_at"))
        # 验证码一次性:不管对错都作废
        session.pop("cap_digest", None)
        session.pop("cap_at", None)
        session.pop("cap_token", None)
        if not ok:
            record_fail(ip, f"验证码错误:{why}")
            flash(why, "error")
            return redirect(url_for("login"))

    # 3. 密码
    if not check_admin_password(pwd):
        record_fail(ip, "密码错误")
        time.sleep(min(2.0, max(0.0,
                     float(db.get_sec("sec_login_delay") or 1.0))))
        flash("密码不对哦,再想想?🤔", "error")
        return redirect(url_for("login"))

    # 3.5 两步验证(v2.0):密钥存在 → 需要 6 位动态码
    totp_secret = db.get_setting("totp_secret") or ""
    if totp_secret:
        code = request.form.get("totp", "")
        if not totp_mod.verify(totp_secret, code):
            record_fail(ip, "2FA 动态码错误")
            flash("动态码不对,看看手机验证器再输一次", "error")
            return redirect(url_for("login"))

    # 4. 成功
    clear_fail(ip)
    sid = base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip("=")
    session.clear()                     # 防会话固定攻击
    session["user"] = ADMIN_USER
    session["sid"] = sid
    session["last_seen"] = int(time.time())
    session["ip"] = ip                  # v2.3:记录登录 IP,供可选绑定用
    session.permanent = True
    # 会话有效期按后台设置走(默认 168 小时 = 7 天)
    try:
        hours = max(1, int(db.get_sec("sec_session_hours")))
    except (TypeError, ValueError):
        hours = 168
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=hours)
    db.add_session(sid, ip, ua)
    db.add_audit("login_ok", ip, "登录成功" +
                 ("(2FA)" if totp_secret else ""), ua)
    db.purge_old_sessions(30)
    return redirect(url_for("admin"))


@app.get("/admin/logout")
def logout():
    sid = session.get("sid")
    if sid:
        db.revoke_session(sid)
    db.add_audit("logout", client_ip(), "主动退出",
                 request.headers.get("User-Agent", ""))
    session.clear()
    return redirect(url_for("login"))


@app.get("/admin")
@app.get("/admin/")
@login_required
def admin():
    data = {
        "skills": db.get_skills(),
        "timeline": db.get_timeline(),
        "stats": db.get_stats(),
        "works": db.get_works(),
        "profile": db.get_profile(),
        "honors": db.get_honors(),
        "notes": db.get_notes(),
        "friendlinks": db.get_friendlinks(),
    }
    # 初始密码还没改过 → 前端弹窗提示修改
    return render_template("admin.html", data=data,
                           must_change=db.must_change_password())


# ---------------- 改密码 ----------------

# v2.3 常见弱口令黑名单(全小写比对,命中即拒)
WEAK_PASSWORDS = {
    "123456", "12345678", "123456789", "1234567890",
    "password", "password1", "qwerty", "abc123", "111111", "000000",
    "admin", "admin123", "root", "toor", "passw0rd", "p@ssw0rd",
    "iloveyou", "dragon", "monkey", "letmein", "welcome",
    "qwertyuiop", "1q2w3e4r", "1qaz2wsx", "asd123", "a123456",
    "88888888", "66666666", "5201314", "147258369", "987654321",
}


def check_password_policy(pwd: str) -> str | None:
    """按后台可调策略校验新密码。返回 None=通过,否则返回拒绝原因。"""
    try:
        min_len = max(6, min(64, int(db.get_sec("sec_pass_minlen") or 8)))
        min_class = max(1, min(4, int(db.get_sec("sec_pass_classes") or 2)))
    except (TypeError, ValueError):
        min_len, min_class = 8, 2

    if len(pwd) < min_len:
        return f"密码至少 {min_len} 位(后台可调)"
    classes = sum([
        bool(re.search(r"[a-z]", pwd)),
        bool(re.search(r"[A-Z]", pwd)),
        bool(re.search(r"[0-9]", pwd)),
        bool(re.search(r"[^A-Za-z0-9]", pwd)),
    ])
    if classes < min_class:
        return f"密码至少要包含 {min_class} 种字符(小写/大写/数字/符号)"
    if pwd.lower() in WEAK_PASSWORDS:
        return "这是常见弱密码,换一个"
    return None


@app.post("/api/password")
@login_required
def change_password():
    """已登录状态下修改自己的密码"""
    body = request.get_json(force=True, silent=True) or {}
    old_pwd = body.get("old", "")
    new_pwd = body.get("new", "")

    if not db.verify_password(old_pwd, db.get_pass_hash() or ""):
        return jsonify(error="旧密码不对哦"), 400
    why = check_password_policy(new_pwd)
    if why:
        return jsonify(error=why), 400
    if new_pwd == old_pwd:
        return jsonify(error="新密码不能和旧密码一样"), 400
    if new_pwd == db.DEFAULT_ADMIN_PASS:
        return jsonify(error="不能还用 admin 当密码!换一个"), 400

    db.set_pass_hash(db.hash_password(new_pwd))
    db.clear_must_change()
    db.add_audit("pass_change", client_ip(), "修改后台密码",
                 request.headers.get("User-Agent", ""))
    session.clear()  # 改完强制重新登录,用新密码
    return jsonify(ok=True)


# ---------------- 安全管理 API(需登录) ----------------

@app.get("/api/security/settings")
@login_required
def get_sec_settings():
    return jsonify(db.get_sec_all())


# ---------------- 两步验证(2FA / TOTP) ----------------

@app.get("/api/security/2fa/setup")
@login_required
def totp_setup():
    """生成新密钥(暂存 pending,不启用);返回 otpauth URI 给前端画二维码"""
    secret = totp_mod.generate_secret()
    db.set_setting("totp_pending", secret)
    uri = totp_mod.otpauth_uri(secret, "zhishengjie@imyxj.xyz")
    db.add_audit("2fa_setup", client_ip(), "生成 2FA 密钥待确认",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, uri=uri)


@app.post("/api/security/2fa/enable")
@login_required
def totp_enable():
    """输入手机上的 6 位码确认绑定;成功即启用"""
    body = request.get_json(silent=True) or {}
    pending = db.get_setting("totp_pending") or ""
    if not pending:
        return jsonify(error="请先生成密钥"), 400
    if not totp_mod.verify(pending, body.get("code") or ""):
        return jsonify(error="动态码不对,再试试"), 400
    db.set_setting("totp_secret", pending)
    db.set_setting("totp_pending", "")
    db.add_audit("2fa_enable", client_ip(), "两步验证已启用",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True)


@app.post("/api/security/2fa/disable")
@login_required
def totp_disable():
    """关闭 2FA(需要当前有效动态码,防偷会话的人顺手关掉)"""
    body = request.get_json(silent=True) or {}
    secret = db.get_setting("totp_secret") or ""
    if not secret:
        return jsonify(error="尚未启用两步验证"), 400
    if not totp_mod.verify(secret, body.get("code") or ""):
        return jsonify(error="动态码不对,无法关闭"), 400
    db.set_setting("totp_secret", "")
    db.add_audit("2fa_disable", client_ip(), "两步验证已关闭",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True)


@app.get("/api/security/2fa/status")
@login_required
def totp_status():
    """当前 2FA 状态(只回开关,不回密钥)"""
    return jsonify(enabled=bool(db.get_setting("totp_secret")),
                   pending=bool(db.get_setting("totp_pending")))


@app.post("/api/security/settings")
@login_required
def save_sec_settings():
    """保存安全设置。只接受已知的键,并做范围校验。"""
    body = request.get_json(force=True, silent=True) or {}

    # 键 -> (最小值, 最大值)
    limits = {
        "sec_captcha": (0, 1),
        "sec_captcha_len": (3, 6),
        "sec_fail_threshold": (1, 50),
        "sec_block_minutes": (1, 1440),
        "sec_session_hours": (1, 720),
        "sec_idle_minutes": (0, 1440),
        "sec_audit_keep": (50, 5000),
        # v2.3 新增
        "sec_pass_minlen": (6, 64),
        "sec_pass_classes": (1, 4),
        "sec_login_delay": (0, 10),
        "sec_bind_ip": (0, 1),
    }
    changed = []
    for key, (lo, hi) in limits.items():
        if key not in body:
            continue
        try:
            val = int(body[key])
        except (TypeError, ValueError):
            return jsonify(error=f"{key} 必须是数字"), 400
        if not (lo <= val <= hi):
            return jsonify(error=f"{key} 必须在 {lo}~{hi} 之间"), 400
        db.set_sec(key, val)
        changed.append(key)

    if not changed:
        return jsonify(error="没有要保存的项"), 400

    db.add_audit("sec_settings", client_ip(),
                 "修改安全设置:" + ",".join(changed),
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, changed=changed, settings=db.get_sec_all())


# ---------------- 前台特效控制(节日等) ----------------

@app.get("/api/fx")
def api_fx():
    """公开:前台读取当前特效配置(节日模式/指定节日/动效总开关)"""
    return jsonify(
        mode=db.get_fx("fx_holiday_mode"),
        key=db.get_fx("fx_holiday_key"),
        effects=db.get_fx("fx_effects"),
    )


@app.get("/api/security/fx")
@login_required
def get_fx_settings():
    out = dict(db.get_fx_all())
    out["keys"] = list(db.HOLIDAY_KEYS)
    return jsonify(out)


@app.post("/api/security/fx")
@login_required
def save_fx_settings():
    """保存前台特效设置。mode 三选一,key 必须是已知节日。"""
    body = request.get_json(force=True, silent=True) or {}
    changed = []

    mode = body.get("fx_holiday_mode")
    if mode is not None:
        if mode not in ("auto", "manual", "off"):
            return jsonify(error="节日模式只能是 auto / manual / off"), 400
        db.set_fx("fx_holiday_mode", mode)
        changed.append("fx_holiday_mode")

    if "fx_holiday_key" in body:
        key = str(body["fx_holiday_key"] or "")
        if key and key not in db.HOLIDAY_KEYS:
            return jsonify(error="未知的节日标识"), 400
        db.set_fx("fx_holiday_key", key)
        changed.append("fx_holiday_key")

    if "fx_effects" in body:
        eff = str(body["fx_effects"])
        if eff not in ("0", "1"):
            return jsonify(error="动效开关只能是 0 或 1"), 400
        db.set_fx("fx_effects", eff)
        changed.append("fx_effects")

    if not changed:
        return jsonify(error="没有要保存的项"), 400

    db.add_audit("fx_settings", client_ip(),
                 "修改前台特效设置:" + ",".join(changed),
                 request.headers.get("User-Agent", ""))
    out = {"ok": True, "changed": changed}
    out.update(db.get_fx_all())
    return jsonify(out)


# ---------------- 留言板(后台管理) ----------------

@app.get("/api/messages/admin")
@login_required
def api_messages_admin():
    """后台:全部留言 + 计数"""
    return jsonify(messages=db.list_messages_admin(), counts=db.message_counts())


@app.post("/api/messages/<int:mid>/mod")
@login_required
def api_message_mod(mid):
    """审核/回复/删除,action = show | hide | pending | reply | delete"""
    body = request.get_json(silent=True) or {}
    act = body.get("action")
    ok, detail = False, ""

    if act == "show":
        ok = db.set_message_shown(mid, 1)
        detail = "展示留言"
    elif act == "hide":
        ok = db.set_message_shown(mid, 2)
        detail = "隐藏留言"
    elif act == "pending":
        ok = db.set_message_shown(mid, 0)
        detail = "转待审核"
    elif act == "reply":
        ok = db.reply_message(mid, body.get("reply") or "")
        detail = f"回复留言({len((body.get('reply') or '').strip())}字)"
    elif act == "delete":
        ok = db.del_message(mid)
        detail = "删除留言"
    else:
        return jsonify(error="未知操作"), 400

    if not ok:
        return jsonify(error="留言不存在"), 404
    db.add_audit("message_mod", client_ip(), f"{detail} id={mid}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, counts=db.message_counts())


@app.get("/api/likes/admin")
@login_required
def api_likes_admin():
    """后台:各页点赞 + 总数"""
    return jsonify(likes=db.like_counts(), total=db.like_total())


# ---------------- 公告与倒计时(后台管理) ----------------

@app.get("/api/notices/admin")
@login_required
def api_notices_admin():
    """后台:公告列表"""
    return jsonify(notices=db.list_notices())


@app.post("/api/notices/admin")
@login_required
def api_notices_add():
    body = request.get_json(silent=True) or {}
    r = db.add_notice(body.get("body") or "")
    if not r.get("ok"):
        return jsonify(r), 400
    db.add_audit("notice_add", client_ip(), f"新增公告 id={r['id']}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, notices=db.list_notices())


@app.post("/api/notices/<int:nid>/mod")
@login_required
def api_notice_mod(nid):
    """action = on | off | delete"""
    body = request.get_json(silent=True) or {}
    act = body.get("action")
    if act in ("on", "off"):
        ok = db.set_notice_active(nid, 1 if act == "on" else 0)
    elif act == "delete":
        ok = db.del_notice(nid)
    else:
        return jsonify(error="未知操作"), 400
    if not ok:
        return jsonify(error="公告不存在"), 404
    db.add_audit("notice_mod", client_ip(), f"{act} 公告 id={nid}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, notices=db.list_notices())


@app.get("/api/countdowns/admin")
@login_required
def api_countdowns_admin():
    """后台:倒计时列表"""
    return jsonify(countdowns=db.list_countdowns())


@app.post("/api/countdowns/admin")
@login_required
def api_countdowns_save():
    body = request.get_json(silent=True) or {}
    r = db.upsert_countdown(
        cid=body.get("id"), title=body.get("title") or "",
        target=body.get("target") or "", emoji=body.get("emoji") or "⏳",
        active=1 if body.get("active", 1) else 0)
    if not r.get("ok"):
        return jsonify(r), 400
    db.add_audit("countdown_save", client_ip(),
                 f"保存倒计时 {body.get('title','')} @ {body.get('target','')}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, countdowns=db.list_countdowns())


@app.post("/api/countdowns/<int:cid>/delete")
@login_required
def api_countdown_delete(cid):
    if not db.del_countdown(cid):
        return jsonify(error="倒计时不存在"), 404
    db.add_audit("countdown_del", client_ip(), f"删除倒计时 id={cid}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, countdowns=db.list_countdowns())


# ---------------- 访客深度统计 ----------------

@app.get("/api/stats/visitors")
@login_required
def api_visitors_breakdown():
    """看板卡片:新老访客 + 平均停留时长"""
    days = request.args.get("days", 30, type=int)
    days = max(1, min(days, 365))
    return jsonify(db.visitor_breakdown(days))


@app.get("/api/stats/visits/csv")
@login_required
def api_visits_csv():
    """访问明细导出 CSV(近 N 天,不含 IP)"""
    import csv as _csv
    import io as _io
    days = request.args.get("days", 7, type=int)
    days = max(1, min(days, 30))
    since = int(time.time()) - days * 86400
    with db.get_db() as c:
        rows = c.execute(
            "SELECT day,ts,path,referer,ua,city,is_new,dur_s FROM visits "
            "WHERE ts>=? AND is_bot=0 ORDER BY ts DESC", (since,)).fetchall()
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["日期", "时间(北京)", "页面", "来源", "设备", "城市", "新访客", "停留秒"])
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    _BJ = _tz(_td(hours=8))
    for r in rows:
        t = _dt.fromtimestamp(r["ts"], _BJ).strftime("%Y-%m-%d %H:%M:%S")
        w.writerow([r["day"], t, r["path"], r["referer"], r["ua"], r["city"],
                    "是" if r["is_new"] else "否", r["dur_s"]])
    resp = make_response(buf.getvalue())
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=visits.csv"
    db.add_audit("csv_export", client_ip(), f"导出近{days}天访问明细",
                 request.headers.get("User-Agent", ""))
    return resp


@app.get("/api/security/overview")
@login_required
def sec_overview():
    """安全面板一屏所需的数据"""
    s = db.get_sec_all()
    now = int(time.time())
    blocked = db.list_blocked()
    sessions = db.list_sessions()
    cur_sid = session.get("sid")
    for x in sessions:
        x["current"] = (x["sid"] == cur_sid)

    # 最近 24 小时的登录失败次数
    fails_24h = 0
    for a in db.list_audit(500):
        if a["action"] in ("login_fail", "captcha_fail", "login_block"):
            if now - a["ts"] <= 86400:
                fails_24h += 1

    return jsonify(
        settings=s,
        blocked=blocked,
        sessions=sessions,
        current_sid=cur_sid,
        fails_24h=fails_24h,
        must_change=db.must_change_password(),
        server_time=now,
    )


@app.get("/api/security/audit")
@login_required
def get_audit():
    try:
        limit = int(request.args.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100
    limit = max(10, min(limit, 500))
    return jsonify(rows=db.list_audit(limit))


@app.delete("/api/security/audit")
@login_required
def delete_audit():
    n = db.clear_audit()
    db.add_audit("audit_clear", client_ip(), f"清空审计日志 {n} 条",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, deleted=n)


@app.post("/api/security/unblock")
@login_required
def unblock_ip():
    body = request.get_json(force=True, silent=True) or {}
    ip = (body.get("ip") or "").strip()
    if not ip:
        return jsonify(error="缺少 IP"), 400
    ok = db.unblock(ip)
    db.add_audit("unblock", client_ip(), f"解除封锁 {ip}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=ok)


@app.post("/api/security/revoke")
@login_required
def revoke_session_api():
    body = request.get_json(force=True, silent=True) or {}
    sid = (body.get("sid") or "").strip()
    if not sid:
        return jsonify(error="缺少会话 id"), 400
    if sid == session.get("sid"):
        return jsonify(error="不能踢掉当前这个会话"), 400
    db.revoke_session(sid)
    db.add_audit("revoke_session", client_ip(), "踢下线一个会话",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True)


@app.post("/api/security/revoke-all")
@login_required
def revoke_all_api():
    """踢掉除自己以外的所有会话"""
    n = db.revoke_all_sessions(keep_sid=session.get("sid"))
    db.add_audit("revoke_all", client_ip(), f"踢下线其他所有会话({n} 个)",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, revoked=n)


# ---------------- 后台 CRUD API(需登录) ----------------

@app.post("/api/skills")
@login_required
def add_skill():
    item = request.get_json(force=True, silent=True) or {}
    row = db.insert_skill(item)
    return jsonify(row), 201


@app.put("/api/skills/<int:sid>")
@login_required
def update_skill(sid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_skill(sid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/skills/<int:sid>")
@login_required
def delete_skill(sid):
    ok = db.delete_skill(sid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


@app.post("/api/timeline")
@login_required
def add_event():
    item = request.get_json(force=True, silent=True) or {}
    row = db.insert_timeline(item)
    return jsonify(row), 201


@app.put("/api/timeline/<int:eid>")
@login_required
def update_event(eid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_timeline(eid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/timeline/<int:eid>")
@login_required
def delete_event(eid):
    ok = db.delete_timeline(eid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


@app.post("/api/stats")
@login_required
def add_stat():
    item = request.get_json(force=True, silent=True) or {}
    row = db.insert_stat(item)
    return jsonify(row), 201


@app.put("/api/stats/<int:sid>")
@login_required
def update_stat(sid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_stat(sid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/stats/<int:sid>")
@login_required
def delete_stat(sid):
    ok = db.delete_stat(sid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


# ---------------- works(项目墙) ----------------

@app.post("/api/works")
@login_required
def add_work():
    item = request.get_json(force=True, silent=True) or {}
    return jsonify(db.insert_work(item)), 201


@app.put("/api/works/<int:wid>")
@login_required
def update_work(wid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_work(wid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/works/<int:wid>")
@login_required
def delete_work(wid):
    ok = db.delete_work(wid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


# ---------------- profile(关于我 / 信息卡片) ----------------

@app.post("/api/profile")
@login_required
def add_profile():
    item = request.get_json(force=True, silent=True) or {}
    return jsonify(db.insert_profile(item)), 201


@app.put("/api/profile/<int:pid>")
@login_required
def update_profile(pid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_profile(pid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/profile/<int:pid>")
@login_required
def delete_profile(pid):
    ok = db.delete_profile(pid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


# ---------------- v2.2 荣誉墙 CRUD ----------------

@app.post("/api/honors")
@login_required
def add_honor():
    item = request.get_json(force=True, silent=True) or {}
    return jsonify(db.insert_honor(item)), 201


@app.put("/api/honors/<int:hid>")
@login_required
def update_honor(hid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_honor(hid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/honors/<int:hid>")
@login_required
def delete_honor(hid):
    ok = db.delete_honor(hid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


# ---------------- v2.2 随手记 CRUD ----------------

@app.post("/api/notes")
@login_required
def add_note():
    item = request.get_json(force=True, silent=True) or {}
    return jsonify(db.insert_note(item)), 201


@app.put("/api/notes/<int:nid>")
@login_required
def update_note(nid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_note(nid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/notes/<int:nid>")
@login_required
def delete_note(nid):
    ok = db.delete_note(nid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


# ---------------- v2.2 友情链接 CRUD ----------------

@app.post("/api/friendlinks")
@login_required
def add_friendlink():
    item = request.get_json(force=True, silent=True) or {}
    if not item.get("name") or not item.get("url"):
        return jsonify(error="名称和链接都要填"), 400
    return jsonify(db.insert_friendlink(item)), 201


@app.put("/api/friendlinks/<int:fid>")
@login_required
def update_friendlink(fid):
    item = request.get_json(force=True, silent=True) or {}
    row = db.update_friendlink(fid, item)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/friendlinks/<int:fid>")
@login_required
def delete_friendlink(fid):
    ok = db.delete_friendlink(fid)
    return ("", 204) if ok else (jsonify(error="not found"), 404)


# ---------------- 图片上传 ----------------

def sniff_image(head: bytes) -> str | None:
    """根据文件头判断真实类型,认不出就返回 None"""
    for magic, kind in MAGIC.items():
        if head.startswith(magic):
            return kind
    # WEBP: RIFF....WEBP
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


@app.post("/api/upload")
@login_required
def upload_image():
    """后台传图,返回可直接引用的 URL"""
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="没有选文件"), 400

    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify(error="只支持 png / jpg / gif / webp"), 400

    raw = f.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify(error="图片太大了,请压缩到 5MB 以内"), 400

    real = sniff_image(raw[:16])
    if real is None:
        return jsonify(error="这个文件不是真正的图片"), 400
    # 扩展名和真实类型对不上 → 以真实类型为准
    if ALLOWED_EXT[ext] != real and not (ext == "jpg" and real == "jpeg"):
        ext = "jpg" if real == "jpeg" else real

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = f"{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:12]}.{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as out:
        out.write(raw)
    os.chmod(path, 0o644)   # nginx 要能读

    db.add_audit("upload", client_ip(), f"上传图片 {name}({len(raw)} 字节)",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, url=f"{UPLOAD_URL}/{name}",
                   size=len(raw), name=name)


@app.get("/api/uploads")
@login_required
def list_uploads():
    """列出已上传的图片,方便后台挑图/删图"""
    if not os.path.isdir(UPLOAD_DIR):
        return jsonify(items=[])
    items = []
    for fn in sorted(os.listdir(UPLOAD_DIR), reverse=True):
        if fn.rsplit(".", 1)[-1].lower() not in ALLOWED_EXT:
            continue
        p = os.path.join(UPLOAD_DIR, fn)
        if not os.path.isfile(p):
            continue
        items.append({
            "name": fn,
            "url": f"{UPLOAD_URL}/{fn}",
            "size": os.path.getsize(p),
            "mtime": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"),
        })
    return jsonify(items=items)


@app.delete("/api/uploads/<name>")
@login_required
def delete_upload(name):
    # 防路径穿越:只允许纯文件名
    if "/" in name or "\\" in name or name.startswith("."):
        return jsonify(error="非法文件名"), 400
    p = os.path.join(UPLOAD_DIR, name)
    if not os.path.isfile(p):
        return jsonify(error="not found"), 404
    os.remove(p)
    db.add_audit("upload_del", client_ip(), f"删除图片 {name}",
                 request.headers.get("User-Agent", ""))
    return "", 204


# ---------------- 数据导出 / 导入(备份) ----------------

@app.get("/api/export")
@login_required
def export_data():
    """导出全部内容为 JSON(不含密码哈希)"""
    payload = {
        "version": 2,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "skills": db.get_skills(),
        "timeline": db.get_timeline(),
        "stats": db.get_stats(),
        "works": db.get_works(),
        "profile": db.get_profile(),
        "honors": db.get_honors(),
        "notes": db.get_notes(),
        "friendlinks": db.get_friendlinks(),
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    db.add_audit("export", client_ip(), "导出数据备份",
                 request.headers.get("User-Agent", ""))
    resp = app.response_class(body, mimetype="application/json")
    resp.headers["Content-Disposition"] = f'attachment; filename="mysite-backup-{stamp}.json"'
    return resp


@app.post("/api/import")
@login_required
def import_data():
    """从 JSON 恢复内容。默认合并(按 id 覆盖),replace=true 则先清空"""
    payload = request.get_json(force=True, silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="文件格式不对,需要导出的 JSON"), 400

    kinds = ("skills", "timeline", "stats", "works", "profile")
    if not any(isinstance(payload.get(k), list) for k in kinds):
        return jsonify(error="里面没有可恢复的数据"), 400

    replace = bool(payload.get("replace"))
    counts = db.import_payload(payload, replace=replace)
    db.add_audit("import", client_ip(),
                 f"导入数据 replace={replace} {counts}",
                 request.headers.get("User-Agent", ""))
    return jsonify(ok=True, replace=replace, counts=counts)


# ---------------- 模板过滤器 ----------------

# (备用)


# ---------------- 启动 ----------------
# gunicorn 导入本模块时不走 __main__,所以建库必须放模块级
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db.init_db(DB_PATH)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100, debug=False)
