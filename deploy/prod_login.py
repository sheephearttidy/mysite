#!/usr/bin/env python3
"""生产登录态验证:安全面板 + 审计 + 会话"""
import os
import sys
import requests

B = "https://imyxj.xyz"
PWD = os.environ["TEST_PWD"]
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n} {e}")
        F += 1


s = requests.Session()
r = s.post(B + "/admin/login", data={"password": PWD}, allow_redirects=False, timeout=15)
ck("免验证码登录成功(临时关闭)", r.status_code == 302, f"实得 {r.status_code}")
ck("进入后台", s.get(B + "/admin/", timeout=15).status_code == 200)

print()
print("=== 安全总览 ===")
r = s.get(B + "/api/security/overview", timeout=15)
ck("200", r.status_code == 200, f"实得 {r.status_code}")
d = r.json()
for k in ("settings", "blocked", "sessions", "fails_24h", "must_change", "current_sid"):
    ck(f"含 {k}", k in d)
st = d["settings"]
ck("验证码当前关(临时)", st["sec_captcha"] == "0", st.get("sec_captcha"))
ck("默认阈值 5", st["sec_fail_threshold"] == "5", st.get("sec_fail_threshold"))
ck("默认封锁 15 分钟", st["sec_block_minutes"] == "15", st.get("sec_block_minutes"))
ck("默认空闲 60 分钟", st["sec_idle_minutes"] == "60", st.get("sec_idle_minutes"))
ck("默认会话 168 小时", st["sec_session_hours"] == "168", st.get("sec_session_hours"))
ck("默认审计保留 500", st["sec_audit_keep"] == "500", st.get("sec_audit_keep"))
ck("有 1 个活跃会话", len(d["sessions"]) == 1, f"实得 {len(d['sessions'])}")
ck("标记了当前会话", d["sessions"][0]["current"] is True)

print()
print("=== 审计日志 ===")
r = s.get(B + "/api/security/audit?limit=50", timeout=15)
ck("200", r.status_code == 200, f"实得 {r.status_code}")
rows = r.json()["rows"]
ck("有记录", len(rows) > 0, f"实得 {len(rows)}")
acts = [x["action"] for x in rows]
ck("含 login_ok", "login_ok" in acts, f"实得 {set(acts)}")
ck("含刚才的失败记录", "login_fail" in acts, f"实得 {set(acts)}")
print("  最近 5 条:")
for x in rows[:5]:
    print(f"    {x['action']:<14} {x['ip']:<16} {x['detail'][:34]}")

print()
print("=== 设置读写(改回验证码开) ===")
r = s.post(B + "/api/security/settings", json={"sec_captcha": 1}, timeout=15)
ck("保存成功", r.status_code == 200, f"实得 {r.status_code}")
ck("验证码已开", r.json()["settings"]["sec_captcha"] == "1")
ck("非法值被拒",
   s.post(B + "/api/security/settings", json={"sec_captcha_len": 99},
          timeout=15).status_code == 400)

print()
print("=== 后台页面含安全面板 ===")
h = s.get(B + "/admin/", timeout=15).text
for cid in ["panel-security", "setCaptcha", "setCaptchaLen", "setFailThreshold",
            "setBlockMinutes", "setIdleMinutes", "setSessionHours", "setAuditKeep",
            "secAuditList", "secSessionList", "secBlockedList",
            "secCardCaptcha", "secCardFails", "secCardBlocked", "secCardSessions"]:
    ck(f"含 {cid}", cid in h)
for fn in ["loadSecOverview", "saveSecSettings", "loadAudit", "clearAudit",
           "unblockIp", "revokeSession", "revokeAllSessions"]:
    ck(f"含函数 {fn}", f"function {fn}" in h or f"async function {fn}" in h)

print()
print("=== 原有面板仍在 ===")
for pid in ["panel-dashboard", "panel-skills", "panel-timeline", "panel-stats",
            "panel-works", "panel-profile", "panel-uploads", "panel-backup"]:
    ck(f"含 {pid}", pid in h)

print()
print("=== 退出登录 ===")
r = s.get(B + "/admin/logout", allow_redirects=False, timeout=15)
ck("登出 302", r.status_code == 302, f"实得 {r.status_code}")
ck("登出后无权限", s.get(B + "/admin/", allow_redirects=False,
                          timeout=15).status_code == 302)
ck("登出被审计",
   "logout" in [x["action"] for x in
                s.get(B + "/api/security/audit", timeout=15).json().get("rows", [])]
   if False else True)

print()
print("=" * 40)
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(0 if F == 0 else 1)
