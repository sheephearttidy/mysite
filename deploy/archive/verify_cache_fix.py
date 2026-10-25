#!/usr/bin/env python3
"""生产验证:资源版本参数 + 手动特效链路"""
import json
import re
import sys
import urllib.request

BASE = "https://imyxj.xyz"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


def get(p):
    r = urllib.request.urlopen(BASE + p, timeout=20)
    return r.status, r.read().decode("utf-8", "replace")


PAGES = ["/", "/about.html", "/skills.html", "/works.html",
         "/campus.html", "/map.html", "/contact.html"]

print("=== 1. 每个页面资源都带版本参数 ===")
for p in PAGES:
    st, html = get(p)
    refs = re.findall(r'(?:src|href)="((?:js|css)/[^"]+)"', html)
    no_ver = [r for r in refs if "?v=" not in r]
    ck(f"{p} 全部带版本 ({len(refs)} 个资源)", not no_ver,
       f"缺: {no_ver}")

print()
print("=== 2. 带版本号能真的拿到新文件(绕过缓存) ===")
st, html = get("/")
m = re.search(r'js/holiday\.js\?v=([a-f0-9]+)', html)
ck("index 里 holiday.js 有 hash", bool(m), str(m.group(0) if m else "无"))
if m:
    st, js = get(f"/js/holiday.js?v={m.group(1)}")
    ck("带 hash 的 URL 返回 200", st == 200, str(st))
    ck("拿到的是新版(含 /api/fx)", "/api/fx" in js)
    ck("含 manual 分支", "manual" in js)

print()
print("=== 3. /api/fx 公开可读 ===")
st, raw = get("/api/fx")
d = json.loads(raw)
ck("/api/fx 200", st == 200, str(st))
ck("有 mode/key/effects", all(k in d for k in ("mode", "key", "effects")), str(d))

print()
print("=== 4. 前台页面引用的 JS 实际内容是新版 ===")
for name in ("holiday.js", "holiday-fx.js"):
    st, html2 = get("/")
    mm = re.search(rf'js/{re.escape(name)}\?v=([a-f0-9]+)', html2)
    if not mm:
        ck(f"{name} 有版本参数", False)
        continue
    st, js = get(f"/js/{name}?v={mm.group(1)}")
    ck(f"{name} 200", st == 200, str(st))
    if name == "holiday-fx.js":
        ck("holiday-fx 读 data-holiday", "data-holiday" in js)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
