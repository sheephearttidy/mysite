#!/usr/bin/env python3
"""生产环境:多页拆分验证(6 页 + api/page + 导航高亮 + 主题)"""
import json
import re
import ssl
import sys
import urllib.request

B = "https://imyxj.xyz"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


def get(path):
    req = urllib.request.Request(B + path)
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    return r.status, r.read().decode("utf-8", "replace")


PAGES = {
    "index": ("", "首页"),
    "about": ("about.html", "关于我"),
    "skills": ("skills.html", "技能树"),
    "works": ("works.html", "小破项目"),
    "campus": ("campus.html", "校园日常"),
    "contact": ("contact.html", "来找我玩"),
}

# 1. 每页 200 + 结构
for name, (fn, active_label) in PAGES.items():
    url = "/" if fn == "" else "/" + fn
    st, body = get(url)
    ck(f"{name} 页 200", st == 200, str(st))
    ck(f"{name} data-page", f'data-page="{name}"' in body)
    ck(f"{name} 主题按钮", 'id="themeToggle"' in body)
    ck(f"{name} 防闪", "data-theme-source" in body)
    ck(f"{name} theme.js", "js/theme.js" in body)
    ck(f"{name} main.js", "js/main.js" in body)
    # 当前页高亮唯一
    active = re.findall(r'<a href="[^"]*" class="active">([^<]+)</a>', body)
    ck(f"{name} 当前页高亮", active == [active_label], str(active))
    # 导航无锚点
    anchors = re.findall(r'<li><a href="(#[^"]+)"', body)
    ck(f"{name} 无锚点导航", not anchors, str(anchors))

# 2. 关键容器
checks = [
    ("index", "class=\"stats\""),
    ("about", "id=\"aboutCard\""),
    ("about", "id=\"infoCards\""),
    ("skills", "class=\"skills-cols\""),
    ("works", "id=\"worksGrid\""),
    ("campus", "class=\"timeline\""),
    ("contact", "id=\"wechatBtn\""),
]
for page, frag in checks:
    fn = "" if page == "index" else page + ".html"
    _, body = get("/" + fn)
    ck(f"{page} 含 {frag}", frag in body)

# 3. api/page 接口
for page, field in [("index", "stats"), ("skills", "skills"), ("about", "profile"),
                    ("works", "works"), ("campus", "timeline")]:
    st, data = get(f"/api/page/{page}")
    d = json.loads(data)
    ck(f"api/page/{page} 200+字段", st == 200 and field in d and len(d[field]) > 0,
       f"{st} {str(d)[:80]}")

st, data = get("/api/page/contact")
d = json.loads(data) if data.strip() else None
ck("api/page/contact 空", st == 200 and d in ({}, None), f"{st} {str(d)[:40]}")

# 4. 静态资源
for u in ["/css/base.css", "/css/home.css", "/css/widgets.css", "/css/dark.css",
          "/css/responsive.css", "/js/main.js", "/js/theme.js"]:
    st, _ = get(u)
    ck(f"{u} 200", st == 200, str(st))

# 5. main.js 用分页接口
_, js = get("/js/main.js")
ck("main.js 用 /api/page/", "/api/page/" in js)
ck("main.js 无 /api/content", "/api/content" not in js)

# 6. 后台仍正常(登录页 200)
st, _ = get("/admin/login")
ck("登录页 200", st == 200, str(st))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
