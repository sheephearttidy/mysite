#!/usr/bin/env python3
"""给前台 7 个页面的 js/css 引用加内容哈希版本参数 ?v=xxxx
文件内容变了 hash 就变,URL 就变,自动绕过浏览器/nginx 缓存。
"""
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 引用了本地 js/css 的模板都要列进来(v3.1.0:contact.html 带 doodle.js)
PAGES = [os.path.join("templates", "front", "base.html"),
         os.path.join("templates", "front", "map.html"),
         os.path.join("templates", "front", "contact.html")]

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

# v2.1:后台静态主题副本同步(单一真源=前台),再算一次副本哈希保证一致
sync = os.path.join(ROOT, "deploy", "sync_admin_theme.py")
if os.path.exists(sync):
    import subprocess
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, sync, "--fix"],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    print((r.stdout or "").strip())
    if r.returncode != 0:
        print(r.stderr)

print()
changed = 0
for page in PAGES:
    path = os.path.join(ROOT, page)
    with io.open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html

    def repl(m):
        attr, url = m.group(1), m.group(2)
        prefix = "/" if url.startswith("/") else ""
        base = url.lstrip("/").split("?")[0]
        h = hashes.get(base)
        if not h:
            return m.group(0)
        return f'{attr}="{prefix}{base}?v={h}"'

    html = re.sub(r'(src|href)="(/?(?:js|css)/[^"?]+)(?:\?[^"]*)?"', repl, html)

    if html != orig:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        changed += 1
        print(f"OK {page} 已加版本参数")

print()
print(f"共修改 {changed} 个页面")

# 验证
print("\n=== 验证公共模板 ===")
with io.open(os.path.join(ROOT, "templates", "front", "base.html"), encoding="utf-8") as f:
    h = f.read()
for r in re.findall(r'(?:src|href)="/?((?:js|css)/[^"]+)"', h):
    print(f"  {'✓' if '?v=' in r else '✗'} {r}")
