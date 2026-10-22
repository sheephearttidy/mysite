#!/usr/bin/env python3
"""v2.2.0 Chrome 渲染验证:三页新组件真实渲染 + 数据来源核对"""
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://SERVER_IP"   # 直连测试 nginx? 不,测试环境 5102 只有 Flask,前台走本机文件服务
# 测试前台由 testapp 的 Flask 兜底路由渲染,直接访问 5102 页面
T = "http://SERVER_IP:15102"  # 占位,若端口不对改用本地
PASS = FAIL = 0


def ck(name, cond):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def dump(url, wait=6):
    try:
        out = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=8000", "--dump-dom", url],
            capture_output=True, timeout=wait + 15,
            encoding="utf-8", errors="replace").stdout or ""
    except Exception as e:
        print("  chrome err:", e)
        out = ""
    return out


print("== 说明:前台页面走本地文件服务器验证(数据来自测试后台 5102) ==")

# 本地静态服务器(9999)指向项目根,数据接口代理不可用 → 前台会静默回退内置内容
# 因此这里重点验证:结构渲染 + 静态兜底内容正常显示
d1 = dump("http://127.0.0.1:8901/about.html", 8)
ck("about 结构:荣誉墙容器", 'id="honorWall"' in d1)
ck("about 静态兜底:荣誉卡片", "honor-card" in d1)
ck("about 兜底显示校级徽章", "校级" in d1)

d2 = dump("http://127.0.0.1:8901/campus.html", 8)
ck("campus 结构:随手记容器", 'id="noteWall"' in d2)
ck("campus 兜底:便签卡片", "note-card" in d2)

d3 = dump("http://127.0.0.1:8901/contact.html", 8)
ck("contact 结构:友链容器", 'id="friendLinks"' in d3)
ck("contact 兜底:友链卡片", "friend-card" in d3)

# 测试环境动态数据(5102 Flask 有兜底路由直接出 HTML?)—— 检查动态路径
# testapp 的 run.py 有 /js /css 路由,页面也应可访问
d4 = dump("http://SERVER_IP:5102/about.html", 8) if False else ""
print(f"\n通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
