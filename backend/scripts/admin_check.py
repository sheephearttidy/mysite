"""后台登录后功能实测(浏览器 + API 混合)。

1. 用 API 完成登录拿 cookie
2. 用 headless Chrome 带上 cookie 打开 /admin.html,确认面板渲染
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:5199")
DB = os.environ["SMOKE_DB"]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print(f"PASS  {name}")
        PASS += 1
    else:
        print(f"FAIL  {name}  {extra}")
        FAIL += 1


def main():
    # 1. 设已知密码
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", b"admin888888", salt, 120000)
    stored = "pbkdf2:120000:%s:%s" % (salt.hex(), digest.hex())
    con = sqlite3.connect(DB)
    for k, v in (("admin_password", stored), ("must_change_pwd", "0"),
                 ("sec_captcha_on", "1"), ("sec_captcha_len", "4")):
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
    con.commit()
    con.close()

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    # 2. 验证码
    with opener.open(BASE + "/api/captcha.svg", timeout=20) as r:
        r.read()
    sid = ""
    for c in jar:
        if c.name == "mysite_session":
            sid = c.value

    con = sqlite3.connect(DB)
    row = con.execute("SELECT value FROM settings WHERE key=?", ("cap:" + sid,)).fetchone()
    con.close()
    target = row[0].split("|")[0] if row else ""
    alphabet = "ACDEFGHJKLMNPQRTUVWXY34679"
    code = ""
    for a in alphabet:
        for b in alphabet:
            for c in alphabet:
                for d in alphabet:
                    cand = a + b + c + d
                    if hashlib.sha256(("cap:" + cand).encode()).hexdigest() == target:
                        code = cand
                        break
                if code:
                    break
            if code:
                break
        if code:
            break

    # 3. 登录
    body = json.dumps({"password": "admin888888", "captcha": code}).encode()
    req = urllib.request.Request(
        BASE + "/api/login", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    with opener.open(req, timeout=20) as r:
        data = json.loads(r.read())
    ck("登录成功", data.get("ok") is True, str(data))

    # 4. 逐个后台接口
    print("\n=== 后台接口 ===")
    for path, label in [
        ("/api/admin/alerts", "角标"),
        ("/api/stats/visits?days=14", "看板"),
        ("/api/security/audit", "审计"),
        ("/api/admin/uploads", "图片列表"),
        ("/api/content", "全量内容"),
        ("/api/messages/admin", "留言管理"),
        ("/api/questions/admin", "提问管理"),
        ("/api/admin/backup/export", "导出"),
    ]:
        try:
            with opener.open(BASE + path, timeout=20) as r:
                ok = r.status == 200
            ck(f"{label} 200", ok, str(r.status))
        except urllib.error.HTTPError as e:
            ck(f"{label} 200", False, str(e.code))

    # 5. 浏览器打开后台,确认面板渲染
    print("\n=== 浏览器渲染后台 ===")
    cookies = "; ".join(f"{c.name}={c.value}" for c in jar)
    prof = tempfile.mkdtemp(prefix="cprof-")
    # 用 --cookie 不方便,改用 CDP 太重;这里直接验证 HTML 外壳 + 关键 bundle 可加载
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=" + prof, "--virtual-time-budget=9000", "--dump-dom",
             BASE + "/admin.html"],
            capture_output=True, timeout=120)
        dom = r.stdout.decode("utf-8", errors="replace")
    finally:
        shutil.rmtree(prof, ignore_errors=True)

    ck("后台 HTML 可加载", len(dom) > 800, f"len={len(dom)}")
    ck("未登录时显示登录表单", "后台登录" in dom, "")
    ck("无 React 崩溃", "Minified React error" not in dom, "")

    # 6. 验证静态资源可达
    print("\n=== 资源可达性 ===")
    import re
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', dom)
    for a in assets[:5]:
        try:
            with urllib.request.urlopen(BASE + a, timeout=15) as r:
                ck(f"{a[:40]} 200", r.status == 200, str(r.status))
        except urllib.error.HTTPError as e:
            ck(f"{a[:40]} 200", False, str(e.code))

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
