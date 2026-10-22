#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chrome 真机验证 about 页「最近在听」区块:卡片渲染 + iframe src 正确 + 无 CSP 违规"""
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:15102"
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


r = subprocess.run(
    [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
     "--headless=new", "--disable-gpu", "--no-sandbox",
     "--virtual-time-budget=20000", "--dump-dom", BASE + "/about.html"],
    capture_output=True, encoding="utf-8", errors="replace", timeout=180)
dom = r.stdout
err = r.stderr

print("=" * 60)
print("Chrome 真机验证:about 页「最近在听」")
print("=" * 60)

ck("页面加载出 DOM", len(dom) > 5000, f"len={len(dom)}")
ck("有「最近在听」标题", "最近在听" in dom)

# 卡片
cards = dom.count('class="music-card')
ck("渲染出音乐卡片", cards >= 1, f"cards={cards}")

# iframe
iframes = re.findall(r'<iframe[^>]*class="music-frame"[^>]*>', dom)
ck("有 music-frame iframe", len(iframes) >= 1, f"found={len(iframes)}")
if iframes:
    src = re.search(r'src="([^"]+)"', iframes[0])
    s = src.group(1) if src else ""
    print(f"  iframe src = {s}")
    ck("iframe 指向官方播放器", "i.y.qq.com/n2/m/outchain/player/index.html" in s, s)
    ck("iframe 带数字 songid", bool(re.search(r"songid=\d+", s)), s)

# 歌曲信息
ck("显示歌名(晴天)", "晴天" in dom)
ck("显示歌手(周杰伦)", "周杰伦" in dom)
ck("有 VIP 试听提示", "试听" in dom or "60 秒" in dom)

# CSP 违规
viol = [l for l in err.splitlines()
        if "Content Security Policy" in l or "Refused to" in l]
ck("无 CSP 拦截报告", not viol, str(viol[:3]))

# 前台其它区块仍在
ck("荣誉墙仍渲染", dom.count('class="honor-card') >= 1, f"{dom.count('class=\"honor-card')}")
ck("自我介绍仍渲染", "是谁" in dom or "在干嘛" in dom)

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
if FAILS:
    for f in FAILS:
        print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
