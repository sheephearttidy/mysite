#!/usr/bin/env python3
"""测试:验证码 + 安全模块"""
import sys
import sqlite3
import requests

B = "http://127.0.0.1:5102"
DB = "/tmp/testapp/data/test.db"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n} {e}")
        F += 1


def reset():
    c = sqlite3.connect(DB)
    c.execute("DELETE FROM login_fails")
    c.execute("DELETE FROM sessions")
    c.execute("DELETE FROM audit")
    c.commit()
    c.close()


def set_sec(k, v):
    c = sqlite3.connect(DB)
    c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
              "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, str(v)))
    c.commit()
    c.close()


def login(sess, pwd="admin", use_cap=True):
    if use_cap:
        sess.get(f"{B}/admin/captcha.svg")
        txt = sess.get(f"{B}/__test/cap").json()["text"]
        return sess.post(f"{B}/admin/login",
                         data={"password": pwd, "captcha": txt},
                         allow_redirects=False)
    return sess.post(f"{B}/admin/login", data={"password": pwd},
                     allow_redirects=False)


print("=" * 50)
print("组 1:验证码图片")
print("=" * 50)
r = requests.get(f"{B}/admin/captcha.svg")
ck("返回 200", r.status_code == 200, f"实得 {r.status_code}")
ck("Content-Type 是 svg", "svg" in r.headers.get("Content-Type", ""),
   r.headers.get("Content-Type"))
ck("内容含 <svg", b"<svg" in r.content)
ck("禁止缓存", "no-store" in r.headers.get("Cache-Control", ""),
   r.headers.get("Cache-Control"))
svg = r.content.decode("utf-8", "ignore")
ck("有干扰线", svg.count("<path") >= 4, f"实得 {svg.count('<path')}")
ck("有噪点", svg.count("<circle") >= 20, f"实得 {svg.count('<circle')}")
ck("有 4 个字符", svg.count("<text") == 4, f"实得 {svg.count('<text')}")
ck("字符有旋转", "rotate(" in svg)

print()
print("=" * 50)
print("组 2:每次不同")
print("=" * 50)
s2 = requests.Session()
a = s2.get(f"{B}/admin/captcha.svg").content
b = s2.get(f"{B}/admin/captcha.svg").content
ck("两次内容不同", a != b)

print()
print("=" * 50)
print("组 3:验证码错 -> 失败")
print("=" * 50)
reset()
s = requests.Session()
s.get(f"{B}/admin/captcha.svg")
r = s.post(f"{B}/admin/login", data={"password": "admin", "captcha": "ZZZZ"},
           allow_redirects=False)
ck("重定向", r.status_code == 302, f"实得 {r.status_code}")
ck("仍未登录", s.get(f"{B}/admin/", allow_redirects=False).status_code == 302)
c = sqlite3.connect(DB)
n = c.execute("SELECT COUNT(*) FROM audit WHERE action='login_fail'").fetchone()[0]
ck("记录失败审计", n == 1, f"实得 {n}")
det = c.execute("SELECT detail FROM audit WHERE action='login_fail'").fetchone()
ck("原因是验证码", "验证码" in (det[0] if det else ""), f"实得 {det}")
c.close()

print()
print("=" * 50)
print("组 4:验证码对 + 密码错 -> 失败")
print("=" * 50)
reset()
s = requests.Session()
s.get(f"{B}/admin/captcha.svg")
txt = s.get(f"{B}/__test/cap").json()["text"]
ck("拿到验证码", bool(txt), f"实得 {txt}")
r = s.post(f"{B}/admin/login", data={"password": "wrong", "captcha": txt},
           allow_redirects=False)
ck("仍失败", s.get(f"{B}/admin/", allow_redirects=False).status_code == 302)
c = sqlite3.connect(DB)
n = c.execute("SELECT COUNT(*) FROM audit WHERE action='login_fail'").fetchone()[0]
ck("记了失败", n == 1, f"实得 {n}")
c.close()

print()
print("=" * 50)
print("组 5:验证码对 + 密码对 -> 成功")
print("=" * 50)
reset()
s = requests.Session()
r = login(s)
ck("重定向", r.status_code == 302, f"实得 {r.status_code}")
ck("跳到后台", "/admin" in r.headers.get("Location", ""))
ck("能访问后台", s.get(f"{B}/admin/").status_code == 200)
c = sqlite3.connect(DB)
ck("记录登录成功",
   c.execute("SELECT COUNT(*) FROM audit WHERE action='login_ok'").fetchone()[0] == 1)
ck("会话已登记",
   c.execute("SELECT COUNT(*) FROM sessions WHERE revoked=0").fetchone()[0] == 1)
c.close()

print()
print("=" * 50)
print("组 6:验证码复用被拒")
print("=" * 50)
reset()
s = requests.Session()
s.get(f"{B}/admin/captcha.svg")
txt = s.get(f"{B}/__test/cap").json()["text"]
s.post(f"{B}/admin/login", data={"password": "admin", "captcha": txt})
s.get(f"{B}/admin/logout")
s.post(f"{B}/admin/login", data={"password": "admin", "captcha": txt},
       allow_redirects=False)
