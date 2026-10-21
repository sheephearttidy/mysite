# ============================================================
# 我的小窝 · 后台管理系统
# Flask + SQLite,轻量零依赖数据库
# ============================================================

import os
import io
import json
import time
import uuid
import shutil
import base64
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, flash, send_from_directory)

import db
import captcha
import geo

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


@app.before_request
def limit_json_body():
    """除图片上传外,请求体一律不得超过 64KB(防内存放大)"""
    if request.path == "/api/upload":
        return None
    if request.content_length and request.content_length > JSON_MAX_BYTES:
        return jsonify(error="请求体太大了"), 413
    return None

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
    )


# 每个页面需要的数据:拆分多页后,各页只拉自己那部分
PAGE_FIELDS = {
    "index": ("stats",),
    "about": ("profile",),
    "skills": ("skills",),
    "works": ("works",),
    "campus": ("timeline",),
    "contact": (),
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
    """前台每次打开页面调一次。公开接口,只记已知页面,防扫描器刷库。"""
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
        db.record_visit(path=path, referer=ref, ua=ua,
                        day=now.strftime("%Y-%m-%d"), ts=int(time.time()),
                        city=city)
    except Exception:
        return jsonify(ok=False), 200   # 统计失败不影响用户
    return jsonify(ok=True)


@app.get("/api/map")
def api_map():
    """访客城市分布(公开):返回 [{city, count}],不暴露 IP"""
    return jsonify(cities=db.get_visit_cities())


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
        flash("密码不对哦,再想想?🤔", "error")
        return redirect(url_for("login"))

    # 4. 成功
    clear_fail(ip)
    sid = base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip("=")
    session.clear()                     # 防会话固定攻击
    session["user"] = ADMIN_USER
    session["sid"] = sid
    session["last_seen"] = int(time.time())
    session.permanent = True
    # 会话有效期按后台设置走(默认 168 小时 = 7 天)
    try:
        hours = max(1, int(db.get_sec("sec_session_hours")))
    except (TypeError, ValueError):
        hours = 168
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=hours)
    db.add_session(sid, ip, ua)
    db.add_audit("login_ok", ip, "登录成功", ua)
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
    }
    # 初始密码还没改过 → 前端弹窗提示修改
    return render_template("admin.html", data=data,
                           must_change=db.must_change_password())


# ---------------- 改密码 ----------------

@app.post("/api/password")
@login_required
def change_password():
    """已登录状态下修改自己的密码"""
    body = request.get_json(force=True, silent=True) or {}
    old_pwd = body.get("old", "")
    new_pwd = body.get("new", "")

    if not db.verify_password(old_pwd, db.get_pass_hash() or ""):
        return jsonify(error="旧密码不对哦"), 400
    if len(new_pwd) < 6:
        return jsonify(error="新密码至少 6 位啦"), 400
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
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "skills": db.get_skills(),
        "timeline": db.get_timeline(),
        "stats": db.get_stats(),
        "works": db.get_works(),
        "profile": db.get_profile(),
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
