#!/usr/bin/env python3
"""CI 用:前端一致性检查(不依赖 Flask,纯文件级)
1. 7 个页面都存在,导航 7 链接一致
2. 每个 html 引用的本地 js/css 文件都存在
3. 带 ?v= 的哈希与文件实际 sha256[:8] 一致(防改了文件忘了重算)
"""
import io
import os
import re
import hashlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]
P = F = 0


def ck(name, cond, extra=""):
    global P, F
    if cond:
        print(f"PASS  {name}")
        P += 1
    else:
        print(f"FAIL  {name}  {extra}")
        F += 1


def sha8(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]


pages_abs = [os.path.join(ROOT, p) for p in PAGES]
ck("7 个页面文件存在", all(os.path.exists(p) for p in pages_abs),
   str([p for p in pages_abs if not os.path.exists(p)]))

nav_re = re.compile(r'class="nav-links".*?</nav>', re.S)
link_re = re.compile(r'href="/([a-z]+)\.html"')

navs = []
for p, ab in zip(PAGES, pages_abs):
    if not os.path.exists(ab):
        continue
    with io.open(ab, encoding="utf-8") as f:
        s = f.read()
    m = nav_re.search(s)
    navs.append((p, sorted(link_re.findall(m.group(0))) if m else None))

first = navs[0][1]
ck("每页导航都能解析", all(n for _, n in navs))
ck("导航 7 链接一致", all(n == first for _, n in navs),
   str([(p, n) for p, n in navs if n != first]))

# 资源引用存在 + 哈希一致
ref_re = re.compile(r'(?:src|href)="((?:js|css)/[^"?]+)(?:\?v=([a-f0-9]{8}))?"')
bad_missing, bad_hash, nover = [], [], []
for p, ab in zip(PAGES, pages_abs):
    if not os.path.exists(ab):
        continue
    with io.open(ab, encoding="utf-8") as f:
        s = f.read()
    for path, ver in ref_re.findall(s):
        fp = os.path.join(ROOT, path)
        if not os.path.exists(fp):
            bad_missing.append(f"{p}:{path}")
            continue
        if ver and sha8(fp) != ver:
            bad_hash.append(f"{p}:{path}(页面={ver} 实际={sha8(fp)})")
        if not ver:
            nover.append(f"{p}:{path}")

ck("引用的本地资源都存在", not bad_missing, str(bad_missing[:5]))
ck("版本哈希与文件一致", not bad_hash, str(bad_hash[:5]))
ck("本地资源全部带版本参数", not nover, str(nover[:5]))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
