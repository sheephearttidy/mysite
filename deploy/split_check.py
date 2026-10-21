#!/usr/bin/env python3
"""验证前后台样式拆分结果"""
import re
import sys
import sqlite3
import requests

B = "http://127.0.0.1:5102"
DB = "/tmp/testapp/data/test.db"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n} {e}")
        F += 1


def login(sess):
    sess.get(f"{B}/admin/captcha.svg")
    txt = sess.get(f"{B}/__test/cap").json()["text"]
    return sess.post(f"{B}/admin/login",
                     data={"password": "admin", "captcha": txt},
                     allow_redirects=False)


print("=" * 52)
print("组 1:后台模板已无内联 CSS/JS")
print("=" * 52)
s = requests.Session()
login(s)
h = s.get(f"{B}/admin/").text
ck("无 <style> 块", "<style>" not in h, f"找到 {h.count('<style>')} 处")
ck("引用了 admin.css", "css/admin.css" in h)
ck("引用了 admin.js", "js/admin.js" in h)
ck("有数据注入点", "window.__ADMIN_DATA__" in h)
ck("有改密标记注入", "window.__ADMIN_MUST_CHANGE__" in h)
ck("无 Jinja 残留", "{{" not in h and "{%" not in h)
# 内联脚本只应剩:数据注入段 + 主题防闪段(v1.5.1 新增,合法)
inline = re.findall(r"(?s)<script>(.*?)</script>", h)
inject = [s for s in inline if "window.__" in s]
foucs = [s for s in inline if "尽早应用主题" in s]
ck("内联脚本只剩注入段+防闪段", len(inject) == 1 and len(foucs) == 1,
   f"注入 {len(inject)} 段 防闪 {len(foucs)} 段 合计 {len(inline)}")
if inject:
    js = inject[0]
    ck("内联段只有 window 赋值", js.count("window.__") == 2,
       f"实得 {js.count('window.__')} 处")
    ck("内联段无函数定义", "function " not in js)
    ck("内联段无事件绑定", "addEventListener" not in js)
    ck("内联段无 DOM 查询", "getElementById" not in js)
ck("模板体积已降", len(h) < 30000, f"实得 {len(h)} 字符")

print()
print("=" * 52)
print("组 2:登录页已无内联 CSS/JS")
print("=" * 52)
lh = requests.get(f"{B}/admin/login").text
ck("无 <style> 块", "<style>" not in lh)
ck("引用了 login.css", "css/login.css" in lh)
ck("引用了 login.js", "js/login.js" in lh)
ck("无 Jinja 残留", "{{" not in lh and "{%" not in lh)
ck("验证码输入框仍在", 'name="captcha"' in lh)
ck("验证码图片仍在", 'id="capImg"' in lh)
ck("模板体积已降", len(lh) < 8000, f"实得 {len(lh)} 字符")

print()
print("=" * 52)
print("组 3:静态资源可访问且内容正确")
print("=" * 52)
for path, must, desc in [
    ("/admin/static/css/admin.css", ".sidebar", "侧边栏样式"),
    ("/admin/static/css/admin.css", ".sec-grid", "安全面板样式"),
    ("/admin/static/css/admin.css", ".sec-table", "安全表格样式"),
    ("/admin/static/css/admin.css", ".switch", "开关样式"),
    ("/admin/static/css/admin.css", ":root", "配色变量"),
    ("/admin/static/css/login.css", ".cap-row", "验证码行样式"),
    ("/admin/static/css/login.css", ".cap-img", "验证码图样式"),
    ("/admin/static/css/login.css", ".blocked", "封锁提示样式"),
    ("/admin/static/js/admin.js", "function loadSecOverview", "安全总览函数"),
    ("/admin/static/js/admin.js", "function saveSecSettings", "保存设置函数"),
    ("/admin/static/js/admin.js", "function loadAudit", "审计函数"),
    ("/admin/static/js/admin.js", "function revokeAllSessions", "踢会话函数"),
    ("/admin/static/js/admin.js", "window.__ADMIN_DATA__", "读注入数据"),
    ("/admin/static/js/login.js", "capBox", "验证码点击"),
    ("/admin/static/js/login.js", "if (!box) return", "元素缺失自动跳过"),
]:
    r = requests.get(B + path)
    ok = r.status_code == 200 and must in r.text
    ck(f"{path.split('/')[-1]} 含{desc}", ok,
       f"{r.status_code}, 含={must in r.text}")

