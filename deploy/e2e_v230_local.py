#!/usr/bin/env python3
"""v2.3 Chrome 本机验证:走 ssh 隧道 15102,确认后台 JS 真渲染+CSP 不挡"""
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:15102"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    PASS, FAIL = PASS + (1 if cond else 0), FAIL + (0 if cond else 1)


def dump(url):
    r = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=12000", "--dump-dom", url],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60)
    return r.stdout


def reach():
    try:
        urllib.request.urlopen(BASE + "/admin/login", timeout=4)
        return True
    except Exception:
        return False


if not reach():
    print("隧道 15102 不通,先开: ssh -N -L 15102:127.0.0.1:5102 root@SERVER_IP")
    sys.exit(2)

# 1) 登录页:防闪段 + 表单都在(CSP nonce 生效,样式脚本没被拦)
h = dump(BASE + "/admin/login")
ck("登录页 title", "<title>" in h and "登录" in h)
ck("防闪内联脚本在 DOM", "尽早应用主题" in h)
ck("验证码图节点", "captcha.svg" in h)
ck("表单密码框", 'type="password"' in h)

# 2) 后台页需要登录,未登录应重定向到登录页(不白屏/不 CSP 崩)
h2 = dump(BASE + "/admin/")
ck("/admin 未登录跳登录页(非白屏)", "captcha.svg" in h2 or "登录" in h2)

print(f"\nChrome 验证: 通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
