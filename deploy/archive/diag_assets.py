#!/usr/bin/env python3
"""检查前台页面里的 js/css 引用(看有没有版本参数)"""
import io
import re

PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]
ROOT = "/var/www/mysite/"

for p in PAGES:
    with io.open(ROOT + p, encoding="utf-8") as f:
        html = f.read()
    refs = re.findall(r'(?:src|href)="((?:js|css)/[^"]+)"', html)
    print(f"--- {p} ({len(refs)} 个资源) ---")
    for r in refs:
        has_v = "?v=" in r
        print(f"   {'✓带版本' if has_v else '✗无版本'} {r}")
    print()
