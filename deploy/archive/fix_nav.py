#!/usr/bin/env python3
"""补齐导航:给 6 个旧页面在「校园日常」与「来找我玩」之间插入「来访地图」
map.html 已有该链接,跳过。
"""
import os

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "contact.html"]

OLD = '      <li><a href="/campus.html">校园日常</a></li>\n' \
      '      <li><a href="/contact.html">来找我玩</a></li>'
NEW = '      <li><a href="/campus.html">校园日常</a></li>\n' \
      '      <li><a href="/map.html">来访地图</a></li>\n' \
      '      <li><a href="/contact.html">来找我玩</a></li>'

for fn in PAGES:
    path = os.path.join(ROOT, fn)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    if NEW in html:
        print(f"SKIP {fn} 已有来访地图")
        continue
    if OLD not in html:
        print(f"WARN {fn} 未找到导航锚点")
        continue
    html = html.replace(OLD, NEW, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"OK {fn} 已插入来访地图")
