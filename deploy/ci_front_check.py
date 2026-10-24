#!/usr/bin/env python3
"""CI 用:前台 Jinja 模板与本地资源一致性检查(不依赖 Flask)
1. 7 个页面模板继承公共布局,导航在共享模板中维护
2. 模板引用的本地 js/css 文件都存在
3. 带 ?v= 的哈希与文件实际 sha256[:8] 一致
"""
import io
import os
import re
import hashlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE_NAMES = ["index", "about", "skills", "works", "campus", "map", "contact"]
PAGES = [os.path.join("templates", "front", f"{name}.html") for name in PAGE_NAMES]
SHARED = [os.path.join("templates", "front", name) for name in
          ("base.html", "_nav.html", "_footer.html")]
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
ck("公共模板文件存在", all(os.path.exists(os.path.join(ROOT, p)) for p in SHARED),
   str([p for p in SHARED if not os.path.exists(os.path.join(ROOT, p))]))

nav_re = re.compile(r'class="nav-links".*?</nav>', re.S)
link_re = re.compile(r'href="/([a-z]+)\.html"')

nav_path = os.path.join(ROOT, "templates", "front", "_nav.html")
nav_text = io.open(nav_path, encoding="utf-8").read() if os.path.exists(nav_path) else ""
nav_match = nav_re.search(nav_text)
nav_links = sorted(link_re.findall(nav_match.group(0))) if nav_match else []
ck("共享导航包含 6 个子页面链接", len(nav_links) == 6, str(nav_links))
ck("每页都继承公共布局", all("extends 'front/base.html'" in io.open(p, encoding="utf-8").read()
                               for p in pages_abs if os.path.exists(p)))

# 资源引用存在 + 哈希一致
ref_re = re.compile(r'(?:src|href)="/?((?:js|css)/[^"?]+)(?:\?v=([a-f0-9]{8}))?"')
bad_missing, bad_hash, nover = [], [], []
template_files = [os.path.join(ROOT, p) for p in PAGES + SHARED]
for p, ab in zip(PAGES + SHARED, template_files):
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
