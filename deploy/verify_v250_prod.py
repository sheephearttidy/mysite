#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生产验证:后台改站点信息 -> 前台生效 -> 改回默认"""
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
PROD = "https://imyxj.xyz"
PWD = os.environ.get("PROD_PWD", "")
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


cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = op.open(PROD + "/admin/captcha.svg", timeout=25).read().decode()
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
op.open(PROD + "/admin/login",
        urllib.parse.urlencode({"password": PWD, "captcha": code}).encode(), timeout=25)
print("登录完成\n")

print("=" * 60)
print("v2.5 生产验证")
print("=" * 60)

# 1. 读
r = json.loads(op.open(PROD + "/api/site", timeout=25).read())
ck("GET /api/site 正常", "values" in r and "fields" in r)
ck("9 个字段", len(r.get("fields", [])) == 9, str(len(r.get("fields", []))))
ck("当前姓名=至尊杰", r["values"]["site_owner"] == "至尊杰", r["values"]["site_owner"])

# 2. 写 -> 前台生效
req = urllib.request.Request(
    PROD + "/api/site", method="PUT",
    data=json.dumps({"site_owner": "测试小明", "site_school": "北京大学"}).encode(),
    headers={"Content-Type": "application/json"})
r2 = json.loads(op.open(req, timeout=25).read())
ck("PUT 保存成功", r2["values"]["site_owner"] == "测试小明", r2["values"]["site_owner"])

d = json.loads(urllib.request.urlopen(PROD + "/api/page/index", timeout=25).read())
ck("前台 API 立即生效", d["site"]["site_owner"] == "测试小明", d["site"]["site_owner"])

# Chrome 真机确认渲染
p = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--virtual-time-budget=15000", "--dump-dom", PROD + "/index.html"],
                   capture_output=True, encoding="utf-8", errors="replace", timeout=180)
dom = p.stdout
ck("前台渲染新姓名", "测试小明" in dom, "没渲染")
ck("旧姓名已清除", dom.count("至尊杰") == 0, f"残留 {dom.count('至尊杰')} 处")

# 3. 改回默认
req = urllib.request.Request(
    PROD + "/api/site", method="PUT",
    data=json.dumps({"site_owner": "至尊杰", "site_name": "至尊杰的小窝",
                     "site_school": "燕京理工学院",
                     "site_major": "计算机科学与技术", "site_grade": "2026 级",
                     "site_focus": "智能车 AI",
                     "site_slogan": "learning and building",
                     "site_credit": "纯手搓 + AI 协作",
                     "site_start_year": "2026"}).encode(),
    headers={"Content-Type": "application/json"})
r3 = json.loads(op.open(req, timeout=25).read())
ck("已恢复默认", r3["values"]["site_owner"] == "至尊杰", r3["values"]["site_owner"])
ck("学校已恢复", r3["values"]["site_school"] == "燕京理工学院", r3["values"]["site_school"])

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
for f in FAILS:
    print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
