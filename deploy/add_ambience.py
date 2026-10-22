#!/usr/bin/env python3
"""v1.9.1:7 页挂 ambience.js(幂等)"""
import io
import os

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]

TAG = '<script src="js/ambience.js"></script>\n'

for p in PAGES:
    path = os.path.join(ROOT, p)
    with io.open(path, encoding="utf-8") as f:
        s = f.read()
    if "js/ambience.js" in s:
        print(f"SKIP {p}")
        continue
    anchor = s.find('src="js/theme.js')
    if anchor < 0:
        print(f"SKIP {p}: no theme.js")
        continue
    line_end = s.find("\n", anchor)
    s = s[:line_end + 1] + TAG + s[line_end + 1:]
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print(f"OK   {p}")

print()
for p in PAGES:
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        ok = "js/ambience.js" in f.read()
    print(f"  {'✓' if ok else '✗'} {p}")