ck("复用被拒", s.get(f"{B}/admin/", allow_redirects=False).status_code == 302)

print()
print("=" * 50)
print("组 7:失败封锁")
print("=" * 50)
reset()
set_sec("sec_fail_threshold", 3)
set_sec("sec_block_minutes", 5)
s = requests.Session()
for i in range(3):
    s.get(f"{B}/admin/captcha.svg")
    s.post(f"{B}/admin/login", data={"password": "bad", "captcha": "XXXX"})
c = sqlite3.connect(DB)
row = c.execute("SELECT count, blocked_until FROM login_fails").fetchone()
ck("有失败记录", row is not None)
if row:
    ck("已封锁", row[1] > 0, f"blocked_until={row[1]}")
ck("记录封锁审计",
   c.execute("SELECT COUNT(*) FROM audit WHERE action='login_block'").fetchone()[0] == 1)
c.close()
s2 = requests.Session()
s2.get(f"{B}/admin/captcha.svg")
txt = s2.get(f"{B}/__test/cap").json()["text"]
s2.post(f"{B}/admin/login", data={"password": "admin", "captcha": txt})
ck("封锁期无法登录", s2.get(f"{B}/admin/", allow_redirects=False).status_code == 302)

print()
print("=" * 50)
print("组 8:安全总览")
print("=" * 50)
reset()
set_sec("sec_fail_threshold", 5)
set_sec("sec_block_minutes", 15)
s = requests.Session()
login(s)
r = s.get(f"{B}/api/security/overview")
ck("200", r.status_code == 200, f"实得 {r.status_code}")
d = r.json()
for k in ("settings", "blocked", "sessions", "fails_24h", "must_change"):
    ck(f"含 {k}", k in d)
ck("默认验证码开", d["settings"]["sec_captcha"] == "1", d["settings"].get("sec_captcha"))

print()
print("=" * 50)
print("组 9:设置读写与校验")
print("=" * 50)
r = s.post(f"{B}/api/security/settings", json={"sec_captcha": 0})
ck("关闭验证码", r.status_code == 200 and r.json()["settings"]["sec_captcha"] == "0")
ck("位数超范围被拒",
   s.post(f"{B}/api/security/settings", json={"sec_captcha_len": 9}).status_code == 400)
ck("阈值 0 被拒",
   s.post(f"{B}/api/security/settings", json={"sec_fail_threshold": 0}).status_code == 400)
ck("非数字被拒",
   s.post(f"{B}/api/security/settings", json={"sec_fail_threshold": "abc"}).status_code == 400)
ck("未知键被拒",
   s.post(f"{B}/api/security/settings", json={"evil": 1}).status_code == 400)
ck("空请求被拒", s.post(f"{B}/api/security/settings", json={}).status_code == 400)
r = s.post(f"{B}/api/security/settings", json={"sec_captcha": 1, "sec_captcha_len": 5})
ck("恢复验证码", r.status_code == 200)
ck("位数已改", r.json()["settings"]["sec_captcha_len"] == "5")

print()
print("=" * 50)
print("组 10:关闭验证码后可免验证码")
print("=" * 50)
reset()
# reset() 清空了 sessions 表,原会话已失效,必须重新登录
s = requests.Session()
login(s)
s.post(f"{B}/api/security/settings", json={"sec_captcha": 0})
s2 = requests.Session()
login(s2, use_cap=False)
ck("无验证码能登录", s2.get(f"{B}/admin/").status_code == 200)
s.post(f"{B}/api/security/settings", json={"sec_captcha": 1, "sec_captcha_len": 4})

print()
print("=" * 50)
print("组 11:审计日志")
print("=" * 50)
r = s.get(f"{B}/api/security/audit?limit=50")
ck("200", r.status_code == 200, f"实得 {r.status_code}")
rows = r.json()["rows"]
ck("有记录", len(rows) > 0, f"实得 {len(rows)}")
acts = {x["action"] for x in rows}
ck("含 login_ok", "login_ok" in acts, f"实得 {acts}")
ck("含 sec_settings", "sec_settings" in acts, f"实得 {acts}")
ck("limit 非法不崩", s.get(f"{B}/api/security/audit?limit=abc").status_code == 200)
ck("limit 过大被夹", len(s.get(f"{B}/api/security/audit?limit=9999").json()["rows"]) <= 500)

