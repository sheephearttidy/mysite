"""全站视觉检查:页面渲染、世界地图、动态组件、暗色 CSS。

用 headless Chrome dump-dom 取真实渲染结果,检查关键元素是否出现。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5216"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def dump(url, width=1400, height=900):
    prof = tempfile.mkdtemp(prefix="cprof-")
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=" + prof,
             "--window-size=%d,%d" % (width, height),
             "--virtual-time-budget=12000", "--dump-dom", url],
            capture_output=True, timeout=180,
        )
        return r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def main() -> int:
    print("=" * 62)
    print("前台 9 页")
    print("=" * 62)
    pages = {
        "/": ["你好,我是"],
        "/about": ["关于我这只人类"],
        "/skills": ["技能树", "认真技能"],
        "/works": ["我的小破项目们"],
        "/campus": ["校园打怪升级记录"],
        "/gallery": ["相册"],
        "/map": ["来访地图", "城市排行"],
        "/contact": ["来找我玩", "留言墙"],
        "/nope": ["这个页面跑丢了"],
    }
    for path, needles in pages.items():
        dom, _ = dump(BASE + path)
        missing = [n for n in needles if n not in dom]
        crash = bool(re.search(r"Uncaught|Minified React error", dom))
        ok = not missing and not crash and len(dom) > 500
        ck("%-12s dom=%dB" % (path, len(dom)), ok, "missing=%s crash=%s" % (missing, crash))

    print()
    print("=" * 62)
    print("世界地图")
    print("=" * 62)
    dom, _ = dump(BASE + "/map")
    ck("SVG 底图存在", 'viewBox="0 0 1000 514"' in dom, "")
    ck("国界路径 >= 150 条", len(re.findall(r'<path d="M', dom)) >= 150,
       "实际 %d" % len(re.findall(r'<path d="M', dom)))
    ck("城市圆点 >= 3", len(re.findall(r"<circle", dom)) >= 3,
       "实际 %d" % len(re.findall(r"<circle", dom)))
    ck("经纬网格线", len(re.findall(r"<line", dom)) >= 10,
       "实际 %d" % len(re.findall(r"<line", dom)))

    print()
    print("=" * 62)
    print("动态组件")
    print("=" * 62)
    dom, _ = dump(BASE + "/")
    ck("GradientText 动画", "gradient-flow" in dom, "")
    ck("TextType 光标动画", "cursor-blink" in dom, "")
    ck("ShinyText 扫光", "shiny-sweep" in dom, "")
    ck("Meteors 流星", "meteor-fall" in dom, "")
    ck("Particles canvas", "<canvas" in dom, "")
    ck("Aurora 背景", "aurora-drift" in dom, "")

    print()
    print("=" * 62)
    print("后台")
    print("=" * 62)
    dom, _ = dump(BASE + "/admin.html")
    ck("后台页加载", len(dom) > 800, str(len(dom)))
    ck("登录表单", "后台登录" in dom, "")
    ck("无 React 崩溃", "Minified React error" not in dom, "")

    assets = re.findall(r'src="(/assets/admin-[^"]+\.js)"', dom)
    ck("admin bundle", bool(assets), str(assets))
    if assets:
        import urllib.request

        with urllib.request.urlopen(BASE + assets[0], timeout=20) as r:
            js = r.read().decode("utf-8", "replace")
        ck("bundle 含暗色切换", "暗色" in js, "")
        ck("bundle 含强制改密", "MUST_CHANGE" in js or "must_change" in js, "")
        ck("bundle 含安全中心", "security/settings" in js, "")

    print()
    print("=" * 62)
    print("CSS 变量与暗色")
    print("=" * 62)
    css = re.findall(r'href="(/assets/[^"]+\.css)"', dom)
    if css:
        import urllib.request

        with urllib.request.urlopen(BASE + css[0], timeout=20) as r:
            sheet = r.read().decode("utf-8", "replace")
        ck("含 :root 变量", ":root" in sheet, "")
        ck("含暗色覆盖", 'data-theme="dark"' in sheet or "data-theme=dark" in sheet, "")
        ck("含 --on-accent", "--on-accent" in sheet, "")
        ck("含 .admin-table", ".admin-table" in sheet, "")
        ck("含 .admin-input", ".admin-input" in sheet, "")
        ck("含减少动效适配", "prefers-reduced-motion" in sheet, "")
    else:
        ck("找到 CSS", False, str(css))

    print()
    print("=" * 62)
    print("CSP 兼容性(内联脚本不应被拦)")
    print("=" * 62)
    _, err = dump(BASE + "/")
    violations = [l for l in err.splitlines() if "Content Security Policy" in l or "Refused to" in l]
    ck("首页无 CSP 违规", not violations, "违规 %d 条" % len(violations))
    _, err2 = dump(BASE + "/admin.html")
    v2 = [l for l in err2.splitlines() if "Content Security Policy" in l or "Refused to" in l]
    ck("后台无 CSP 违规", not v2, "违规 %d 条" % len(v2))

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
