#!/usr/bin/env python3
"""生产验证:样式拆分"""
import os
import re
import sys
import requests

B = "https://imyxj.xyz"
PWD = os.environ.get("TEST_PWD", "")
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n} {e}")
        F += 1


print("=" * 52)
print("组 1:前台 CSS 拆分")
print("=" * 52)
r = requests.get(B + "/", timeout=20)
fh = r.text
ck("首页 200", r.status_code == 200)
ck("不再引用 style.css", "css/style.css" not in fh)
ck("style.css 已 404",
   requests.get(B + "/css/style.css", timeout=15).status_code == 404)
for f in ["base.css", "home.css", "widgets.css", "dark.css", "responsive.css"]:
    rr = requests.get(f"{B}/css/{f}", timeout=15)
    ck(f"{f} 200 且非空", rr.status_code == 200 and len(rr.text) > 300,
       f"{rr.status_code}, {len(rr.text)} 字节")
    ck(f"index 引用 {f}", f in fh)
# 顺序
order = [fh.index(f"css/{f}") for f in
         ["base.css", "home.css", "widgets.css", "dark.css", "responsive.css"]]
ck("加载顺序正确", order == sorted(order))

# 关键内容
for f, must in [("base.css", "--ink"), ("base.css", "::selection"),
                ("home.css", ".hero-grid"), ("home.css", ".works-grid"),
                ("widgets.css", ".qr-overlay"), ("widgets.css", ".back-top"),
                ("dark.css", '[data-theme="dark"]'),
                ("responsive.css", "max-width: 900px"),
                ("responsive.css", "max-width: 560px")]:
    rr = requests.get(f"{B}/css/{f}", timeout=15)
    ck(f"{f} 含 {must}", must in rr.text, f"含={must in rr.text}")

# 总量守恒:拆分后总字节应与原来接近
total = sum(len(requests.get(f"{B}/css/{f}", timeout=15).text)
            for f in ["base.css", "home.css", "widgets.css", "dark.css",
                      "responsive.css"])
ck("CSS 总量合理(>20KB)", total > 20000, f"实得 {total} 字节")

print()
print("=" * 52)
print("组 2:后台静态资源")
print("=" * 52)
for path, must in [
    ("/admin/static/css/admin.css", ".sidebar"),
    ("/admin/static/css/admin.css", ".sec-grid"),
    ("/admin/static/css/admin.css", ".sec-table"),
    ("/admin/static/css/login.css", ".cap-row"),
    ("/admin/static/js/admin.js", "loadSecOverview"),
    ("/admin/static/js/admin.js", "window.__ADMIN_DATA__"),
    ("/admin/static/js/login.js", "capBox"),
]:
    rr = requests.get(B + path, timeout=15)
    ck(f"{path.split('/')[-1]} 含 {must[:20]}",
       rr.status_code == 200 and must in rr.text,
       f"{rr.status_code}")

ck("admin.css 是 CSS 类型",
   "css" in requests.get(B + "/admin/static/css/admin.css",
                         timeout=15).headers.get("Content-Type", ""))
ck("admin.js 是 JS 类型",
   "javascript" in requests.get(B + "/admin/static/js/admin.js",
                                timeout=15).headers.get("Content-Type", ""))

print()
print("=" * 52)
print("组 3:后台模板瘦身")
print("=" * 52)
lh = requests.get(B + "/admin/login", timeout=15).text
ck("登录页无 <style>", "<style>" not in lh)
ck("登录页引用 login.css", "css/login.css" in lh)
ck("登录页引用 login.js", "js/login.js" in lh)
ck("登录页无 Jinja 残留", "{{" not in lh)
ck("验证码仍在", 'id="capImg"' in lh and 'name="captcha"' in lh)
ck("登录页已瘦身", len(lh) < 9000, f"实得 {len(lh)} 字符")
# 版本号
ck("login.css 带版本号", re.search(r"login\.css\?v=\d+", lh) is not None)

print()
print("=" * 52)
print("组 4:登录态下后台模板")
print("=" * 52)
s = requests.Session()
s.post(B + "/admin/login", data={"password": PWD}, allow_redirects=False,
       timeout=20)
h = s.get(B + "/admin/", timeout=20).text
ck("后台无 <style>", "<style>" not in h)
ck("引用 admin.css", "css/admin.css" in h)
ck("引用 admin.js", "js/admin.js" in h)
ck("数据注入点", "window.__ADMIN_DATA__" in h)
ck("无 Jinja 残留", "{{" not in h)
ck("模板已瘦身", len(h) < 35000, f"实得 {len(h)} 字符")
inline = re.findall(r"(?s)<script>(.*?)</script>", h)
ck("只有 1 段内联脚本", len(inline) == 1, f"实得 {len(inline)}")
if inline:
    ck("内联段无业务逻辑",
       "function " not in inline[0] and "addEventListener" not in inline[0])
ck("admin.css 带版本号", re.search(r"admin\.css\?v=\d+", h) is not None)

print()
print("=" * 52)
print("组 5:功能完好")
print("=" * 52)
d = s.get(B + "/api/content", timeout=15).json()
ck("skills=8", len(d["skills"]) == 8)
ck("works=6", len(d["works"]) == 6)
ck("profile=7", len(d["profile"]) == 7)
ck("安全总览 200", s.get(B + "/api/security/overview", timeout=15).status_code == 200)
ck("审计 200", s.get(B + "/api/security/audit", timeout=15).status_code == 200)
ck("验证码 200", requests.get(B + "/admin/captcha.svg", timeout=15).status_code == 200)
for pid in ["panel-security", "panel-dashboard", "panel-works", "panel-uploads"]:
    ck(f"含 {pid}", pid in h)

print()
print("=" * 52)
print("组 6:安全与缓存")
print("=" * 52)
anon = requests.Session()
ck("未登录后台 302",
   anon.get(B + "/admin/", allow_redirects=False, timeout=15).status_code == 302)
ck("未登录 API 401",
   anon.get(B + "/api/security/overview", timeout=15).status_code == 401)
ck("静态资源可匿名取(登录页需要)",
   anon.get(B + "/admin/static/css/login.css", timeout=15).status_code == 200)
hd = requests.get(B + "/admin/static/css/admin.css", timeout=15).headers
ck("静态资源有缓存头", "cache-control" in {k.lower() for k in hd},
   str(dict(hd))[:100])
hd2 = requests.get(B + "/", timeout=15).headers
ck("首页仍有 HSTS", "strict-transport-security" in {k.lower() for k in hd2})

print()
print("=" * 52)
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(0 if F == 0 else 1)
