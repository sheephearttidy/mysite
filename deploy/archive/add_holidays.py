#!/usr/bin/env python3
"""批量把节日特效接入前台页面:
- head: <script src="js/holiday.js"></script> 加在防闪脚本 </script> 之后
- CSS: holidays.css 加在 dark.css 之后, responsive.css 之前
- body 末尾: <script src="js/holiday-fx.js"></script>
"""
import os
import re

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "contact.html", "map.html"]

CSS_BLOCK = ('<link rel="stylesheet" href="css/dark.css" />\n'
             '<link rel="stylesheet" href="css/holidays.css" />\n'
             '<link rel="stylesheet" href="css/responsive.css" />')

HOLIDAY_JS = '  <script src="js/holiday.js"></script>'

FX_JS = '<script src="js/holiday-fx.js"></script>'

for fn in PAGES:
    path = os.path.join(ROOT, fn)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html
    n = 0

    # 1. CSS 顺序插入 holidays.css
    pat = re.compile(r'<link rel="stylesheet" href="css/dark\.css" />\s*'
                     r'<link rel="stylesheet" href="css/responsive\.css" />')
    if pat.search(html):
        html = pat.sub(CSS_BLOCK, html, count=1)
        n += 1
    else:
        print(f"WARN {fn}: 未找到 dark.css+responsive.css 序列")

    # 2. holiday.js 加在防闪脚本后(匹配最后一个 </script> 在 </head> 前)
    pat2 = re.compile(r'  \}\)\(\);\n</script>\n</head>')
    if pat2.search(html):
        html = pat2.sub(f'  }})();\n</script>\n{HOLIDAY_JS}\n</head>', html, count=1)
        n += 1
    else:
        print(f"WARN {fn}: 未找到防闪脚本尾部")

    # 3. holiday-fx.js 加在 </body> 前
    pat3 = re.compile(r'</body>')
    if pat3.search(html):
        html = pat3.sub(f'{FX_JS}\n</body>', html, count=1)
        n += 1
    else:
        print(f"WARN {fn}: 未找到 </body>")

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"OK {fn} ({n} 处)")
    else:
        print(f"SKIP {fn} 无变化")
