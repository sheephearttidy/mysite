"""运行时权限实测:未登录状态下打一遍所有接口,验证该拦的都拦住了。

这比静态分析可靠 —— 直接看真实响应码,不依赖框架内部结构。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5213"

# 期望未登录时返回 401 的接口(后台专属)
MUST_401 = [
    ("GET", "/api/admin/alerts"),
    ("GET", "/api/admin/backup/export"),
    ("POST", "/api/admin/backup/import"),
    ("GET", "/api/admin/fx"),
    ("PUT", "/api/admin/fx"),
    ("POST", "/api/admin/upload"),
    ("GET", "/api/admin/uploads"),
    ("DELETE", "/api/admin/uploads/x.png"),
    ("GET", "/api/stats/visits"),
    ("GET", "/api/stats/visits/csv"),
    ("GET", "/api/security/audit"),
    ("DELETE", "/api/security/audit"),
    ("GET", "/api/security/blocked"),
    ("GET", "/api/security/sessions"),
    ("GET", "/api/security/settings"),
    ("POST", "/api/security/settings"),
    ("POST", "/api/security/revoke"),
    ("POST", "/api/security/revoke-all"),
    ("POST", "/api/security/unblock"),
    ("GET", "/api/messages/admin"),
    ("POST", "/api/messages/1/mod"),
    ("GET", "/api/questions/admin"),
    ("POST", "/api/questions/1/mod"),
    ("POST", "/api/content/skills"),
    ("PUT", "/api/content/skills/1"),
    ("DELETE", "/api/content/skills/1"),
    ("PUT", "/api/site"),
    ("GET", "/api/me"),
    ("POST", "/api/password"),
]

# 期望未登录也能访问的公开接口
MUST_PUBLIC = [
    ("GET", "/api/health"),
    ("GET", "/api/site"),
    ("GET", "/api/content"),
    ("GET", "/api/content/skills"),
    ("GET", "/api/page/index"),
    ("GET", "/api/messages"),
    ("GET", "/api/questions"),
    ("GET", "/api/likes"),
    ("GET", "/api/map"),
    ("GET", "/api/notices/active"),
    ("GET", "/api/countdowns/active"),
    ("GET", "/api/captcha.svg"),
]

PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def call(method, path):
    data = None
    headers = {}
    if method in ("POST", "PUT"):
        data = b"{}"
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001
        return f"ERR:{e}"


def main() -> int:
    print("=" * 60)
    print("未登录时必须被拒的接口")
    print("  403 = CSRF 中间件先拒;401 = 认证层拒。两者都表示未放行。")
    print("=" * 60)
    for method, path in MUST_401:
        st = call(method, path)
        ck(f"{method:6s} {path:34s} -> {st}", st in (401, 403), f"期望 401/403,实际 {st}")

    print()
    print("=" * 60)
    print("公开接口(未登录应可访问)")
    print("=" * 60)
    for method, path in MUST_PUBLIC:
        st = call(method, path)
        ck(f"{method:6s} {path:34s} -> {st}", st == 200, f"期望 200,实际 {st}")

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
