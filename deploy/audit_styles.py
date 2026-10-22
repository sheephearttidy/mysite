#!/usr/bin/env python3
"""全站样式审查:前台 HTML 用到的 class 是否都有 CSS 定义(含 JS 动态类)
输出:未定义类清单(疑似不生效样式)
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]
CSS_FILES = ["css/base.css", "css/home.css", "css/widgets.css",
             "css/dark.css", "css/holidays.css", "css/responsive.css"]
JS_FILES = ["js/main.js", "js/interact.js", "js/ambience.js",
            "js/site-extra.js", "js/theme.js", "js/holiday.js", "js/holiday-fx.js"]

# 1) 收集前台 CSS 里定义的所有类名
css_text = ""
for c in CSS_FILES:
    p = os.path.join(ROOT, c)
    if os.path.exists(p):
        css_text += io.open(p, encoding="utf-8").read() + "\n"
defined = set(re.findall(r"\.([A-Za-z_][\w-]*)", css_text))

# 2) JS 里动态添加的类也算已定义引用(单独列出,它们不一定需要 CSS)
js_text = ""
for j in JS_FILES:
    p = os.path.join(ROOT, j)
    if os.path.exists(p):
        js_text += io.open(p, encoding="utf-8").read() + "\n"
js_classes = set()
for m in re.finditer(r"""className\s*=\s*['"]([^'"]+)['"]""", js_text):
    js_classes.update(m.group(1).split())
for m in re.finditer(r"""classList\.(?:add|toggle)\(\s*['"]([^'"]+)['"]""", js_text):
    js_classes.add(m.group(1))
# 拼接表达式如 'msg-note msg-' + color:抓字符串片段里的前缀,去掉结尾残词
js_classes = {c for c in js_classes if not c.endswith("-")}

# 3) HTML 里用到的类
used = {}          # cls -> [page,...]
inline_els = 0
for p in PAGES:
    fp = os.path.join(ROOT, p)
    if not os.path.exists(fp):
        continue
    s = io.open(fp, encoding="utf-8").read()
    # 去掉内联 script/style 再抓 class
    body = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    inline_els += len(re.findall(r"<style", s))
    for m in re.finditer(r'class="([^"]+)"', body):
        for cls in m.group(1).split():
            used.setdefault(cls, []).append(p)

# 4) JS 动态类也在 HTML 里出现的合并进 used
for cls in js_classes:
    used.setdefault(cls, [])

# 5) 找未定义的
missing = sorted(c for c in used if c not in defined)
known_ok = []   # JS 动态类但 CSS 有定义
print(f"前台 CSS 定义类总数: {len(defined)}")
print(f"HTML+JS 用到类总数: {len(used)}")
print(f"内联 <style> 块: {inline_els}")
print()
print("=== HTML/JS 用到但前台 CSS 未定义的类 ===")
for c in missing:
    pages = used.get(c) or ["(仅 JS 动态)"]
    # JS 动态类若 CSS 也没有,标为真问题
    src = "JS" if not pages or pages == ["(仅 JS 动态)"] else "HTML"
    print(f"  [{src}] .{c}   <- {','.join(pages[:3])}")
print()
print("=== JS 动态类且 CSS 也未定义(潜在无样式) ===")
for c in sorted(js_classes):
    if c not in defined:
        print(f"  .{c}")
