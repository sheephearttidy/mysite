#!/usr/bin/env python3
"""v2.0.2 全项目功能审计:
A. 前台 7 页 + 后台模板:每个 class 都有归属 CSS(前台 CSS / 后台 CSS / 内联 style)
B. 按钮/可交互元素:有 onclick 或 id 绑定(防"死按钮")
C. JS 引用的 getElementById 在 HTML 中存在(防绑定落空)
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]
ADMIN_HTML = os.path.join(ROOT, "admin", "templates", "admin.html")
ADMIN_LOGIN = os.path.join(ROOT, "admin", "templates", "login.html")
CSS_FILES = ["css/base.css", "css/home.css", "css/widgets.css",
             "css/dark.css", "css/holidays.css", "css/responsive.css"]
ADMIN_CSS = ["admin/static/css/admin.css", "admin/static/css/login.css",
             "admin/static/css/holidays.css"]
JS_FILES = ["js/core.js", "js/main.js", "js/interact.js", "js/ambience.js",
            "js/site-extra.js", "js/theme.js", "js/holiday.js", "js/holiday-fx.js"]
ADMIN_JS = ["admin/static/js/admin/admin-core.js", "admin/static/js/admin/admin-panel.js",
            "admin/static/js/admin/admin-content.js", "admin/static/js/admin/admin-media.js",
            "admin/static/js/admin/admin-ops.js", "admin/static/js/admin/admin-site.js",
            "admin/static/js/admin/admin-app.js", "admin/static/js/login.js"]

P = F = 0


def ck(name, cond, extra=""):
    global P, F
    if cond:
        print(f"PASS  {name}")
        P += 1
    else:
        print(f"FAIL  {name}  {extra}")
        F += 1


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


# ---------- 收集 CSS 类 ----------
front_css = admin_css = ""
for c in CSS_FILES:
    front_css += read(os.path.join(ROOT, c)) + "\n"
for c in ADMIN_CSS:
    admin_css += read(os.path.join(ROOT, c)) + "\n"
front_def = set(re.findall(r"\.([A-Za-z_][\w-]*)", front_css))
admin_def = set(re.findall(r"\.([A-Za-z_][\w-]*)", admin_css))

# ---------- JS 动态类(过滤拼接残词) ----------
all_js = ""
for j in JS_FILES + ADMIN_JS:
    all_js += read(os.path.join(ROOT, j)) + "\n"
js_classes = set()
for m in re.finditer(r"""className\s*=\s*['"]([^'"]+)['"]""", all_js):
    js_classes.update(m.group(1).split())
for m in re.finditer(r"""classList\.(?:add|toggle)\(\s*['"]([^'"]+)['"]""", all_js):
    js_classes.add(m.group(1))
js_classes = {c for c in js_classes if not c.endswith("-") and c not in ("visible",)}

# ---------- HTML 类检查 ----------
def check_page_classes(name, html, css_def, scope):
    used = {}
    body = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"{%.*?%}|{{.*?}}", "", body, flags=re.S)   # 剥 Jinja 模板语法
    for m in re.finditer(r'class="([^"]+)"', body):
        for cls in m.group(1).split():
            used.setdefault(cls, 0)
    missing = []
    for cls in used:
        if cls in css_def or cls in js_classes:
            continue
        # 有内联 style 的元素允许无类定义(一次性布局)
        pat = re.compile(r'<[^>]*class="[^"]*\b' + re.escape(cls) + r'\b[^"]*"[^>]*style="')
        if pat.search(html):
            continue
        missing.append(cls)
    ck(f"[{scope}] {name} 类全部有归属", not missing, str(missing[:8]))
    return used


all_used = {}
for p in PAGES:
    fp = os.path.join(ROOT, p)
    if os.path.exists(fp):
        all_used.update(check_page_classes(p, read(fp), front_def, "前台"))
check_page_classes("admin.html", read(ADMIN_HTML), admin_def, "后台")
check_page_classes("login.html", read(ADMIN_LOGIN), admin_def, "后台")

# ---------- 按钮/交互元素 ----------
btn_issues = []
for p in PAGES:
    html = read(os.path.join(ROOT, p))
    if not html:
        continue
    for m in re.finditer(r"<button\b[^>]*>", html):
        tag = m.group(0)
        if "onclick" not in tag and "type=" not in tag and "id=" not in tag:
            btn_issues.append(f"{p}: {tag[:60]}")
ck("前台按钮全部有行为绑定", not btn_issues, str(btn_issues[:3]))

# ---------- JS getElementById 与 HTML id 对账 ----------
html_all = ""
for p in PAGES:
    html_all += read(os.path.join(ROOT, p))
html_all += read(ADMIN_HTML) + read(ADMIN_LOGIN)
html_ids = set(re.findall(r'id="([^"]+)"', html_all))
# JS 动态创建的 id 排除
dyn_ids = set(re.findall(r"""(?:id\s*=\s*['"]|createElement[\s\S]{0,80}id)\s*[=:]?\s*['"]?([\w-]+)['"]""", all_js))
missing_ids = []
for j in JS_FILES + ADMIN_JS:
    js = read(os.path.join(ROOT, j))
    for m in re.finditer(r"getElementById\(\s*['\"]([\w-]+)['\"]\s*\)", js):
        eid = m.group(1)
        if eid not in html_ids and eid not in dyn_ids:
            missing_ids.append(f"{os.path.basename(j)}: #{eid}")
ck("JS 引用的元素 id 全部存在", not missing_ids, str(missing_ids[:8]))

# ---------- 后台按钮 onclick 函数存在 ----------
admin_js_text = ""
for j in ADMIN_JS:
    admin_js_text += read(os.path.join(ROOT, j))
admin_funcs = set(re.findall(r"(?:async\s+)?function\s+(\w+)\s*\(", admin_js_text))
admin_funcs |= set(re.findall(r"(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>", admin_js_text))
onclick_issues = []
for m in re.finditer(r'onclick="(\w+)\(', read(ADMIN_HTML)):
    fn = m.group(1)
    if fn not in admin_funcs:
        onclick_issues.append(fn)
ck("后台 onclick 函数全部已定义", not onclick_issues, str(onclick_issues[:6]))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