print()
print("=" * 50)
print("组 12:会话踢下线")
print("=" * 50)
reset()
sa = requests.Session()
login(sa)
sb = requests.Session()
login(sb)
d = sa.get(f"{B}/api/security/overview").json()
ck("两个会话", len(d["sessions"]) == 2, f"实得 {len(d['sessions'])}")
ck("标记当前会话", sum(1 for x in d["sessions"] if x["current"]) == 1)
other = [x for x in d["sessions"] if not x["current"]][0]
r = sa.post(f"{B}/api/security/revoke", json={"sid": other["sid"]})
ck("踢下线成功", r.status_code == 200, f"实得 {r.status_code}")
ck("被踢会话失效", sb.get(f"{B}/admin/", allow_redirects=False).status_code == 302)
ck("自己仍有效", sa.get(f"{B}/admin/").status_code == 200)
ck("踢自己会被拒",
   sa.post(f"{B}/api/security/revoke",
           json={"sid": d["current_sid"]}).status_code == 400)
ck("缺 sid 被拒", sa.post(f"{B}/api/security/revoke", json={}).status_code == 400)

print()
print("=" * 50)
print("组 13:踢全部会话")
print("=" * 50)
reset()
sa = requests.Session()
login(sa)
sb = requests.Session()
login(sb)
r = sa.post(f"{B}/api/security/revoke-all")
ck("成功", r.status_code == 200)
ck("踢了 1 个", r.json()["revoked"] == 1, f"实得 {r.json().get('revoked')}")
ck("sb 失效", sb.get(f"{B}/admin/", allow_redirects=False).status_code == 302)
ck("sa 仍有效", sa.get(f"{B}/admin/").status_code == 200)

print()
print("=" * 50)
print("组 14:解除封锁(用不同 IP 模拟攻击者)")
print("=" * 50)
reset()
set_sec("sec_fail_threshold", 2)
set_sec("sec_block_minutes", 10)
# 攻击者 IP 用 X-Real-IP 模拟(生产里 nginx 会写入真实客户端 IP)
ATTACKER = {"X-Real-IP": "203.0.113.66"}
s3 = requests.Session()
s3.headers.update(ATTACKER)
for i in range(2):
    s3.get(f"{B}/admin/captcha.svg", headers=ATTACKER)
    s3.post(f"{B}/admin/login",
            data={"password": "x", "captcha": "YYYY"}, headers=ATTACKER)
sa2 = requests.Session()
login(sa2)
d = sa2.get(f"{B}/api/security/overview").json()
ck("封锁列表有 1 个", len(d["blocked"]) == 1, f"实得 {len(d['blocked'])}")
ck("封锁的是攻击者 IP", d["blocked"][0]["ip"] == "203.0.113.66",
   f"实得 {d['blocked'][0]['ip']}")
ck("管理员自己没被锁", sa2.get(f"{B}/admin/").status_code == 200)
ip = d["blocked"][0]["ip"]
r = sa2.post(f"{B}/api/security/unblock", json={"ip": ip})
ck("解除成功", r.status_code == 200 and r.json()["ok"])
ck("列表已空", len(sa2.get(f"{B}/api/security/overview").json()["blocked"]) == 0)
ck("解除后攻击者能登录", login(requests.Session()).status_code == 302)
ck("缺 ip 被拒", sa2.post(f"{B}/api/security/unblock", json={}).status_code == 400)
set_sec("sec_fail_threshold", 5)

print()
print("=" * 50)
print("组 15:未登录不能碰安全接口")
print("=" * 50)
for path, method in [("/api/security/overview", "get"), ("/api/security/settings", "get"),
                     ("/api/security/audit", "get"), ("/api/security/settings", "post"),
                     ("/api/security/unblock", "post"), ("/api/security/revoke", "post"),
                     ("/api/security/revoke-all", "post"), ("/api/security/audit", "delete")]:
    r = getattr(requests, method)(f"{B}{path}", json={})
    ck(f"{method.upper()} {path}", r.status_code == 401, f"实得 {r.status_code}")

print()
print("=" * 50)
print("组 16:原有功能完好")
print("=" * 50)
sa = requests.Session()
login(sa)
d = sa.get(f"{B}/api/content").json()
ck("skills=8", len(d["skills"]) == 8)
ck("works=6", len(d["works"]) == 6)
ck("profile=7", len(d["profile"]) == 7)
ck("导出 200", sa.get(f"{B}/api/export").status_code == 200)
ck("看板 200", sa.get(f"{B}/api/stats/visits").status_code == 200)
h = sa.get(f"{B}/admin/").text
for cid in ["panel-security", "setCaptcha", "secAuditList", "secSessionList",
            "secBlockedList", "secCardCaptcha"]:
    ck(f"页面含 {cid}", cid in h)

print()
print("=" * 50)
print("组 17:登录页含验证码")
print("=" * 50)
h = requests.get(f"{B}/admin/login").text
ck("验证码输入框", 'name="captcha"' in h)
ck("验证码图片", 'id="capImg"' in h)
ck("指向 captcha.svg", '/admin/captcha.svg' in h)
ck("点击刷新", 'capBox' in h)
ck("提示 3 分钟", "3 分钟" in h)

print()
print("=" * 50)
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(0 if F == 0 else 1)
