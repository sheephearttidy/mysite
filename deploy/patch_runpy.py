#!/usr/bin/env python3
"""给测试环境 run.py 加 manifest.json / sw.js 路由(幂等)"""
import io

p = "/tmp/testapp/run.py"
s = io.open(p, encoding="utf-8").read()
if "manifest.json" in s:
    print("already")
    raise SystemExit

anchor = "A.app.run("
add = (
    '@A.app.get("/manifest.json")\n'
    'def _manifest():\n'
    '    return send_from_directory("/tmp/testapp/frontend", "manifest.json",\n'
    '                               mimetype="application/manifest+json")\n'
    '\n'
    '@A.app.get("/sw.js")\n'
    'def _sw():\n'
    '    return send_from_directory("/tmp/testapp/frontend", "sw.js",\n'
    '                               mimetype="application/javascript")\n'
    '\n'
)
s = s.replace(anchor, add + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")
