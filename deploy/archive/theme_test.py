"""测试环境:登录后台 + 验证主题切换功能是否正常"""
import re
import sys
import urllib.request
import urllib.parse
import http.cookiejar
import ssl

BASE = "http://127.0.0.1:5102"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

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


def get(path, as_admin=False):
    req = urllib.request.Request(BASE + path)
    if as_admin:
        req.add_header("X-Requested-With", "XMLHttpRequest")
    r = opener.open(req, timeout=15)
    return r.status, r.read().decode("utf-8", "replace")


# 1. 登录页
st, body = get("/admin/login")
check("登录页 200", st == 200, str(st))
check("登录页含主题按钮", 'id="themeBtn"' in body)
check("登录页含 theme.js", "js/theme.js" in body)
check("登录页含防闪脚本", "尽早应用主题" in body)
check("登录页含深色 meta", 'content="#1c1a21"' in body)

# 2. 取验证码并识别(纯 stdlib 识别器从 captcha.py 的逻辑来)
cap_src = open("captcha.py", encoding="utf-8").read()
# 服务器返回的 svg 里字符以 text 形式存在,直接解析即可
req = urllib.request.Request(BASE + "/admin/captcha.svg")
cap = opener.open(req, timeout=15)
svg = cap.read().decode("utf-8")
check("验证码图 200", cap.status == 200)
chars = re.findall(r'<text[^>]*>([A-Z0-9])</text>', svg)
cap_text = "".join(chars)
check("验证码含字符", len(cap_text) >= 4, repr(cap_text[:10]))

# 3. 提交登录
# 测试环境密码为初始密码 admin(must_change_pass=1),生产密码通过环境变量传入
import os
pwd = os.environ.get("TEST_PWD", "admin")
check("测试密码已提供", len(pwd) > 0)
data = urllib.parse.urlencode({"password": pwd, "captcha": cap_text}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data)
try:
    r = opener.open(req, timeout=15)
    st2 = r.status
    final = r.geturl()
    body2 = r.read().decode("utf-8", "replace")
except urllib.error.HTTPError as e:
    st2 = e.code
    final = e.geturl()
    body2 = e.read().decode("utf-8", "replace")
# 真正的成功判定:登录后响应里应包含后台面板(或重定向到 /admin/)
check("登录成功(含后台面板)", "panel-dashboard" in body2 or "panel-skills" in body2,
      f"{st2} {final}")

# 4. 后台主页
st, body = get("/admin/", as_admin=True)
check("后台主页 200", st == 200, str(st))
check("后台含主题按钮", 'id="themeBtn"' in body)
check("后台含 theme.js", "js/theme.js" in body)
check("后台含 admin.css", "css/admin.css" in body)
check("后台含防闪脚本", "尽早应用主题" in body)

# 5. theme.js 静态资源可达
for p in ["/admin/static/js/theme.js", "/admin/static/js/admin.js",
          "/admin/static/css/admin.css", "/admin/static/css/login.css"]:
    st, b = get(p)
    check(f"静态资源 {p}", st == 200, str(st))

# 6. theme.js 内容检查
st, js = get("/admin/static/js/theme.js")
check("theme.js 含 themeToggle", "themeToggle" in js)
check("theme.js 含 localStorage", "localStorage" in js)
check("theme.js 含 matchMedia", "matchMedia" in js)
check("theme.js 含 data-theme", "data-theme" in js)

# 7. admin.css 深色块
st, css = get("/admin/static/css/admin.css")
check("admin.css 含深色块", '[data-theme="dark"]' in css)
check("admin.css 含 bf- 类", ".bf-pink" in css and ".bf-teal" in css)
check("admin.css 含主题按钮", ".theme-btn" in css)

# 8. admin.js 不再有 COLORS 硬编码
st, js = get("/admin/static/js/admin.js")
check("admin.js 无 COLORS", "COLORS" not in js)
check("admin.js 用 bf- 类", "bf-" in js)

print()
print(f"通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
