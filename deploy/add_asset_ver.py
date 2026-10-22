#!/usr/bin/env python3
"""给前台 7 个页面的 js/css 引用加内容哈希版本参数 ?v=xxxx
文件内容变了 hash 就变,URL 就变,自动绕过浏览器/nginx 缓存。
"""
import hashlib
import io
import os
import re

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]

# 先算每个资源文件的内容哈希(8 位)
hashes = {}
for sub in ("css", "js"):
    d = os.path.join(ROOT, sub)
    for fn in os.listdir(d):
        if fn.endswith((".css", ".js")):
            p = os.path.join(d, fn)
            with open(p, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()[:8]
            hashes[f"{sub}/{fn}"] = h

print(f"算出 {len(hashes)} 个资源哈希")
for k in sorted(hashes):
    print(f"  {k:22s} {hashes[k]}")

print()
changed = 0
for page in PAGES:
    path = os.path.join(ROOT, page)
    with io.open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html

    def repl(m):
        attr, url = m.group(1), m.group(2)
        base = url.split("?")[0]
        h = hashes.get(base)
        if not h:
            return m.group(0)
        return f'{attr}="{base}?v={h}"'

    html = re.sub(r'(src|href)="((?:js|css)/[^"?]+)(?:\?[^"]*)?"', repl, html)

    if html != orig:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        changed += 1
        print(f"OK {page} 已加版本参数")

print()
print(f"共修改 {changed} 个页面")

# 验证
print("\n=== 验证 index.html ===")
with io.open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
    h = f.read()
for r in re.findall(r'(?:src|href)="((?:js|css)/[^"]+)"', h):
    print(f"  {'✓' if '?v=' in r else '✗'} {r}")
