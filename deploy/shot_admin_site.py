#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""截图后台「站点信息」面板:代理注入 cookie,自动点开面板后截图"""
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
BASE = "http://127.0.0.1:15102"
PORT = 18085
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "_shots", "admin_site_panel.png")

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = op.open(BASE + "/admin/captcha.svg", timeout=20).read().decode()
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
op.open(BASE + "/admin/login",
        urllib.parse.urlencode({"password": "admin", "captcha": code}).encode(), timeout=20)
COOKIE = "; ".join(f"{c.name}={c.value}" for c in cj)
print("登录完成")

INJECT = """
<script>
window.addEventListener('load', function(){
  setTimeout(function(){
    var a = document.querySelector('[data-panel="site-info"]');
    if (a) a.click();
  }, 800);
});
</script>
"""


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        req = urllib.request.Request(BASE + self.path)
        req.add_header("Cookie", COOKIE)
        try:
            r = urllib.request.urlopen(req, timeout=30)
            body, ct = r.read(), r.headers.get("Content-Type", "")
        except Exception as e:
            body, ct = str(e).encode(), "text/plain"
        if ct.startswith("text/html"):
            t = body.decode("utf-8", errors="replace")
            if "</body>" in t and "panelTitle" in t:
                t = t.replace("</body>", INJECT + "</body>", 1)
            body = t.encode()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


srv = S(("127.0.0.1", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=20000", "--window-size=1546,1500",
                f"--screenshot={OUT}", f"http://127.0.0.1:{PORT}/admin/"],
               capture_output=True, timeout=180)
srv.shutdown()
print("截图:", OUT, os.path.getsize(OUT) if os.path.exists(OUT) else "失败")
