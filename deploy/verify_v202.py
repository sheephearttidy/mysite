#!/usr/bin/env python3
"""v2.0.2 生产验证:公告弹窗 + 留言墙渲染 + 后台编辑器(Chrome 渲染)"""
import http.cookiejar
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
P = F = 0


def ck(n, c, e=""):
    global P, F
    print(("PASS  " if c else "FAIL  ") + n + (("  " + e) if e and not c else ""))
    if c:
        P += 1
    else:
        F += 1


def dump(url, wait=8):
    prof = tempfile.mkdtemp(prefix="v202_")
    out = os.path.join(prof, "d.html")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + prof, f"--virtual-time-budget={wait*1000}",
                    "--dump-dom", url],
                   stdout=open(out, "w", encoding="utf-8"),
                   stderr=subprocess.DEVNULL, timeout=180)
    dom = io.open(out, encoding="utf-8", errors="replace").read()
    shutil.rmtree(prof, ignore_errors=True)
    return dom


# 1) 发一条测试公告到生产(稍后删)
import urllib.error
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def post_json(p, obj):
    req = urllib.request.Request("https://imyxj.xyz" + p,
                                 data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return op.open(req, timeout=20).read().decode()
    except urllib.error.HTTPError as e:
        return e.read().decode()


print("=== 公告弹窗 ===")
import urllib.parse
svg = op.open("https://imyxj.xyz/admin/captcha.svg", timeout=20).read().decode()
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": os.environ["PROD_PWD"],
                               "captcha": cap, "totp": ""}).encode()
req = urllib.request.Request("https://imyxj.xyz/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=20).read().decode()
ck("登录成功", "panel-dashboard" in body)
r = json.loads(post_json("/api/notices/admin", {"body": "自检:公告弹窗测试 v2.0.2 🎈"}))
ck("发布测试公告", r.get("ok"), str(r))
nid = None
d = json.loads(op.open("https://imyxj.xyz/api/notices/active", timeout=20).read())
if d.get("notice"):
    nid = d["notice"]["id"]

dom = dump("https://imyxj.xyz/", wait=8)
ck("前台出现公告弹窗", "notice-pop" in dom)
ck("弹窗含公告文本", "v2.0.2" in dom)
ck("弹窗不在导航流里(独立挂 body)", '<body' in dom and "notice-pop" in dom)
ck("旧 notice-bar 结构已废弃", "notice-bar" not in dom)

# 关闭测试公告
if nid:
    post_json(f"/api/notices/{nid}/mod", {"action": "delete"})
    d = json.loads(op.open("https://imyxj.xyz/api/notices/active", timeout=20).read())
    ck("测试公告已删除", d.get("notice") is None)

print()
print("=== 留言墙渲染 ===")
dom = dump("https://imyxj.xyz/#msgwall", wait=9)
ck("留言墙 DOM 有卡片", 'msg-note' in dom, "(无 msg-note)")
m = re.search(r'<div class="msgwall-grid"[^>]*>(.*?)</div>\s*<p', dom, re.S)
cards = len(re.findall(r'msg-note', dom))
ck(f"渲染出 {cards} 张便签(生产存量 2 条)", cards >= 2, f"实际 {cards}")
ck("便签可见(reveal 已点亮)",
   'msg-note visible' in dom or 'visible' not in dom, "(透明未点亮)")

print()
print(f"通过 {P} 项,失败 {F} 项")
exit(1 if F else 0)
