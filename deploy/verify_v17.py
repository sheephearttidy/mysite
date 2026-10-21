#!/usr/bin/env python3
"""生产环境:v1.7.0 验证(map 页 + 节日 + api/map + 原有全站)"""
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


# 1. 全部 7 个页面
PAGES = {
    "index": ("", "首页"),
    "about": ("about.html", "关于我"),
    "skills": ("skills.html", "技能树"),
    "works": ("works.html", "小破项目"),
    "campus": ("campus.html", "校园日常"),
    "map": ("map.html", "来访地图"),
    "contact": ("contact.html", "来找我玩"),
}
for name, (fn, active_label) in PAGES.items():
    url = "/" if fn == "" else "/" + fn
    st, body = get(url)
    ck(f"{name} 页 200", st == 200, str(st))
    ck(f"{name} data-page", f'data-page="{name}"' in body)
    active = re.findall(r'<a href="[^"]*" class="active">([^<]+)</a>', body)
    ck(f"{name} 当前页高亮", active == [active_label], str(active))

# 2. 节日接入
for name, fn in [("index", ""), ("about", "about.html"), ("map", "map.html")]:
    url = "/" if fn == "" else "/" + fn
    _, body = get(url)
    ck(f"{name} 含 holidays.css", "css/holidays.css" in body)
    ck(f"{name} 含 holiday.js", "js/holiday.js" in body)
    ck(f"{name} 含 holiday-fx.js", "js/holiday-fx.js" in body)

# 3. 新资源
for u in ["/map.html", "/css/holidays.css", "/js/holiday.js", "/js/holiday-fx.js",
          "/js/cities.js", "/js/map.js"]:
    st, _ = get(u)
    ck(f"{u} 200", st == 200, str(st))

# 4. /api/map
st, data = get("/api/map")
d = json.loads(data)
ck("api/map 200", st == 200)
ck("api/map 含 cities 数组", "cities" in d and isinstance(d["cities"], list), str(d)[:80])

# 5. 旧接口不回归
st, data = get("/api/page/index")
d = json.loads(data)
ck("api/page/index 正常", st == 200 and "stats" in d)

# 6. 后台登录页 200
st, _ = get("/admin/login")
ck("登录页 200", st == 200, str(st))

# 7. track 接受 map 页路径(不真发,只验证路径白名单逻辑在生产同样)
# 用 sendBeacon 相同 payload 的 POST——会真记录,但无害
import urllib.parse
try:
    req = urllib.request.Request(
        B + "/api/track",
        data=b'{"path": "/map.html"}',
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/130",
                 "X-Forwarded-For": "114.114.114.114"})
    r = urllib.request.urlopen(req, timeout=10, context=ctx)
    j = json.loads(r.read().decode())
    ck("track 接受 /map.html", j.get("ok") is True, str(j)[:80])
except Exception as e:
    ck("track 接受 /map.html", False, str(e)[:120])

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
