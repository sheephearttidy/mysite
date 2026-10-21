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
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, flash, send_from_directory)

import db

app = Flask(__name__)
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "mysite.db")

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

# 简单防爆破:同 IP 连续失败 8 次,封 10 分钟
_failed = {}  # ip -> [count, blocked_until]


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
        return f(*args, **kwargs)
    return wrapper


def check_admin_password(pwd: str) -> bool:
    """密码哈希存在数据库 settings 表里"""
    return db.verify_password(pwd, db.get_pass_hash() or "")


def rate_limit_ok(ip: str) -> bool:
    rec = _failed.get(ip)
    if rec and rec[1] > time.time():
        return False  # 封禁中
    return True


def record_fail(ip: str):
    rec = _failed.get(ip) or [0, 0]
    rec[0] += 1
    if rec[0] >= 8:
        rec[1] = time.time() + 600  # 封 10 分钟
        rec[0] = 0
    _failed[ip] = rec


def clear_fail(ip: str):
    _failed.pop(ip, None)


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


@app.get("/api/health")
def api_health():
    return jsonify(ok=True, time=datetime.now(timezone.utc).isoformat())


# ---------------- 访问统计 ----------------

# 只记这些路径,避免被扫描器刷爆数据库
TRACK_PATHS = {"/", "/index.html"}
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
    """前台每次打开首页调一次。公开接口,只记首页,防扫描器刷库。"""
    body = request.get_json(silent=True) or {}
    path = (body.get("path") or "/")[:100]
    if path not in TRACK_PATHS:
        return jsonify(ok=False, error="只统计首页"), 400

    ua = request.headers.get("User-Agent", "")[:300]
    ref = _clean_referer(request.headers.get("Referer", ""))

    now = datetime.now(_BEIJING)
    try:
        db.record_visit(path=path, referer=ref, ua=ua,
                        day=now.strftime("%Y-%m-%d"), ts=int(time.time()))
    except Exception:
        return jsonify(ok=False), 200   # 统计失败不影响用户
    return jsonify(ok=True)


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
    return render_template("login.html", initial=db.must_change_password())


@app.post("/admin/login")
def login_post():
    ip = client_ip()
    pwd = request.form.get("password", "")
    if rate_limit_ok(ip) and check_admin_password(pwd):
        clear_fail(ip)
        session["user"] = ADMIN_USER
        session.permanent = True
        return redirect(url_for("admin"))
    record_fail(ip)
    flash("密码不对哦,再想想?🤔", "error")
    return redirect(url_for("login"))


@app.get("/admin/logout")
def logout():
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
    session.clear()  # 改完强制重新登录,用新密码
    return jsonify(ok=True)


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
    return jsonify(ok=True, replace=replace, counts=counts)


# ---------------- 模板过滤器 ----------------

# (备用)


# ---------------- 启动 ----------------
# gunicorn 导入本模块时不走 __main__,所以建库必须放模块级
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db.init_db(DB_PATH)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100, debug=False)
