"""测试环境:多页拆分回归(6 页 + api/page + 导航高亮 + 动态选择器)"""
import sys
import re
import urllib.request

BASE = "http://127.0.0.1:5102"
PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}  {extra}")


def get(path):
    r = urllib.request.urlopen(BASE + path, timeout=15)
    return r.status, r.read().decode("utf-8", "replace")


def get_status(path):
    """只拿状态码,404 也正常返回"""
    try:
        return urllib.request.urlopen(BASE + path, timeout=15).status
    except urllib.error.HTTPError as e:
        return e.code


PAGES = {
    "index": {"active": "首页", "nav": 7},
    "about": {"active": "关于我", "nav": 7},
    "skills": {"active": "技能树", "nav": 7},
    "works": {"active": "小破项目", "nav": 7},
    "campus": {"active": "校园日常", "nav": 7},
    "map": {"active": "来访地图", "nav": 7},
    "contact": {"active": "来找我玩", "nav": 7},
}

# 1. 每个页面结构完整
for name, spec in PAGES.items():
    st, body = get("/" + ("" if name == "index" else name + ".html"))
    check(f"{name} 页 200", st == 200, str(st))
    check(f"{name} data-page", f'data-page="{name}"' in body)
    check(f"{name} 含主题按钮", 'id="themeToggle"' in body)
    check(f"{name} 含防闪", "data-theme-source" in body)
    check(f"{name} 含双 meta", body.count('name="theme-color"') >= 2)
    check(f"{name} 含 footer", "<footer>" in body)
    check(f"{name} 含回顶", 'id="backTop"' in body)
    check(f"{name} 含二维码弹窗", 'id="qrOverlay"' in body)
    # 导航:6 个链接 + 当前页 active 且唯一
    nav_links = body.count('class="nav-links"')
    check(f"{name} 有导航", nav_links >= 1)
    import re
    active = re.findall(r'<a href="[^"]*" class="active">([^<]+)</a>', body)
    check(f"{name} 当前页高亮唯一", active == [spec["active"]], str(active))
    # 导航链接全部指向页面(非锚点)
    anchors = re.findall(r'<li><a href="(#[^"]+)"', body)
    check(f"{name} 无锚点导航", not anchors, str(anchors))

# 2. 页面关键容器(动态填充目标)
st, body = get("/index.html")
check("首页 stats 容器", 'class="stats"' in body)
st, body = get("/about.html")
check("about 卡片", 'id="aboutCard"' in body)
check("about 信息卡", 'id="infoCards"' in body)
st, body = get("/skills.html")
check("skills 双列", 'class="skills-cols"' in body)
st, body = get("/works.html")
check("works 网格", 'id="worksGrid"' in body)
st, body = get("/campus.html")
check("campus 时间线", 'class="timeline"' in body)
st, body = get("/contact.html")
check("contact 按钮", 'id="wechatBtn"' in body)

# 3. api/page 接口
import json
st, data = get("/api/page/index")
check("api/page/index 200", st == 200)
d = json.loads(data)
check("index 返回 stats", "stats" in d and len(d["stats"]) > 0)
check("index 无多余字段", set(d.keys()) == {"stats"}, str(d.keys()))

st, data = get("/api/page/skills")
d = json.loads(data)
check("skills 返回 skills", "skills" in d and len(d["skills"]) > 0)
check("skills 只返回 skills", set(d.keys()) == {"skills"}, str(d.keys()))

st, data = get("/api/page/about")
d = json.loads(data)
check("about 返回 profile", "profile" in d and len(d["profile"]) > 0)

st, data = get("/api/page/works")
d = json.loads(data)
check("works 返回 works", "works" in d and len(d["works"]) > 0)

st, data = get("/api/page/campus")
d = json.loads(data)
check("campus 返回 timeline", "timeline" in d and len(d["timeline"]) > 0)

st, data = get("/api/page/contact")
d = json.loads(data) if data.strip() else {}
# v2.2:contact 页新增友情链接,接口返回 friendlinks 列表
check("contact 返回友链", st == 200 and isinstance(d.get("friendlinks"), list)
      and len(d["friendlinks"]) > 0, str(d)[:120])

st = get_status("/api/page/unknown")
check("api/page/unknown 404", st == 404, str(st))

# 4. main.js 用分页接口
st, js = get("/js/main.js")
check("main.js 含 PAGE_API", "PAGE_API" in js)
check("main.js 用 /api/page/", "/api/page/" in js)
check("main.js 不再用 /api/content", "/api/content" not in js)

# 4.1 v2.1 拆分:core.js 公共核心存在且被页面引用
st, core = get("/js/core.js")
check("core.js 200 且含 observeReveals", st == 200 and "observeReveals" in core, str(st))
check("core.js 含 esc 工具", "const esc" in core)
st, ih = get("/")
check("index 引用 core.js 且先于 main.js",
      ih.index("js/core.js") < ih.index("js/main.js"))
check("index 引用 core.js 带版本", re.search(r"js/core\.js\?v=[0-9a-f]{8}", ih) is not None)

# 4.2 v2.1:项目封面底色键与 API 一致(颜色名,不再用数字)
check("main.js 项目封面用 wc- 键", "wc-${escAttr(w.cover)}" in js)
check("main.js 不再用 cover- 前缀", "cover-${escAttr(w.cover)}" not in js)

print()
print(f"通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
