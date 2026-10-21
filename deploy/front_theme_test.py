"""测试环境:前台页面主题相关检查"""
import sys
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


st, body = get("/")
check("前台 200", st == 200, str(st))
check("前台含 themeToggle", 'id="themeToggle"' in body)
check("前台含 theme.js", 'src="js/theme.js"' in body)
check("前台含 main.js", 'src="js/main.js"' in body)
check("前台含防闪脚本", "尽早应用主题" in body or "data-theme-source" in body)
check("前台含双 meta", body.count('name="theme-color"') >= 2)
check("前台含 dark.css", "dark.css" in body)

# CSS 加载顺序:base -> home -> widgets -> dark -> holidays -> responsive
import re
order = re.findall(r'<link[^>]+href="css/([a-z]+\.css)"', body)
check("CSS 顺序正确", order == ["base.css", "home.css", "widgets.css", "dark.css", "holidays.css", "responsive.css"],
      str(order))

# dark.css 内容
st, css = get("/css/dark.css")
check("dark.css 200", st == 200)
check("dark.css 含深色块", '[data-theme="dark"]' in css)
check("dark.css 含 sec 覆盖", ".sec-yellow" in css)
check("dark.css 含 Morandi 色", "#d488a6" in css)

# main.js 不再有主题逻辑
st, js = get("/js/main.js")
check("main.js 无重复主题逻辑", "paint" not in js or "data-theme" not in js.replace("theme.js", ""))

print()
print(f"通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
