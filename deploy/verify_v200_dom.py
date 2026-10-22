#!/usr/bin/env python3
"""Chrome 渲染确认 v2.0 首页"""
import os
import shutil
import subprocess
import tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="v200_")
out = os.path.join(prof, "d.html")
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--user-data-dir=" + prof, "--virtual-time-budget=8000",
                "--dump-dom", "https://imyxj.xyz/"],
               stdout=open(out, "w", encoding="utf-8"),
               stderr=subprocess.DEVNULL, timeout=180)
with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()
shutil.rmtree(prof, ignore_errors=True)

checks = [
    ("manifest link", 'rel="manifest"' in dom),
    ("SW 注册", "serviceWorker.register" in dom),
    ("v1.9 留言墙仍在", "msgwallGrid" in dom),
    ("v1.9.1 主题球仍在", "accent-btn" in dom),
    ("v1.10 点赞仍在", "likeBtn" in dom),
]
for n, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + n)
print(f"DOM 检查 {sum(ok for _, ok in checks)} / {len(checks)}")
