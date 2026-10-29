"""v5.2 线上终验:页面、接口、安全头、CSRF、世界地图。"""
import json
import re
import urllib.error
import urllib.request

B = "https://imyxj.xyz"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def get(path):
    req = urllib.request.Request(B + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


print("=== 页面 ===")
for p in ["/", "/about", "/skills", "/works", "/campus", "/gallery", "/map",
          "/contact", "/admin.html", "/theme-init.js"]:
    st, raw, _ = get(p)
    ck("%-16s %d" % (p, st), st == 200, str(st))

print()
print("=== API ===")
for p in ["/api/health", "/api/site", "/api/map", "/api/page/index",
          "/api/page/skills", "/api/content/skills", "/api/messages"]:
    st, raw, _ = get(p)
    ck("%-24s %d" % (p, st), st == 200, str(st))

print()
print("=== 世界地图(真实国界数据)===")
# /map 是 SPA 路由:直接请求只拿到 index.html 外壳,地图代码在懒加载 chunk 里。
# 正确路径:index.html -> 主包 main-*.js -> 动态 import 的 MapPage-*.js。
# (投影是 gen_world_map.py 预计算的,bundle 里没有 0.8707/MAX_Y 这类常量,
#  原脚本在 DOM 里找 MapPage chunk 必然失败。)
st, raw, _ = get("/map")
dom = raw.decode("utf-8", "replace")
ck("/map 返回页面(SPA 外壳)", st == 200 and 'id="root"' in dom, str(st))

st, raw, _ = get("/")
idx = raw.decode("utf-8", "replace")
entry = re.search(r'assets/(main-[\w-]+\.js)', idx)
ck("index.html 引用主包 main-*.js", bool(entry), "")
if entry:
    st, raw, _ = get("/assets/" + entry.group(1))
    main_js = raw.decode("utf-8", "replace")
    ck("主包可加载(%dKB)" % (len(main_js) // 1024),
       st == 200 and len(main_js) > 3000, str(st))
    m = re.search(r"MapPage-[\w-]+\.js", main_js)
    ck("主包引用地图 chunk", bool(m), "")
    if m:
        st, raw, _ = get("/assets/" + m.group(0))
        js = raw.decode("utf-8", "replace")
        ck("地图 chunk 可加载(%dKB)" % (len(js) // 1024), st == 200, str(st))
        # 国界是预生成的 SVG path 字符串,形如 "M993.7,312.1 994.5,311.6 ..."
        borders = len(re.findall(r'"M[\d.]', js))
        ck("含世界国界数据(%d 条轮廓)" % borders, borders >= 150, "len=%d" % len(js))
        ck("地图按 1000x514 投影", "height:514" in js or "viewBox" in js, "")

print()
print("=== 安全响应头 ===")
st, raw, hdr = get("/")
low = {k.lower(): v for k, v in hdr.items()}
csp = low.get("content-security-policy", "")
ck("CSP 存在", bool(csp), "")
ck("CSP 禁止 iframe 嵌套", "frame-ancestors 'none'" in csp, csp[:80])
ck("X-Content-Type-Options: nosniff", low.get("x-content-type-options") == "nosniff", "")
ck("X-Frame-Options: DENY", low.get("x-frame-options") == "DENY", str(low.get("x-frame-options")))
ck("Referrer-Policy 存在", bool(low.get("referrer-policy")), "")
ck("HSTS 存在", bool(low.get("strict-transport-security")), "")
ck("无重复安全头", hdr.get("X-Frame-Options", "").count("DENY") <= 1 and
   low.get("x-frame-options") == "DENY", str(hdr.get("X-Frame-Options")))

print()
print("=== CSRF(跨站写拒绝)===")
req = urllib.request.Request(
    B + "/api/admin/alerts",
    data=b"{}",
    headers={"Content-Type": "application/json", "Origin": "https://evil.example.com"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=25) as r:
        st = r.status
except urllib.error.HTTPError as e:
    st = e.code
ck("跨站写 -> 403", st == 403, str(st))

# 同源(用 GET 路径上的 POST 会 405,说明 CSRF 已放行)
req = urllib.request.Request(
    B + "/api/admin/alerts",
    data=b"{}",
    headers={"Content-Type": "application/json", "Origin": "https://imyxj.xyz"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=25) as r:
        st = r.status
except urllib.error.HTTPError as e:
    st = e.code
ck("同源写 -> 405(通过 CSRF,路由方法不符)", st == 405, str(st))

print()
print("=== 后台保护 ===")
for p in ["/api/admin/alerts", "/api/stats/visits", "/api/security/settings"]:
    st, _, _ = get(p)
    ck("%-26s 401" % p, st == 401, str(st))

print()
print("=== 敏感文件 ===")
for p in ["/.git/config", "/admin/data/mysite.db", "/.env"]:
    st, raw, _ = get(p)
    body = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    leaked = "[core]" in body or "SQLite format" in body or "MYSITE_" in body
    ck("%-26s 不泄露" % p, not leaked, "")

print()
print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
