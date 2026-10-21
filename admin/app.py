# ============================================================
# 我的小窝 · 后台管理系统
# Flask + SQLite,轻量零依赖数据库
# ============================================================

import os
import time
import hashlib
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, flash)

import db

app = Flask(__name__)
app.secret_key = os.environ.get("MYSITE_SECRET_KEY", os.urandom(24))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

ADMIN_USER = os.environ.get("MYSITE_ADMIN_USER", "admin")
ADMIN_PASS_HASH = os.environ.get("MYSITE_ADMIN_PASS_HASH")  # pbkdf2:iters:salt:hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mysite.db")

# 简单防爆破:同 IP 连续失败 8 次,封 10 分钟
_failed = {}  # ip -> [count, blocked_until]


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
    """格式 pbkdf2:迭代次数:salt_hex:hash_hex"""
    if not ADMIN_PASS_HASH:
        return False
    parts = ADMIN_PASS_HASH.split(":")
    if len(parts) != 4 or parts[0] != "pbkdf2":
        return False
    _, iters, salt_hex, hash_hex = parts
    try:
        calc = hashlib.pbkdf2_hmac("sha256", pwd.encode(), bytes.fromhex(salt_hex), int(iters))
        return calc.hex() == hash_hex
    except ValueError:
        return False


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
    )


@app.get("/api/health")
def api_health():
    return jsonify(ok=True, time=datetime.now(timezone.utc).isoformat())


# ---------------- 后台页面 ----------------

@app.get("/admin/login")
def login():
    if session.get("user"):
        return redirect(url_for("admin"))
    return render_template("login.html")


@app.post("/admin/login")
def login_post():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "x").split(",")[0].strip()
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
@login_required
def admin():
    data = {
        "skills": db.get_skills(),
        "timeline": db.get_timeline(),
        "stats": db.get_stats(),
    }
    return render_template("admin.html", data=data)  # data 会被 tojson 过滤器安全转义


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


# ---------------- 模板过滤器 ----------------

# (ts 过滤器暂时用不上,保留备用)


# ---------------- 启动 ----------------

# gunicorn 导入本模块时不走 __main__,所以建库必须放模块级
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db.init_db(DB_PATH)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100, debug=False)
