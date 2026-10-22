#!/usr/bin/env python3
"""v2.0:7 页挂 PWA(manifest link + theme-color + SW 注册)(幂等)"""
import io
import os

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]

HEAD_TAGS = ('  <link rel="manifest" href="/manifest.json" />\n'
             '  <meta name="theme-color" content="#ff6b9d" />\n')
SW_REG = ('<script>\n'
          "  if ('serviceWorker' in navigator) {\n"
          "    window.addEventListener('load', function () {\n"
          "      navigator.serviceWorker.register('/sw.js').catch(function () {});\n"
          "    });\n"
          '  }\n'
          '</script>\n')

for p in PAGES:
    path = os.path.join(ROOT, p)
    with io.open(path, encoding="utf-8") as f:
        s = f.read()
    changed = []
    # 1) head 里加 manifest + theme-color(插在 </head> 前)
    if 'rel="manifest"' not in s:
        s = s.replace("</head>", HEAD_TAGS + "</head>", 1)
        changed.append("manifest")
    # 2) body 末尾 SW 注册(插在 </body> 前)
    if "serviceWorker.register" not in s:
        s = s.replace("</body>", SW_REG + "</body>", 1)
        changed.append("sw-reg")
    if changed:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
    print(f"OK   {p}: + {', '.join(changed)}" if changed else f"SKIP {p}")

print()
for p in PAGES:
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        s = f.read()
    ok = 'rel="manifest"' in s and "serviceWorker.register" in s
    print(f"  {'✓' if ok else '✗'} {p}")
