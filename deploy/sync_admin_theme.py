#!/usr/bin/env python3
"""v2.1 冗余治理:主题/节日文件前后台各一份的同步检查

背景:前台静态资源由 nginx 直出(/var/www/mysite/{js,css}),
后台静态由 Flask 出(/admin/static/...),两处目录不同。
theme.js / holiday.js / holiday-fx.js / holidays.css 四个文件
前台后台都要用,历史上是两份拷贝,极易改一漏一。

本脚本:
1. 校验四对文件内容一致(不一致则退出码 1,CI/部署前跑)
2. --fix 时把前台版本(单一真源)覆盖到 admin/static/
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (前台真源, 后台副本)
PAIRS = [
    ("js/theme.js",      "admin/static/js/theme.js"),
    ("js/holiday.js",    "admin/static/js/holiday.js"),
    ("js/holiday-fx.js", "admin/static/js/holiday-fx.js"),
    ("css/holidays.css", "admin/static/css/holidays.css"),
]


def digest(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


fix = "--fix" in sys.argv
bad = []
for src, dst in PAIRS:
    sp, dp = os.path.join(ROOT, src), os.path.join(ROOT, dst)
    if not os.path.exists(sp):
        bad.append(f"{src} 不存在")
        continue
    if not os.path.exists(dp):
        bad.append(f"{dst} 不存在")
        if fix:
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copyfile(sp, dp)
            print(f"FIX  已复制 {src} -> {dst}")
        continue
    if digest(sp) != digest(dp):
        bad.append(f"{src} 与 {dst} 内容不一致")
        if fix:
            shutil.copyfile(sp, dp)
            print(f"FIX  已同步 {src} -> {dst}")

if bad:
    print("发现不一致:")
    for b in bad:
        print("  -", b)
    if not fix:
        print("运行: python deploy/sync_admin_theme.py --fix  # 以前台为准同步")
        sys.exit(1)
    print("已全部以前台版本同步")
else:
    print(f"OK  {len(PAIRS)} 对主题文件前后台一致")
