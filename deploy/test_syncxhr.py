#!/usr/bin/env python3
"""验证假设:同步 XHR 设置 timeout 会抛 InvalidAccessError
起一个本地 HTTP 服务,页面里做同步 XHR + timeout,把结果写进 DOM
"""
import http.server
import socketserver
import subprocess
import tempfile
import threading
import time

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 18877

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<script>
var result = [];
function attempt(label, setTimeout) {
  try {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/fx', false);
    if (setTimeout) xhr.timeout = 1200;   // 同步请求设 timeout
    xhr.send(null);
    result.push(label + ': OK status=' + xhr.status + ' body=' + xhr.responseText.slice(0,40));
  } catch (e) {
    result.push(label + ': THREW ' + e.name + ' - ' + e.message);
  }
}
attempt('A 同步+timeout', true);
attempt('B 同步无timeout', false);
document.addEventListener('DOMContentLoaded', function(){
  document.title = 'RESULT';
  var pre = document.createElement('pre');
  pre.id = 'out';
  pre.textContent = result.join('\\n');
  document.body.appendChild(pre);
});
</script></head><body><p>test</p></body></html>"""


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/fx"):
            body = b'{"mode":"manual","key":"memorial","effects":"1"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            b = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

    def log_message(self, *a):
        pass


srv = socketserver.TCPServer(("127.0.0.1", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.5)

tmp = tempfile.mkdtemp()
out = tmp + r"\dom.html"
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=4000", "--dump-dom",
                f"http://127.0.0.1:{PORT}/test.html"],
               stdout=open(out, "w", encoding="utf-8"),
               stderr=subprocess.DEVNULL, timeout=90)

with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()

print("=== 浏览器里两种写法的结果 ===")
import re
m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
print(m.group(1) if m else "(没拿到结果)")

print()
if "THREW" in (m.group(1) if m else ""):
    print("=> 确认:同步 XHR 设 timeout 会抛异常")
else:
    print("=> 未复现异常,需另找原因")

srv.shutdown()
