#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生产面板切换验证:本地代理登录生产(注入 Origin/Cookie),注入点击探针,
Chrome 打开后逐个点击侧边栏。"""
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

sys.stdout.reconfigure(encoding="utf-8")
PROD = "https://imyxj.xyz"
LOCAL_PORT = 18082
PWD = os.environ.get("PROD_PWD", "")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PASS = FAIL = 0
FAILS = []


def ck(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        FAILS.append(name)
        print(f"  FAIL {name}  {detail}")


# 登录生产
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = op.open(PROD + "/admin/captcha.svg", timeout=25).read().decode()
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
op.open(PROD + "/admin/login",
        urllib.parse.urlencode({"password": PWD, "captcha": code}).encode(), timeout=25)
COOKIE = "; ".join(f"{c.name}={c.value}" for c in cj)
print(f"登录完成,cookie {len(cj)} 个")

PROBE = """
<script>
(function(){
  function run(){
    var out=[], links=document.querySelectorAll('.sb-link');
    for (var i=0;i<links.length;i++){
      var a=links[i], want=a.dataset.panel;
      try { a.click(); } catch(e) { out.push({want:want,got:'CLICK_ERR'}); continue; }
      var act=document.querySelector('.panel.active');
      var got=act?act.id.replace('panel-',''):'(none)';
      var t=document.getElementById('panelTitle');
      out.push({want:want,got:got,title:t?t.textContent:'',ok:got===want});
    }
    var bad=out.filter(function(o){return !o.ok;});
    var msg='PANELRESULT|total='+out.length+'|bad='+bad.length;
    if(bad.length){ msg+='|BAD='+bad.map(function(b){return b.want+'->'+b.got;}).join(','); }
    document.title=msg;
    var pre=document.createElement('pre'); pre.id='__PANELS__';
    pre.textContent=JSON.stringify(out); document.body.appendChild(pre);
  }
  if (document.readyState==='complete') setTimeout(run,800);
  else window.addEventListener('load',function(){setTimeout(run,800);});
})();
</script>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        req = urllib.request.Request(PROD + self.path)
        req.add_header("Cookie", COOKIE)
        req.add_header("User-Agent", "Mozilla/5.0 Chrome/120")
        try:
            r = urllib.request.urlopen(req, timeout=30)
            body, ctype = r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            body, ctype = e.read(), e.headers.get("Content-Type", "")
        if ctype.startswith("text/html"):
            txt = body.decode("utf-8", errors="replace")
            if "panelTitle" in txt and "</body>" in txt:
                txt = txt.replace("</body>", PROBE + "</body>", 1)
            body = txt.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


srv = Server(("127.0.0.1", LOCAL_PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print(f"代理 http://127.0.0.1:{LOCAL_PORT}")

r = subprocess.run(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--virtual-time-budget=25000", "--dump-dom",
     f"http://127.0.0.1:{LOCAL_PORT}/admin/"],
    capture_output=True, encoding="utf-8", errors="replace", timeout=180)
dom = r.stdout
srv.shutdown()

print("=" * 60)
print("生产后台面板切换验证")
print("=" * 60)

m = re.search(r"<title>PANELRESULT\|([^<]*)</title>", dom)
ck("探针执行完成", bool(m), "title 无 PANELRESULT")
if m:
    info = m.group(1)
    total = int(re.search(r"total=(\d+)", info).group(1))
    bad = int(re.search(r"bad=(\d+)", info).group(1))
    print(f"  入口 {total} 个,错误 {bad} 个")
    if bad:
        print("  ", re.search(r"BAD=([^|]*)", info).group(1) if "BAD=" in info else "?")
    ck("所有面板切换正确", bad == 0, f"bad={bad}")
    ck("入口数=24", total == 24, f"total={total}")

mp = re.search(r'<pre id="__PANELS__">(.*?)</pre>', dom, re.S)
if mp:
    import html as H
    rows = json.loads(H.unescape(mp.group(1)))
    for o in rows:
        if o["want"] in ("honors", "notes", "friendlinks", "songs"):
            print(f"   {'✓' if o['ok'] else '✗'} {o['want']:14s} -> {o['got']:14s} | {o.get('title','')}")

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
