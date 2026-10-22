#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生产环境截图:后台「站点信息」面板(亮色 + 暗色),确认按钮样式真的生效"""
import http.cookiejar
import http.server
import os
import re
import socketserver
import subprocess
import sys
import threading
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
PROD = "https://imyxj.xyz"
PWD = os.environ.get("PROD_PWD", "")
PORT = 18087
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_shots")
assert PWD, "需要 PROD_PWD"

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = op.open(PROD + "/admin/captcha.svg", timeout=25).read().decode()
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
op.open(PROD + "/admin/login",
        urllib.parse.urlencode({"password": PWD, "captcha": code}).encode(), timeout=25)
COOKIE = "; ".join(f"{c.name}={c.value}" for c in cj)
print("生产登录完成")


def inject(theme):
    return f"""
<script>
window.addEventListener('load', function(){{
  setTimeout(function(){{
    if ('{theme}') {{
      document.documentElement.setAttribute('data-theme','{theme}');
    }} else {{
      document.documentElement.removeAttribute('data-theme');
    }}
    var a = document.querySelector('[data-panel="site-info"]');
    if (a) a.click();
  }}, 700);
}});
</script>
"""


class H(http.server.BaseHTTPRequestHandler):
    theme = ""

    def log_message(self, *a):
        pass

    def do_GET(self):
        req = urllib.request.Request(PROD + self.path)
        req.add_header("Cookie", COOKIE)
        try:
            r = urllib.request.urlopen(req, timeout=30)
            body, ct = r.read(), r.headers.get("Content-Type", "")
        except Exception as e:
            body, ct = str(e).encode(), "text/plain"
        if ct.startswith("text/html"):
            t = body.decode("utf-8", errors="replace")
            if "</body>" in t and "panelTitle" in t:
                t = t.replace("</body>", inject(self.theme) + "</body>", 1)
            body = t.encode()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


os.makedirs(OUTDIR, exist_ok=True)
for theme, tag in (("", "light"), ("dark", "dark")):
    H.theme = theme
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), H)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = os.path.join(OUTDIR, f"prod_site_btn_{tag}.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--virtual-time-budget=18000", "--window-size=1546,1200",
                    f"--screenshot={out}", f"http://127.0.0.1:{PORT}/admin/"],
                   capture_output=True, timeout=180)
    srv.shutdown()
    srv.server_close()
    print(tag, "->", out, os.path.getsize(out) if os.path.exists(out) else "失败")
