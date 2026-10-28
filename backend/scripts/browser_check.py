"""浏览器实测:逐页渲染检查(用 headless Chrome dump-dom)。

用法:python scripts/browser_check.py [base_url]
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5199"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# 路径 -> (必须出现的文案, 说明)
PAGES = {
    "/": (["你好,我是", "不正经数据统计"], "首页"),
    "/about": (["关于我这只人类", "荣誉墙"], "关于我"),
    "/skills": (["技能树", "认真技能", "被动技能"], "技能树"),
    "/works": (["我的小破项目们"], "项目墙"),
    "/campus": (["校园打怪升级记录", "时间线"], "校园日常"),
    "/gallery": (["相册"], "相册"),
    "/map": (["来访地图", "城市排行"], "来访地图"),
    "/contact": (["来找我玩", "留言墙", "匿名提问箱"], "来找我"),
    "/nope": (["这个页面跑丢了"], "404"),
}

PASS = FAIL = 0


def find_browser():
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def dump(chrome, url, profile):
    """每次用独立 profile 目录,否则 Chrome 会因默认目录被占用而静默失败。"""
    r = subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--user-data-dir=" + profile,
         "--virtual-time-budget=9000", "--dump-dom", url],
        capture_output=True, timeout=120,
    )
    return r.stdout.decode("utf-8", errors="replace")


def main():
    global PASS, FAIL
    chrome = find_browser()
    if not chrome:
        print("找不到 Chrome / Edge,跳过浏览器测试")
        return 0
    print("browser: %s\n" % chrome)

    for path, (needles, label) in PAGES.items():
        profile = tempfile.mkdtemp(prefix="cprof-")
        try:
            dom = dump(chrome, BASE + path, profile)
        finally:
            shutil.rmtree(profile, ignore_errors=True)

        missing = [n for n in needles if n not in dom]
        crashed = bool(re.search(r"Uncaught|Minified React error", dom))
        empty_root = bool(re.search(r'<div id="root">\s*</div>', dom))

        if not missing and not crashed and not empty_root and len(dom) > 500:
            print("PASS  %-10s %-12s dom=%dB" % (label, path, len(dom)))
            PASS += 1
        else:
            print("FAIL  %-10s %-12s missing=%s crashed=%s empty=%s dom=%dB"
                  % (label, path, missing, crashed, empty_root, len(dom)))
            FAIL += 1

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
