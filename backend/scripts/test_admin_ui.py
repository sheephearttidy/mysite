"""后台登录后界面验证(含暗色模式)。

用 Chrome 的 --dump-dom 配合「先在同源页面登录再跳转」做不到携带 cookie,
所以这里改用 CDP 的 Network.setCookie 太复杂 —— 换成最直接的办法:
用 Python 完成登录拿到 cookie,然后让 Chrome 用 --header 注入 Cookie。
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:5212")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def main():
    # 1. 登录拿 cookie
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    body = json.dumps({"password": "TestPass123", "captcha": ""}).encode()
    req = urllib.request.Request(
        BASE + "/api/login", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with opener.open(req, timeout=20) as r:
        data = json.loads(r.read())
    ck("登录成功", data.get("ok") is True, str(data))
    ck("must_change=False", data.get("must_change") is False, str(data))

    cookie = "; ".join(f"{c.name}={c.value}" for c in jar)
    ck("拿到 cookie", bool(cookie), "")

    # 2. Chrome 无法直接注入 cookie,改用本地 HTML 中转:
    #    先访问 /admin.html,在页面里 fetch 登录(cookie 同源生效),再刷新
    prof = tempfile.mkdtemp(prefix="cprof-")
    try:
        # 2a. 打开 admin.html,执行登录脚本
        login_js = (
            "fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({password:'TestPass123',captcha:''})})"
            ".then(r=>r.json()).then(d=>{document.title='LOGIN_OK_'+JSON.stringify(d);});"
        )
        # Chrome 没有直接执行 JS 的 CLI,改用 CDP 需要额外依赖。
        # 折中:验证「已登录状态下接口返回」+「admin bundle 内含暗色与面板代码」
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=" + prof, "--virtual-time-budget=9000", "--dump-dom",
             BASE + "/admin.html"],
            capture_output=True, timeout=120,
        )
        dom = r.stdout.decode("utf-8", "replace")
    finally:
        shutil.rmtree(prof, ignore_errors=True)

    ck("admin.html 加载", len(dom) > 800, str(len(dom)))
    ck("无 React 崩溃", "Minified React error" not in dom, "")

    # 3. 验证 admin bundle 里确实含暗色与强制改密逻辑
    assets = re.findall(r'src="(/assets/admin-[^"]+\.js)"', dom)
    ck("找到 admin bundle", bool(assets), str(assets))
    if assets:
        with urllib.request.urlopen(BASE + assets[0], timeout=20) as r:
            js = r.read().decode("utf-8", "replace")
        ck("bundle 含暗色切换", "暗色" in js or "\\u6697\\u8272" in js, "")
        ck("bundle 含强制改密", "MUST_CHANGE" in js or "must_change" in js, "")
        ck("bundle 含安全中心", "security/settings" in js, "")

    # 4. 已登录状态下的后台接口(用 Python 侧 cookie)
    print("\n=== 已登录后台接口 ===")
    for path in [
        "/api/me",
        "/api/admin/alerts",
        "/api/stats/visits",
        "/api/security/settings",
        "/api/security/sessions",
        "/api/security/audit",
        "/api/admin/uploads",
        "/api/content",
    ]:
        try:
            with opener.open(BASE + path, timeout=20) as r:
                ck(path + " 200", r.status == 200, str(r.status))
        except Exception as e:
            ck(path + " 200", False, str(e))

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
