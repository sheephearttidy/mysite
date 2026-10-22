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

# 先备份线上真实值,测完原样还原 —— 不能把用户自己填的内容冲掉
ORIG = json.loads(op.open(PROD + "/api/site", timeout=25).read())["values"]
print("已备份线上原值:", ORIG["site_owner"], "/", ORIG["site_focus"], "/", ORIG["site_credit"])

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
# 留言板里的署名是用户自己写的内容(数据库里的真实留言),不属于站点身份字段,
# 不该被改名逻辑改写。统计残留时先剔除留言区的署名。
dom_no_msg = re.sub(r'<b class="msg-name">.*?</b>', '', dom, flags=re.S)
ck("旧姓名已清除", dom_no_msg.count("至尊杰") == 0,
   f"残留 {dom_no_msg.count('至尊杰')} 处")

# 3. 还原线上真实值(不是恢复默认!用户自己填的 Agent / 版权必须原样还回去)
req = urllib.request.Request(
    PROD + "/api/site", method="PUT",
    data=json.dumps(ORIG).encode(),
    headers={"Content-Type": "application/json"})
r3 = json.loads(op.open(req, timeout=25).read())
ck("已还原线上原值", r3["values"] == ORIG,
   f'{r3["values"]} != {ORIG}')

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
for f in FAILS:
    print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
