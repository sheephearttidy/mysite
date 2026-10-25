#!/usr/bin/env python3
"""v1.10:7 页挂 site-extra.js(幂等)"""
import io
import os

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]

TAG = '<script src="js/site-extra.js"></script>\n'

for p in PAGES:
    path = os.path.join(ROOT, p)
    with io.open(path, encoding="utf-8") as f:
        s = f.read()
    if "js/site-extra.js" in s:
        print(f"SKIP {p}")
        continue
    anchor = s.find('src="js/ambience.js')
    if anchor < 0:
        print(f"SKIP {p}: no ambience.js anchor")
        continue
    line_end = s.find("\n", anchor)
    s = s[:line_end + 1] + TAG + s[line_end + 1:]
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print(f"OK   {p}")

print()
for p in PAGES:
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        ok = "js/site-extra.js" in f.read()
    print(f"  {'✓' if ok else '✗'} {p}")
