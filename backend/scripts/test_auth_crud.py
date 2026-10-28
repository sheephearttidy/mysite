"""登录后 CRUD 全流程测试(用临时库,不污染线上数据)。

流程:设密码 -> 登录 -> 增删改查 -> 导入导出 -> 退出。
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:5100")
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print(f"PASS  {name}")
        PASS += 1
    else:
        print(f"FAIL  {name}  {extra}")
        FAIL += 1


def req(path, method="GET", body=None, cookie=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"} if data else {}
    if cookie:
        h["Cookie"] = cookie
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


def jget(path, **kw):
    st, raw, hdr = req(path, **kw)
    try:
        return st, json.loads(raw), hdr
    except Exception:
        return st, None, hdr


def pick_cookie(set_cookie):
    for part in (set_cookie or "").split(";"):
        part = part.strip()
        if part.startswith("mysite_session="):
            return part
    return ""


def solve_captcha(svg, cookie, db_path):
    """测试专用:从 settings 表读出验证码答案哈希,再枚举比对。"""
    sid = cookie.split("=", 1)[1] if "=" in cookie else ""
    con = sqlite3.connect(db_path)
    row = con.execute("SELECT value FROM settings WHERE key=?", ("cap:" + sid,)).fetchone()
    con.close()
    if not row:
        return ""
    target = row[0].split("|")[0]
    alphabet = "ACDEFGHJKLMNPQRTUVWXY34679"
    for a in alphabet:
        for b in alphabet:
            for c in alphabet:
                for d in alphabet:
                    code = a + b + c + d
                    if hashlib.sha256(("cap:" + code).encode()).hexdigest() == target:
                        return code
    return ""


def main():
    db_path = os.environ["SMOKE_DB"]

    # 1. 直接写库,设一个已知密码
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", b"testpass123", salt, 120000)
    stored = "pbkdf2:120000:%s:%s" % (salt.hex(), digest.hex())
    con = sqlite3.connect(db_path)
    for k, v in (
        ("admin_password", stored),
        ("must_change_pwd", "0"),
        ("sec_captcha_on", "1"),
        ("sec_captcha_len", "4"),
    ):
        con.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, v),
        )
    con.commit()
    con.close()

    # 2. 登录
    print("\n=== 登录 ===")
    st, raw, hdr = req("/api/captcha.svg")
    ck("captcha 200", st == 200, str(st))
    cookie = pick_cookie(hdr.get("Set-Cookie") or "")
    ck("拿到会话 cookie", bool(cookie), "")

    code = solve_captcha(raw, cookie, db_path)
    ck("解出验证码", bool(code), "无法从库中匹配")

    st, d, hdr = jget(
        "/api/login", method="POST",
        body={"password": "testpass123", "captcha": code}, cookie=cookie,
    )
    ck("登录成功 200", st == 200 and bool(d and d.get("ok")), "%s %s" % (st, d))

    login_cookie = pick_cookie(hdr.get("Set-Cookie") or "")
    ck("登录下发新 cookie", bool(login_cookie), "")

    st, d, _ = jget("/api/me", cookie=login_cookie)
    ck("/api/me 200", st == 200 and bool(d and d.get("ok")), str(st))

    # 3. CRUD
    print("\n=== CRUD ===")
    st, d, _ = jget(
        "/api/content/skills", method="POST",
        body={"name": "测试技能", "percent": 42, "note": "自动化测试",
              "category": "serious", "color": "teal", "sort": 99},
        cookie=login_cookie,
    )
    ck("创建技能 201", st == 201 and bool(d and d.get("id")), "%s %s" % (st, d))
    new_id = d.get("id") if d else None

    st, d, _ = jget(
        "/api/content/skills/" + str(new_id), method="PUT",
        body={"percent": 88}, cookie=login_cookie,
    )
    ck("部分更新技能 200", st == 200 and bool(d and d.get("percent") == 88), "%s %s" % (st, d))
    ck("更新保留未提交字段", bool(d and d.get("name") == "测试技能"), str(d))

    st, d, _ = jget(
        "/api/content/skills/" + str(new_id), method="PUT",
        body={"percent": 999}, cookie=login_cookie,
    )
    ck("percent 越界 -> 4xx", 400 <= st < 500, str(st))

    st, d, _ = jget("/api/content/skills/" + str(new_id), method="DELETE", cookie=login_cookie)
    ck("删除技能 204", st == 204, str(st))

    st, d, _ = jget("/api/content/skills/" + str(new_id), method="DELETE", cookie=login_cookie)
    ck("重复删除 404", st == 404, str(st))

    # 4. 后台面板
    print("\n=== 后台面板 ===")
    st, d, _ = jget("/api/admin/alerts", cookie=login_cookie)
    ck("alerts 200", st == 200 and isinstance(d, dict), str(st))

    st, d, _ = jget("/api/stats/visits", cookie=login_cookie)
    ck("看板 200", st == 200 and isinstance(d, dict), str(st))
    ck("看板 daily 补零", bool(d and isinstance(d.get("daily"), list) and d["daily"]), "")

    st, d, _ = jget("/api/security/audit", cookie=login_cookie)
    ck("审计日志 200", st == 200 and isinstance(d, list), str(st))

    st, d, _ = jget("/api/admin/uploads", cookie=login_cookie)
    ck("上传列表 200", st == 200 and isinstance(d, list), str(st))

    st, d, _ = jget("/api/admin/backup/export", cookie=login_cookie)
    ck("导出 200", st == 200 and isinstance(d, dict), str(st))
    ck("导出含 skills", bool(d and "skills" in d), "")
    ck("导出不含密码", bool(d and "admin_password" not in json.dumps(d)), "")

    # 5. 退出
    print("\n=== 退出 ===")
    st, d, _ = jget("/api/logout", method="POST", cookie=login_cookie)
    ck("登出 200", st == 200, str(st))
    st, d, _ = jget("/api/me", cookie=login_cookie)
    ck("登出后 /api/me 401", st == 401, str(st))

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
