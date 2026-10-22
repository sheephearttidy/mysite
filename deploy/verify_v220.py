#!/usr/bin/env python3
"""v2.2.0 生产验证:资产版本 + 三页新组件 Chrome 渲染 + 后台注入"""
import re
import subprocess
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PASS = FAIL = 0


def ck(name, cond):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def get(url):
    return urllib.request.urlopen(url, timeout=15).read().decode()


def dump(url, wait=12):
    return subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=12000", "--dump-dom", url],
        capture_output=True, timeout=wait + 20,
        encoding="utf-8", errors="replace").stdout or ""


print("== 资产与接口 ==")
ih = get("https://imyxj.xyz/")
ck("index 引用新版 main.js (1500380f)", "js/main.js?v=1500380f" in ih)
ck("index 引用新版 home.css", re.search(r"css/home\.css\?v=[0-9a-f]{8}", ih) is not None)
api = get("https://imyxj.xyz/api/page/about")
ck("page/about 含 honors", '"honors":[' in api)
api = get("https://imyxj.xyz/api/page/campus")
ck("page/campus 含 notes", '"notes":[' in api)
api = get("https://imyxj.xyz/api/page/contact")
ck("page/contact 含 friendlinks", '"friendlinks":[' in api)
ab = get("https://imyxj.xyz/about.html")
ck("about.html 有荣誉墙容器", 'id="honorWall"' in ab)
cb = get("https://imyxj.xyz/campus.html")
ck("campus.html 有随手记容器", 'id="noteWall"' in cb)
ct = get("https://imyxj.xyz/contact.html")
ck("contact.html 有友链容器", 'id="friendLinks"' in ct)

print("== Chrome 真实渲染(生产) ==")
d1 = dump("https://imyxj.xyz/about.html")
ck("about 渲染出荣誉卡片", "honor-card" in d1)
ck("about 渲染出等级徽章(校级)", "校级" in d1)
d2 = dump("https://imyxj.xyz/campus.html")
ck("campus 渲染出便签卡片", "note-card" in d2)
d3 = dump("https://imyxj.xyz/contact.html")
ck("contact 渲染出友链卡片", "friend-card" in d3)
d0 = dump("https://imyxj.xyz/")
ck("首页未受影响(hero 在)", "至尊杰" in d0)

print(f"\n通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
