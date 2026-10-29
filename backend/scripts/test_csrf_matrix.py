"""同源判定矩阵测试:各种 Origin/Host 组合下,后台写操作应正确放行/拒绝。"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import secrets
import sqlite3
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:5217")
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


def main() -> int:
    # 准备密码
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", b"OriginTest123", salt, 120000)
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

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(path, method="POST", origin=None, host=None, body=None):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json"}
        if origin is not None:
            h["Origin"] = origin
        if host is not None:
            h["Host"] = host
        req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
        try:
            with op.open(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    st = call("/api/login", body={"password": "OriginTest123", "captcha": ""})
    ck("登录", st == 200, str(st))

    print()
    print("=== 同源矩阵(Host=127.0.0.1)===")
    cases = [
        ("同源 http://127.0.0.1:5217", "http://127.0.0.1:5217", None, 201),
        ("同源不带端口", "http://127.0.0.1", None, 201),
        ("本地 localhost", "http://localhost:5217", None, 201),
        ("跨站 evil.com", "https://evil.example.com", None, 403),
        ("相似域名 evil-127.0.0.1.com", "http://evil-127.0.0.1.com", None, 403),
        ("127.0.0.1.evil.com", "http://127.0.0.1.evil.com", None, 403),
        ("无 Origin(纯脚本)", None, None, 403),
    ]
    for label, origin, host, expect in cases:
        st = call("/api/content/skills", origin=origin, host=host,
                  body={"name": "matrix", "percent": 10})
        ck("%s -> %s" % (label, expect), st == expect, "实际 %d" % st)

    print()
    print("=== www 与裸域各自同源 ===")
    # 模拟线上:Host=imyxj.xyz,Origin=https://imyxj.xyz -> 放行
    st = call("/api/content/skills", origin="https://imyxj.xyz",
              host="imyxj.xyz", body={"name": "matrix", "percent": 10})
    ck("Host=imyxj.xyz + Origin=imyxj.xyz -> 201", st == 201, "实际 %d" % st)

    # Host=www.imyxj.xyz,Origin=https://www.imyxj.xyz -> 放行
    st = call("/api/content/skills", origin="https://www.imyxj.xyz",
              host="www.imyxj.xyz", body={"name": "matrix", "percent": 10})
    ck("Host=www + Origin=www -> 201", st == 201, "实际 %d" % st)

    # Host=imyxj.xyz 但 Origin=evil -> 拒
    st = call("/api/content/skills", origin="https://evil.example.com",
              host="imyxj.xyz", body={"name": "matrix", "percent": 10})
    ck("Host=imyxj.xyz + Origin=evil -> 403", st == 403, "实际 %d" % st)

    print()
    print("=== 清理测试数据 ===")
    st, raw = None, None
    # 删掉刚插的
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM skills WHERE name='matrix'")
    con.commit()
    con.close()
    print("done")

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
