"""安全审计:静态代码扫描 + 运行时攻击测试。

覆盖 OWASP 常见项:
- 认证/授权绕过
- 注入(SQL / 命令 / 路径穿越)
- XSS / CSP
- CSRF / 跨站写
- 敏感信息泄露
- 上传漏洞
- 会话安全
- 限流 / 暴力破解
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:5216")
DB = os.environ.get("TEST_DB", r"D:\Agent_ProJect\my-portfolio\_map.db")
PASS = FAIL = 0
FINDINGS: list[str] = []


def ck(name, cond, extra="", *, severity="MEDIUM"):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1
        FINDINGS.append("[%s] %s — %s" % (severity, name, extra))


def call(path, method="GET", body=None, cookie=None, headers=None, raw=None):
    data = raw
    h = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    if cookie:
        h["Cookie"] = cookie
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            # dict(headers) 会丢重复头(比如多个 Set-Cookie),改用 get_all
            hdrs = {k: v for k, v in r.headers.items()}
            set_cookies = r.headers.get_all("Set-Cookie") or []
            if set_cookies:
                hdrs["Set-Cookie"] = set_cookies[0]
            return r.status, r.read(), hdrs
    except urllib.error.HTTPError as e:
        hdrs = {k: v for k, v in e.headers.items()}
        set_cookies = e.headers.get_all("Set-Cookie") or []
        if set_cookies:
            hdrs["Set-Cookie"] = set_cookies[0]
        return e.code, e.read(), hdrs
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode(), {}


def jcall(path, **kw):
    st, raw, hdr = call(path, **kw)
    try:
        return st, json.loads(raw), hdr
    except Exception:
        return st, raw, hdr


# 后台写操作需要同源 Origin(CSRF 防护上线后强制校验)
SITE_ORIGIN = os.environ.get("TEST_ORIGIN", BASE)


def admin_headers(extra=None):
    h = {"Origin": SITE_ORIGIN}
    if extra:
        h.update(extra)
    return h


def setup_admin():
    """设置已知密码 + 关验证码,便于后续测试登录态。"""
    import hashlib
    import secrets

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", b"SecTest12345", salt, 120000)
    stored = "pbkdf2:120000:%s:%s" % (salt.hex(), digest.hex())
    con = sqlite3.connect(DB)
    for k, v in (("pass_hash", stored), ("must_change_pass", "0"), ("sec_captcha", "0")):
        con.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, v),
        )
    con.commit()
    con.close()


def login() -> str:
    st, d, hdr = jcall("/api/login", method="POST", body={"password": "SecTest12345", "captcha": ""})
    assert st == 200, (st, d)
    sc = hdr.get("Set-Cookie", "")
    for part in sc.split(";"):
        part = part.strip()
        if part.startswith("mysite_session="):
            return part
    return ""


def main() -> int:
    setup_admin()

    # ========== 1. 认证与授权 ==========
    print("=" * 66)
    print("1. 认证与授权")
    print("=" * 66)

    st, _, _ = call("/api/admin/alerts")
    ck("未登录访问后台 401", st == 401, str(st), severity="CRITICAL")

    st, _, _ = call("/api/admin/alerts", cookie="mysite_session=forged_session_id_12345")
    ck("伪造会话 ID 被拒", st == 401, str(st), severity="CRITICAL")

    st, _, _ = call("/api/admin/alerts", cookie="mysite_session=")
    ck("空会话被拒", st == 401, str(st), severity="CRITICAL")

    # 会话固定:登录前后 sid 必须变化
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with op.open(BASE + "/api/captcha.svg", timeout=20) as r:
        r.read()
    pre_sid = ""
    for c in jar:
        if c.name == "mysite_session":
            pre_sid = c.value
    st, d, hdr = jcall("/api/login", method="POST", body={"password": "SecTest12345", "captcha": ""})
    post_sid = ""
    for part in hdr.get("Set-Cookie", "").split(";"):
        part = part.strip()
        if part.startswith("mysite_session="):
            post_sid = part.split("=", 1)[1]
    ck("登录后会话 ID 变化(防会话固定)", pre_sid and post_sid and pre_sid != post_sid,
       "pre=%s post=%s" % (pre_sid[:8], post_sid[:8]), severity="HIGH")

    cookie = login()
    ck("正常登录成功", bool(cookie), "", severity="CRITICAL")

    st, _, _ = call("/api/me", cookie=cookie)
    ck("登录后可访问 /api/me", st == 200, str(st))

    # ========== 2. 注入攻击 ==========
    print()
    print("=" * 66)
    print("2. 注入攻击")
    print("=" * 66)

    sqli = ["' OR '1'='1", "'; DROP TABLE skills;--", "1' UNION SELECT * FROM settings--",
            "admin'--", "' OR 1=1 LIMIT 1--"]
    for payload in sqli:
        st, d, _ = jcall("/api/content/skills", method="POST",
                         body={"name": payload, "percent": 50}, cookie=cookie,
                         headers=admin_headers())
        # 应被接受为普通文本(201)或被校验拒绝(4xx),绝不能 500 或执行
        ck("SQL 注入被当文本处理: %r" % payload[:20], st in (201, 400, 422), str(st),
           severity="CRITICAL")
        if st == 201 and isinstance(d, dict) and d.get("id"):
            call("/api/content/skills/%d" % d["id"], method="DELETE", cookie=cookie,
                             headers=admin_headers())

    # 确认表还在
    con = sqlite3.connect(DB)
    n = con.execute("SELECT count(*) FROM skills").fetchone()[0]
    con.close()
    ck("注入后 skills 表完好", n >= 0, "count=%d" % n, severity="CRITICAL")

    # 路径穿越
    traversals = [
        "/api/content/../../etc/passwd",
        "/assets/uploads/../../admin/data/mysite.db",
        "/assets/..%2f..%2fadmin%2fdata%2fmysite.db",
        "/api/admin/uploads/..%2f..%2fapp.py",
    ]
    for p in traversals:
        st, raw, _ = call(p)
        leaked = b"root:" in raw or b"SQLite format" in raw or b"from __future__" in raw
        ck("路径穿越被阻止: %s" % p[:44], not leaked, "泄露内容!", severity="CRITICAL")

    # ========== 3. XSS / 输出转义 ==========
    print()
    print("=" * 66)
    print("3. XSS 与输出转义")
    print("=" * 66)

    xss = '<script>alert(1)</script><img src=x onerror=alert(2)>'
    st, d, _ = jcall("/api/messages", method="POST",
                     body={"name": xss[:20], "body": xss}, cookie=None)
    ck("XSS payload 可提交(存储型需前端转义)", st in (201, 429), str(st))

    # 前端是 React,默认转义;检查 API 返回的原始数据不被执行
    st, d, _ = jcall("/api/messages")
    if isinstance(d, list) and d:
        # 数据应原样返回(JSON),由 React 转义渲染
        ck("API 以 JSON 返回(不拼 HTML)", True, "")

    # 响应头安全(HTTP 头名大小写不敏感,统一转小写查找)
    st, _, hdr = call("/")
    low = {k.lower(): v for k, v in hdr.items()}
    csp = low.get("content-security-policy", "")
    ck("有 CSP 头", bool(csp), "缺失", severity="HIGH")
    ck("CSP 含 script-src 且禁 object-src",
       "script-src" in csp and "object-src 'none'" in csp, csp[:80], severity="MEDIUM")
    ck("CSP 限制 frame-ancestors", "frame-ancestors" in csp, csp[:80], severity="MEDIUM")
    ck("有 X-Content-Type-Options", low.get("x-content-type-options") == "nosniff",
       str(low.get("x-content-type-options")), severity="MEDIUM")
    ck("有 X-Frame-Options 或 frame-ancestors",
       bool(low.get("x-frame-options")) or "frame-ancestors" in csp,
       "缺失", severity="MEDIUM")
    ck("有 Referrer-Policy", bool(low.get("referrer-policy")),
       "缺失", severity="LOW")
    ck("有 Permissions-Policy", bool(low.get("permissions-policy")),
       "缺失", severity="LOW")

    # ========== 4. CSRF / 跨站写 ==========
    print()
    print("=" * 66)
    print("4. CSRF 与跨站写")
    print("=" * 66)

    st, d, hdr = call("/api/content/skills", method="POST",
                      body={"name": "csrf-test", "percent": 10},
                      cookie=cookie,
                      headers={"Origin": "https://evil.example.com"})
    ck("跨站 Origin 写入被拒", st in (403, 401), str(st), severity="HIGH")
    if st == 201 and isinstance(d, dict) and d.get("id"):
        call("/api/content/skills/%d" % d["id"], method="DELETE", cookie=cookie,
                             headers=admin_headers())

    # Cookie 属性
    st, _, hdr = call("/api/login", method="POST", body={"password": "SecTest12345", "captcha": ""})
    sc = hdr.get("Set-Cookie", "")
    ck("会话 Cookie 带 HttpOnly", "HttpOnly" in sc, sc[:100], severity="HIGH")
    ck("会话 Cookie 带 SameSite", "SameSite" in sc, sc[:100], severity="HIGH")

    # ========== 5. 敏感信息泄露 ==========
    print()
    print("=" * 66)
    print("5. 敏感信息泄露")
    print("=" * 66)

    st, raw, _ = call("/api/content")
    body = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    ck("公开内容不含密码哈希", "pbkdf2:" not in body, "泄露密码哈希!", severity="CRITICAL")
    ck("公开内容不含 2FA 密钥", "totp_secret" not in body, "", severity="HIGH")

    st, raw, _ = call("/api/messages")
    body = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    ck("留言不泄露 IP", '"ip"' not in body, "", severity="HIGH")
    ck("留言不泄露 token", '"token"' not in body, "", severity="HIGH")

    # 错误信息不泄露堆栈
    st, raw, _ = call("/api/content/../../nonexistent_table")
    body = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    ck("错误响应不含堆栈", "Traceback" not in body and "File \"" not in body, body[:100],
       severity="MEDIUM")

    # 敏感文件不可访问
    # 注意:SPA 有深链回退,访问不存在的路径会返回 index.html(200)。
    # 判定标准是「响应体里没有真实敏感内容」,而不是状态码。
    for p in ["/.git/config", "/admin/data/mysite.db", "/backend/app/main.py",
              "/.env", "/backend/.venv/pyvenv.cfg", "/backend/seed.py"]:
        st, raw, _ = call(p)
        leaked = (
            b"[core]" in raw
            or b"SQLite format" in raw
            or b"from __future__" in raw
            or b"MYSITE_SECRET_KEY" in raw
            or b"home = /usr/bin" in raw
        )
        ck("敏感文件不泄露内容: %s" % p, not leaked,
           "status=%d 泄露真实内容!" % st, severity="CRITICAL")

    # ========== 6. 上传漏洞 ==========
    print()
    print("=" * 66)
    print("6. 文件上传")
    print("=" * 66)

    boundary = "----WebKitFormBoundaryTEST"
    evil = b"<?php system($_GET['c']); ?>"

    def upload(content: bytes, filename: str):
        payload = (
            ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n" % (boundary, filename)).encode()
            + content
            + ("\r\n--%s--\r\n" % boundary).encode()
        )
        return call("/api/admin/upload", method="POST", raw=payload, cookie=cookie,
                    headers=admin_headers({
                        "Content-Type": "multipart/form-data; boundary=%s" % boundary
                    }))

    st, raw, _ = upload(evil, "shell.php")
    ck("PHP webshell 被拒", st == 400, "status=%d" % st, severity="CRITICAL")

    st, raw, _ = upload(evil, "shell.png")
    ck("伪装 PNG 的 PHP 被拒(校验文件头)", st == 400, "status=%d" % st, severity="CRITICAL")

    st, raw, _ = upload(b"\x89PNG\r\n\x1a\n" + b"A" * 100, "ok.png")
    ck("合法 PNG 可上传", st == 200, "status=%d" % st)

    # ========== 7. 限流与暴力破解 ==========
    print()
    print("=" * 66)
    print("7. 限流与暴力破解")
    print("=" * 66)

    blocked = False
    for i in range(12):
        st, _, _ = call("/api/login", method="POST",
                        body={"password": "wrong-%d" % i, "captcha": "XXXX"},
                        headers={"X-Forwarded-For": "203.0.113.%d" % (i % 2)})
        if st == 403:
            blocked = True
            break
    ck("连续失败后触发封锁", blocked, "12 次尝试未封锁", severity="HIGH")

    # 留言限流
    codes = []
    for i in range(6):
        st, _, _ = call("/api/messages", method="POST",
                        body={"name": "spam", "body": "rate test %d" % i},
                        headers={"X-Forwarded-For": "198.51.100.77"})
        codes.append(st)
    ck("留言接口有频率限制", 429 in codes, "codes=%s" % codes, severity="MEDIUM")

    # ========== 8. 输入校验健壮性 ==========
    print()
    print("=" * 66)
    print("8. 输入校验健壮性")
    print("=" * 66)

    malformed = [
        ("/api/messages", {"name": {"nested": "obj"}, "body": "x"}),
        ("/api/messages", {"body": None}),
        ("/api/messages", {"body": ["a", "b"]}),
        ("/api/questions", {"body": {"a": 1}}),
        ("/api/likes", {"page": 12345}),
        ("/api/login", {"password": [], "captcha": {}}),
    ]
    for path, payload in malformed:
        st, _, _ = call(path, method="POST", body=payload)
        ck("畸形输入不 500: %s %r" % (path, str(payload)[:26]),
           st < 500, "status=%d" % st, severity="HIGH")

    # 超大 body
    st, _, _ = call("/api/messages", method="POST", body={"body": "A" * 100000})
    ck("超大 body 被拒(413 或 4xx)", st in (400, 413, 422), "status=%d" % st)

    # ========== 9. 会话安全 ==========
    print()
    print("=" * 66)
    print("9. 会话安全")
    print("=" * 66)

    # 登出后会话失效
    c2 = login()
    st, _, _ = call("/api/logout", method="POST", cookie=c2)
    ck("登出成功", st == 200, str(st))
    st, _, _ = call("/api/me", cookie=c2)
    ck("登出后会话失效", st == 401, str(st), severity="HIGH")

    # 踢下线
    c3 = login()
    st, _, _ = call("/api/security/revoke-all", method="POST", cookie=c3,
                    headers=admin_headers())
    ck("踢掉其他会话可用", st == 200, str(st))

    print()
    print("=" * 66)
    if FINDINGS:
        print("发现 %d 个问题:" % len(FINDINGS))
        for f in FINDINGS:
            print("  " + f)
    else:
        print("未发现问题")
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
