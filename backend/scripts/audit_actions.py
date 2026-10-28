"""管理动作实测:审核/踢会话/解封/改设置,验证参数传递真的对。

覆盖那些「契约检查只能验证路径存在」的接口。
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:5213")
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
    # 设已知密码 + 关验证码 + 关强制改密
    import secrets
    from app.core.security import hash_password

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", b"AuditPass123", salt, 120000)
    stored = "pbkdf2:120000:%s:%s" % (salt.hex(), digest.hex())

    con = sqlite3.connect(DB)
    for k, v in (
        ("pass_hash", stored),
        ("must_change_pass", "0"),
        ("sec_captcha", "0"),
    ):
        con.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, v),
        )
    # 造一条待审留言 + 一个待答提问
    now = int(time.time())
    con.execute(
        "INSERT INTO messages(name,body,color,ts,ip,shown,reply,token) "
        "VALUES('测试','待审内容','pink',?,'1.2.3.4',0,'','tok')",
        (now,),
    )
    mid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        "INSERT INTO questions(body,ts,ip,shown,answer,answered_ts) "
        "VALUES('待答问题',?,'1.2.3.4',0,'',0)",
        (now,),
    )
    qid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    # 造一条封锁记录
    con.execute(
        "INSERT INTO login_fails(ip,count,blocked_until,last_ts) VALUES('9.9.9.9',5,?,?) "
        "ON CONFLICT(ip) DO UPDATE SET blocked_until=excluded.blocked_until",
        (now + 600, now),
    )
    con.commit()
    con.close()

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(path, method="GET", body=None):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
        try:
            with op.open(req, timeout=20) as r:
                raw = r.read()
                try:
                    return r.status, json.loads(raw)
                except Exception:
                    return r.status, raw
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, raw

    st, d = call("/api/login", "POST", {"password": "AuditPass123", "captcha": ""})
    ck("登录", st == 200, str(st) + " " + str(d))

    # --- 留言审核 ---
    print("\n=== 留言审核 ===")
    st, d = call("/api/messages/admin")
    ck("拉取留言列表", st == 200 and isinstance(d, list), str(st))
    before = next((x for x in d if x["id"] == mid), None) if isinstance(d, list) else None
    ck("找到待审留言", before is not None, str(mid))
    if before:
        ck("初始为待审(shown=0)", before.get("shown") == 0, str(before))

    st, d = call(f"/api/messages/{mid}/mod?action=approve", "POST")
    ck("通过审核 200", st == 200, str(st) + " " + str(d))

    st, d = call("/api/messages/admin")
    after = next((x for x in d if x["id"] == mid), None) if isinstance(d, list) else None
    ck("审核后 shown=1", after is not None and after.get("shown") == 1, str(after))

    # 前台应能看到
    st, d = call("/api/messages")
    ck("前台可见已审留言", st == 200 and any(x["id"] == mid for x in d), "")

    # --- 提问回答 ---
    print("\n=== 提问回答 ===")
    st, d = call(f"/api/questions/{qid}/mod?action=approve&answer=%E6%88%91%E7%9A%84%E5%9B%9E%E7%AD%94", "POST")
    ck("回答问题 200", st == 200, str(st) + " " + str(d))

    st, d = call("/api/questions/admin")
    q = next((x for x in d if x["id"] == qid), None) if isinstance(d, list) else None
    ck("答案已保存", q is not None and q.get("answer") == "我的回答", str(q))
    ck("已回答后公开(shown=1)", q is not None and q.get("shown") == 1, str(q))

    st, d = call("/api/questions")
    ck("前台可见已答问题", st == 200 and any(x["id"] == qid for x in d), "")

    # --- 解封 IP ---
    print("\n=== 封锁名单 ===")
    st, d = call("/api/security/blocked")
    ck("拉取封锁名单", st == 200 and isinstance(d, list), str(st))
    ck("含 9.9.9.9", any(x["ip"] == "9.9.9.9" for x in d), str(d))

    st, d = call("/api/security/unblock?ip=9.9.9.9", "POST")
    ck("解封 200", st == 200, str(st) + " " + str(d))

    st, d = call("/api/security/blocked")
    ck("解封后名单为空", not any(x["ip"] == "9.9.9.9" for x in d), str(d))

    # --- 安全设置 ---
    print("\n=== 安全设置 ===")
    st, d = call("/api/security/settings")
    ck("读取设置", st == 200 and "fail_threshold" in d, str(st))

    st, d = call("/api/security/settings", "POST", {"fail_threshold": 7, "block_minutes": 20})
    ck("更新设置 200", st == 200, str(st) + " " + str(d))
    ck("fail_threshold 已更新", d.get("fail_threshold") == "7", str(d))
    ck("block_minutes 已更新", d.get("block_minutes") == "20", str(d))

    # 越界应拒绝
    st, d = call("/api/security/settings", "POST", {"fail_threshold": 999})
    ck("越界值被拒(400)", st == 400, str(st) + " " + str(d))

    st, d = call("/api/security/settings", "POST", {"captcha_len": "abc"})
    ck("非数字被拒(400)", st == 400, str(st) + " " + str(d))

    # --- 会话管理 ---
    print("\n=== 会话管理 ===")
    st, d = call("/api/security/sessions")
    ck("拉取会话列表", st == 200 and isinstance(d, list) and len(d) >= 1, str(st))

    # --- 审计日志 ---
    print("\n=== 审计日志 ===")
    st, d = call("/api/security/audit")
    ck("拉取审计日志", st == 200 and isinstance(d, list), str(st))
    actions = {x["action"] for x in d} if isinstance(d, list) else set()
    ck("记录了登录", "login_ok" in actions, str(sorted(actions)[:8]))
    ck("记录了审核动作", any(a.startswith("message_") for a in actions), str(sorted(actions)[:8]))

    # --- 站点信息 ---
    print("\n=== 站点信息 ===")
    st, d = call("/api/site")
    original = d.get("site_slogan") if isinstance(d, dict) else None
    payload = dict(d)
    payload["site_slogan"] = "审计测试标语"
    st, d2 = call("/api/site", "PUT", payload)
    ck("更新站点信息 200", st == 200, str(st) + " " + str(d2)[:80])
    st, d3 = call("/api/site")
    ck("标语已生效", d3.get("site_slogan") == "审计测试标语", str(d3.get("site_slogan")))

    # 还原
    payload["site_slogan"] = original
    call("/api/site", "PUT", payload)

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
