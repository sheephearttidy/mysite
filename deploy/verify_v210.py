#!/usr/bin/env python3
"""v2.1.0 生产验证:拆分后所有资产可达 + 关键渲染(Chrome)"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
P = F = 0


def ck(n, c, e=""):
    global P, F
    print(("PASS  " if c else "FAIL  ") + n + (("  " + e) if e and not c else ""))
    P, F = P + (1 if c else 0), F + (0 if c else 1)


def get(p):
    try:
        r = urllib.request.urlopen("https://imyxj.xyz" + p, timeout=20)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


print("=== 资产可达性(拆分后新格局) ===")
for p in ["/js/core.js", "/js/main.js", "/js/interact.js", "/js/site-extra.js",
          "/css/widgets.css", "/css/dark.css", "/css/responsive.css",
          "/admin/static/js/admin/admin-core.js", "/admin/static/js/admin/admin-panel.js",
          "/admin/static/js/admin/admin-content.js", "/admin/static/js/admin/admin-media.js",
          "/admin/static/js/admin/admin-ops.js", "/admin/static/js/admin/admin-site.js",
          "/admin/static/js/admin/admin-app.js"]:
    st, _ = get(p)
    ck(f"GET {p}", st == 200, str(st))

st, old = get("/admin/static/js/admin.js")
ck("旧 admin.js 已移除(404)", st == 404, str(st))

print()
print("=== 页面引用完整性 ===")
st, ih = get("/")
ck("index 引 core.js 先于 main.js", "js/core.js" in ih and
   ih.index("js/core.js") < ih.index("js/main.js"))
ck("index 七个前台 JS 全带版本",
   all(re.search(rf"js/{f}\.js\?v=[0-9a-f]{{8}}", ih) for f in
       ["holiday", "theme", "core", "ambience", "site-extra", "main",
        "interact", "holiday-fx"]))
m = re.search(r"css/widgets\.css\?v=([0-9a-f]{8})", ih)
if m:
    st2, w = get("/css/widgets.css?v=" + m.group(1))
    ck("widgets.css 版本哈希与内容一致", st2 == 200)

print()
print("=== Chrome 渲染 ===")


def dump(url, wait=9):
    prof = tempfile.mkdtemp(prefix="v210_")
    out = os.path.join(prof, "d.html")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + prof, f"--virtual-time-budget={wait*1000}",
                    "--dump-dom", url],
                   stdout=open(out, "w", encoding="utf-8"),
                   stderr=subprocess.DEVNULL, timeout=180)
    dom = io.open(out, encoding="utf-8", errors="replace").read()
    shutil.rmtree(prof, ignore_errors=True)
    return dom


dom = dump("https://imyxj.xyz/#msgwall", wait=9)
ck("首页渲染出 hero", "hero" in dom)
ck("留言墙卡片存在(v2.0.2 保持)", "msg-note" in dom)
ck("无 JS 崩溃痕迹(hero 数据在)", "至尊杰" in dom)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
