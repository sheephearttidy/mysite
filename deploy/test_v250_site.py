#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.5 站点信息功能验证:后台读写 API + 前台动态套用"""
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.environ.get("TEST_BASE", "http://127.0.0.1:15102")
PWD = os.environ.get("TEST_PWD", "admin")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PASS = FAIL = 0
FAILS = []


def ck(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        FAILS.append(name)
        print(f"  FAIL {name}  {detail}")


# ---------- 登录 ----------
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = op.open(BASE + "/admin/captcha.svg", timeout=20).read().decode()
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
op.open(BASE + "/admin/login",
        urllib.parse.urlencode({"password": PWD, "captcha": code}).encode(), timeout=20)
print("登录完成\n")

print("=" * 60)
print("v2.5 站点信息验证")
print("=" * 60)

# ---------- 1. 公开接口带 site ----------
for page in ("index", "about", "skills", "works", "campus", "contact", "map"):
    d = json.loads(op.open(BASE + "/api/page/" + page, timeout=20).read())
    ck(f"/api/page/{page} 含 site", "site" in d, str(list(d.keys())))
    if "site" in d:
        need = ["site_owner", "site_name", "site_school", "site_major",
                "site_grade", "site_focus", "site_slogan", "site_credit"]
        miss = [k for k in need if not d["site"].get(k)]
        ck(f"   {page} 字段齐全", not miss, str(miss))

# ---------- 2. 后台读 ----------
# 先把站点信息恢复默认,避免上一轮测试残留影响断言
req = urllib.request.Request(
    BASE + "/api/site", method="PUT",
    data=json.dumps({"site_owner": "至尊杰", "site_name": "至尊杰的小窝",
                     "site_school": "燕京理工学院",
                     "site_major": "计算机科学与技术", "site_grade": "2026 级",
                     "site_focus": "智能车 AI",
                     "site_slogan": "learning and building",
                     "site_credit": "纯手搓 + AI 协作",
                     "site_start_year": "2026"}).encode(),
    headers={"Content-Type": "application/json"})
op.open(req, timeout=20)

r = json.loads(op.open(BASE + "/api/site", timeout=20).read())
ck("GET /api/site 返回 values", "values" in r and "fields" in r)
ck("字段定义 9 个", len(r.get("fields", [])) == 9, str(len(r.get("fields", []))))
ck("默认值是至尊杰", r["values"].get("site_owner") == "至尊杰",
   r["values"].get("site_owner"))

# ---------- 3. 后台写 ----------
req = urllib.request.Request(
    BASE + "/api/site", method="PUT",
    data=json.dumps({"site_owner": "张三", "site_school": "清华大学",
                     "site_slogan": "just do it"}).encode(),
    headers={"Content-Type": "application/json"})
r2 = json.loads(op.open(req, timeout=20).read())
ck("PUT 保存成功", r2["values"]["site_owner"] == "张三", str(r2["values"].get("site_owner")))
ck("部分更新不影响其它字段",
   r2["values"]["site_major"] == "计算机科学与技术", r2["values"].get("site_major"))
ck("未提供的字段保持原值", r2["values"]["site_name"] == "至尊杰的小窝",
   r2["values"].get("site_name"))

# 空值回落默认
req = urllib.request.Request(
    BASE + "/api/site", method="PUT",
    data=json.dumps({"site_owner": "  "}).encode(),
    headers={"Content-Type": "application/json"})
r3 = json.loads(op.open(req, timeout=20).read())
ck("空值回落默认", r3["values"]["site_owner"] == "至尊杰", r3["values"].get("site_owner"))

# 白名单
req = urllib.request.Request(
    BASE + "/api/site", method="PUT",
    data=json.dumps({"hack_key": "x", "site_owner": "李四"}).encode(),
    headers={"Content-Type": "application/json"})
r4 = json.loads(op.open(req, timeout=20).read())
ck("非法字段被忽略", "hack_key" not in r4["values"], str(r4["values"].keys()))
ck("合法字段已保存", r4["values"]["site_owner"] == "李四")

# ---------- 4. 前台套用(Chrome 真机) ----------
r = subprocess.run(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--virtual-time-budget=15000", "--dump-dom", BASE + "/index.html"],
    capture_output=True, encoding="utf-8", errors="replace", timeout=180)
dom = r.stdout
ck("首屏显示新姓名", "李四" in dom, "没找到李四")
ck("站名联动(李四的小窝)", "李四的小窝" in dom, "站名没跟着姓名变")
ck("旧姓名已消失(正文)", dom.count("至尊杰") == 0, f"还有 {dom.count('至尊杰')} 处")
ck("标题含新姓名", "李四" in dom[:2000], dom[:200].replace("\n", " "))

# 恢复默认
req = urllib.request.Request(
    BASE + "/api/site", method="PUT",
    data=json.dumps({"site_owner": "至尊杰", "site_school": "燕京理工学院",
                     "site_slogan": "learning and building"}).encode(),
    headers={"Content-Type": "application/json"})
op.open(req, timeout=20)

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
for f in FAILS:
    print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
