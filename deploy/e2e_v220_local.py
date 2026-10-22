#!/usr/bin/env python3
"""E2E 本机端:通过 ssh 隧道访问测试服务器 5102,Chrome 渲染验证动态数据"""
import json
import re
import subprocess
import sys

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


def sh(cmd):
    return subprocess.run(["ssh", "root@SERVER_IP", cmd],
                          capture_output=True, timeout=60,
                          encoding="utf-8", errors="replace").stdout.strip()


def dump(url, wait=12):
    return subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=12000", "--dump-dom", url],
        capture_output=True, timeout=wait + 20,
        encoding="utf-8", errors="replace").stdout or ""


# 1. 服务器造数
r = sh("python3 /tmp/e2e_v220.py create")
j = json.loads(r)
ck("后台新增 E2E 荣誉", j.get("ok") and j.get("id"))
stamp, hid = j["stamp"], j["id"]

# 2. 隧道 + Chrome 渲染
tun = subprocess.Popen(
    ["ssh", "-N", "-L", "15102:127.0.0.1:5102", "root@SERVER_IP"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    import time
    time.sleep(3)
    dom = dump("http://127.0.0.1:15102/about.html")
    ck("前台渲染出 E2E 荣誉标题(动态数据入页)", stamp in dom)
    ck("荣誉带国家级徽章", "国家级" in dom)
    ck("荣誉 emoji 在", "🧪" in dom)
finally:
    tun.terminate()

# 3. 清理 + 复验
sh(f"python3 /tmp/e2e_v220.py clean {hid}")
tun = subprocess.Popen(
    ["ssh", "-N", "-L", "15102:127.0.0.1:5102", "root@SERVER_IP"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    import time
    time.sleep(3)
    dom2 = dump("http://127.0.0.1:15102/about.html")
    ck("删除后前台不再显示", stamp not in dom2)
finally:
    tun.terminate()

print(f"\n通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
