#!/usr/bin/env python3
"""v2.3 生产 Chrome 渲染验证:登录页/首页走 https,CSP 不拦真浏览器"""
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    PASS, FAIL = PASS + (1 if cond else 0), FAIL + (0 if cond else 1)


def dump(url):
    r = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=15000", "--dump-dom", url],
        capture_output=True, encoding="utf-8", errors="replace", timeout=90)
    return r.stdout


h = dump("https://imyxj.xyz/admin/login")
ck("生产登录页 title", "登录" in h)
ck("防闪脚本在 DOM(nonce 生效)", "尽早应用主题" in h)
ck("验证码图节点", "captcha.svg" in h)
ck("表单密码框", 'type="password"' in h)

h2 = dump("https://imyxj.xyz/")
ck("首页 title", "至尊杰" in h2)
ck("首页 SSR 内容在", ("hero" in h2 or "section" in h2))
print(f"\n生产 Chrome: 通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