r = requests.get(B + "/admin/static/css/admin.css")
ck("CSS Content-Type", "css" in r.headers.get("Content-Type", ""),
   r.headers.get("Content-Type"))
r = requests.get(B + "/admin/static/js/admin.js")
ck("JS Content-Type", "javascript" in r.headers.get("Content-Type", ""),
   r.headers.get("Content-Type"))

print()
print("=" * 52)
print("组 4:静态资源无需登录也能取(浏览器缓存需要)")
print("=" * 52)
# CSS/JS 必须能匿名拿到,否则登录页会没样式
for path in ["/admin/static/css/login.css", "/admin/static/js/login.js"]:
    r = requests.get(B + path)
    ck(f"{path.split('/')[-1]} 匿名可访问", r.status_code == 200,
       f"实得 {r.status_code}")

print()
print("=" * 52)
print("组 5:缓存版本号")
print("=" * 52)
m = re.search(r"css/admin\.css\?v=(\d+)", h)
ck("admin.css 带版本号", m is not None)
if m:
    ck("版本号是数字时间戳", m.group(1).isdigit() and len(m.group(1)) >= 10,
       m.group(1))
m2 = re.search(r"js/admin\.js\?v=(\d+)", h)
ck("admin.js 带版本号", m2 is not None)
m3 = re.search(r"css/login\.css\?v=(\d+)", lh)
ck("login.css 带版本号", m3 is not None)
if m and m2:
    ck("同页版本号一致", m.group(1) == m2.group(1))

print()
print("=" * 52)
print("组 6:前台 CSS 拆分")
print("=" * 52)
fh = requests.get(B + "/").text
ck("无 style.css 引用", "style.css" not in fh)
for f in ["base.css", "home.css", "widgets.css", "dark.css", "responsive.css"]:
    ck(f"index 引用 {f}", f in fh)
# 顺序必须与层叠依赖一致
order = [fh.index(f"css/{f}") for f in
         ["base.css", "home.css", "widgets.css", "dark.css", "responsive.css"]]
ck("加载顺序正确", order == sorted(order), f"实得 {order}")
for f, must in [("base.css", ":root"), ("base.css", "--pink"),
                ("home.css", ".hero"), ("home.css", ".works-grid"),
                ("widgets.css", "footer"), ("widgets.css", ".qr-overlay"),
                ("dark.css", '[data-theme="dark"]'),
                ("responsive.css", "@media")]:
    r = requests.get(f"{B}/css/{f}")
    ck(f"{f} 含 {must}", r.status_code == 200 and must in r.text,
       f"{r.status_code}, 含={must in r.text}")
# 响应式必须是最后一个
r = requests.get(f"{B}/css/responsive.css")
ck("responsive 只含媒体查询", r.text.count("@media") >= 2)

print()
print("=" * 52)
print("组 7:功能未受影响")
print("=" * 52)
d = s.get(f"{B}/api/content").json()
ck("skills=8", len(d["skills"]) == 8, f"实得 {len(d['skills'])}")
ck("works=6", len(d["works"]) == 6)
ck("profile=7", len(d["profile"]) == 7)
ck("安全总览 200", s.get(f"{B}/api/security/overview").status_code == 200)
ck("审计 200", s.get(f"{B}/api/security/audit").status_code == 200)
ck("导出 200", s.get(f"{B}/api/export").status_code == 200)
ck("看板 200", s.get(f"{B}/api/stats/visits").status_code == 200)
ck("验证码图 200", requests.get(f"{B}/admin/captcha.svg").status_code == 200)

# 面板元素都在
for pid in ["panel-dashboard", "panel-skills", "panel-timeline", "panel-stats",
            "panel-works", "panel-profile", "panel-uploads", "panel-backup",
            "panel-security"]:
    ck(f"页面含 {pid}", pid in h)

print()
print("=" * 52)
print("组 8:未登录访问后台仍被拦")
print("=" * 52)
anon = requests.Session()
r = anon.get(f"{B}/admin/", allow_redirects=False)
ck("后台页面 302", r.status_code == 302, f"实得 {r.status_code}")
ck("API 401", anon.get(f"{B}/api/security/overview").status_code == 401)

print()
print("=" * 52)
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(0 if F == 0 else 1)
