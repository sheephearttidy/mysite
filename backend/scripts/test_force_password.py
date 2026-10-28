"""强制改密流程测试。

验证要点:
1. 初始密码 admin 能登录,但 must_change=True
2. 未改密时,访问任何后台接口都返回 403 MUST_CHANGE_PASSWORD
3. /api/me 和 /api/password 不被拦(否则用户出不来)
4. 改密后立即恢复访问
5. 弱密码被拒
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:5211")
DB = os.environ["TEST_DB"]
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def solve_captcha(cookie_value, db_path):
    """从 settings 读出答案哈希后暴力枚举。

    长度从 sec_captcha_len 读取 —— 别硬编码 4,否则后台把位数调成 5 就解不出来。
    """
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT value FROM settings WHERE key=?", ("cap:" + cookie_value,)
    ).fetchone()
    length_row = con.execute(
        "SELECT value FROM settings WHERE key='sec_captcha_len'"
    ).fetchone()
    con.close()
    if not row:
        return ""
    target = row[0].split("|")[0]
    length = int(length_row[0]) if length_row else 4
    length = max(3, min(length, 6))
    alphabet = "ACDEFGHJKLMNPQRTUVWXY34679"

    import hashlib
    import itertools

    for combo in itertools.product(alphabet, repeat=length):
        code = "".join(combo)
        if hashlib.sha256(("cap:" + code).encode()).hexdigest() == target:
            return code
    return ""


def main():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(path, method="GET", body=None):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
        try:
            with opener.open(req, timeout=20) as r:
                raw = r.read()
                try:
                    return r.status, json.loads(raw)
                except Exception:
                    return r.status, raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, raw.decode("utf-8", "replace")

    # 1. 取验证码并登录
    print("\n=== 1. 初始密码登录 ===")
    with opener.open(BASE + "/api/captcha.svg", timeout=20) as r:
        r.read()
    sid = ""
    for c in jar:
        if c.name == "mysite_session":
            sid = c.value
    code = solve_captcha(sid, DB)
    ck("解出验证码", bool(code), "库中无匹配")

    st, d = call("/api/login", "POST", {"password": "admin", "captcha": code})
    ck("admin 能登录", st == 200 and isinstance(d, dict) and d.get("ok"), str(st) + " " + str(d))
    ck("返回 must_change=True", isinstance(d, dict) and d.get("must_change") is True, str(d))

    # 2. 未改密时后台接口应全部 403
    print("\n=== 2. 未改密时拦截 ===")
    blocked = [
        ("/api/admin/alerts", "GET"),
        ("/api/stats/visits", "GET"),
        ("/api/security/audit", "GET"),
        ("/api/admin/uploads", "GET"),
        ("/api/admin/backup/export", "GET"),
        ("/api/security/settings", "GET"),
    ]
    for path, method in blocked:
        st, d = call(path, method)
        code_ok = isinstance(d, dict) and d.get("code") == "MUST_CHANGE_PASSWORD"
        ck(f"{path} -> 403 MUST_CHANGE", st == 403 and code_ok, f"{st} {d}")

    # /api/content 是前台公开接口,不受改密状态影响(前台要能正常读)
    st, d = call("/api/content")
    ck("/api/content 公开可读(不拦)", st == 200, str(st))

    # 写接口也要拦
    st, d = call("/api/content/skills", "POST", {"name": "x", "percent": 10})
    ck("POST 内容被拦", st == 403, str(st))

    # 3. /api/me 与 /api/password 不能被拦
    print("\n=== 3. 改密通道保持可用 ===")
    st, d = call("/api/me")
    ck("/api/me 可访问(200)", st == 200, str(st))
    ck("/api/me 报告 must_change", isinstance(d, dict) and d.get("must_change") is True, str(d))

    # 4. 弱密码被拒
    print("\n=== 4. 密码强度校验 ===")
    st, d = call("/api/password", "POST", {"old": "admin", "new": "123456"})
    ck("纯数字被拒", st == 400, str(st) + " " + str(d))
    st, d = call("/api/password", "POST", {"old": "admin", "new": "short1"})
    ck("太短被拒", st == 400, str(st) + " " + str(d))
    st, d = call("/api/password", "POST", {"old": "wrong", "new": "GoodPass123"})
    ck("原密码错误被拒", st == 401, str(st) + " " + str(d))

    # 5. 改密成功
    print("\n=== 5. 改密后恢复 ===")
    st, d = call("/api/password", "POST", {"old": "admin", "new": "MyNewPass123"})
    ck("改密成功", st == 200, str(st) + " " + str(d))

    st, d = call("/api/me")
    ck("must_change 变 False", isinstance(d, dict) and d.get("must_change") is False, str(d))

    for path, method in blocked:
        st, d = call(path, method)
        ck(f"{path} 恢复 200", st == 200, f"{st} {str(d)[:80]}")

    # 6. 旧密码失效
    print("\n=== 6. 旧密码失效 ===")
    jar2 = http.cookiejar.CookieJar()
    op2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar2))
    with op2.open(BASE + "/api/captcha.svg", timeout=20) as r:
        r.read()
    sid2 = ""
    for c in jar2:
        if c.name == "mysite_session":
            sid2 = c.value
    code2 = solve_captcha(sid2, DB)
    req = urllib.request.Request(
        BASE + "/api/login",
        data=json.dumps({"password": "admin", "captcha": code2}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with op2.open(req, timeout=20) as r:
            st = r.status
    except urllib.error.HTTPError as e:
        st = e.code
    ck("旧密码 admin 登录失败", st == 401, str(st))

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
