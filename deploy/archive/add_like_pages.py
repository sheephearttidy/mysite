#!/usr/bin/env python3
"""给其余 6 页加:点赞 section + interact.js 引用(幂等,可重复跑)"""
import io
import os

ROOT = r"D:\Agent_Work_Base\my-portfolio"
PAGES = ["about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]

LIKE_HTML = '''<!-- ================= 点赞 ================= -->
<section class="sec-cream" id="likebar">
  <div class="container" style="text-align:center">
    <button class="like-btn" id="likeBtn" aria-label="给这页点个赞">
      <span class="like-ico">❤️</span> <span class="like-n">–</span>
    </button>
    <p class="hint" style="margin-top:10px">喜欢这页就点个赞吧,每人每页只能点一次~</p>
  </div>
</section>

<footer>'''

OLD_FOOTER = "<footer>"
NEW_SCRIPT = '<script src="js/interact.js"></script>'

for p in PAGES:
    path = os.path.join(ROOT, p)
    with io.open(path, encoding="utf-8") as f:
        s = f.read()

    changed = []
    # 1) footer 前插点赞区(只插一次)
    if 'id="likebar"' not in s:
        # 第一个 <footer> 前
        idx = s.find(OLD_FOOTER)
        if idx < 0:
            print(f"SKIP {p}: 没有 footer")
            continue
        s = s[:idx] + LIKE_HTML + s[idx + len(OLD_FOOTER):]
        changed.append("likebar")

    # 2) main.js 后加 interact.js
    if 'js/interact.js' not in s:
        anchor = s.find('src="js/main.js')
        if anchor < 0:
            print(f"SKIP {p}: 没有 main.js")
            continue
        line_end = s.find("\n", anchor)
        s = s[:line_end + 1] + NEW_SCRIPT + "\n" + s[line_end + 1:]
        changed.append("interact.js")

    if changed:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
        print(f"OK   {p}: + {', '.join(changed)}")
    else:
        print(f"SKIP {p}: 已有")

# 验证
print()
for p in PAGES:
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        s = f.read()
    ok1 = 'id="likebar"' in s
    ok2 = 'js/interact.js' in s
    print(f"  {'✓' if ok1 and ok2 else '✗'} {p}  likebar={ok1} interact={ok2}")
