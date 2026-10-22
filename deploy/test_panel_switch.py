#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""面板切换真机验证:本地代理登录测试环境,把点击探针注入后台 HTML,
Chrome 打开后页面自动逐个点击侧边栏,结果写入 <title>。

运行: python deploy/test_panel_switch.py
需要隧道 15102 已开(ssh -N -L 15102:127.0.0.1:5102 root@SERVER_IP)
"""
import http.server
import io
import json
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

UPSTREAM = "http://127.0.0.1:15102"
LOCAL_PORT = 18081
PWD = "admin"
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


# ---------- 登录拿 cookie ----------
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = op.open(UPSTREAM + "/admin/captcha.svg", timeout=20).read().decode()
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
op.open(UPSTREAM + "/admin/login",
        urllib.parse.urlencode({"password": PWD, "captcha": code}).encode(), timeout=20)
COOKIE = "; ".join(f"{c.name}={c.value}" for c in cj)
print(f"登录完成,cookie: {COOKIE[:40]}...")

# ---------- 探针脚本 ----------
PROBE = """
<script>
(function(){
  function run(){
    var out=[], links=document.querySelectorAll('.sb-link');
    for (var i=0;i<links.length;i++){
      var a=links[i], want=a.dataset.panel;
      try { a.click(); } catch(e) { out.push({want:want,got:'CLICK_ERR',err:String(e)}); continue; }
      var act=document.querySelector('.panel.active');
      var got=act?act.id.replace('panel-',''):'(none)';
      var t=document.getElementById('panelTitle');
      out.push({want:want,got:got,title:t?t.textContent:'(no title)',ok:got===want});
    }
    var bad=out.filter(function(o){return !o.ok;});
    var msg='PANELRESULT|total='+out.length+'|bad='+bad.length;
    if(bad.length){ msg+='|BAD='+bad.map(function(b){return b.want+'->'+b.got;}).join(','); }
    document.title=msg;
    var pre=document.createElement('pre'); pre.id='__PANELS__';
    pre.textContent=JSON.stringify(out); document.body.appendChild(pre);
  }
  if (document.readyState==='complete') setTimeout(run,600);
  else window.addEventListener('load',function(){setTimeout(run,600);});
})();
</script>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        url = UPSTREAM + self.path
        req = urllib.request.Request(url)
        req.add_header("Cookie", COOKIE)
        try:
            r = urllib.request.urlopen(req, timeout=30)
            body = r.read()
            ctype = r.headers.get("Content-Type", "text/html")
        except urllib.error.HTTPError as e:
            body = e.read()
            ctype = e.headers.get("Content-Type", "text/html")
        # 只往后台主页面注入探针
        if ctype.startswith("text/html") and b"<title>" in body:
            txt = body.decode("utf-8", errors="replace")
            if "</body>" in txt and "panelTitle" in txt:
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
print(f"代理已起 http://127.0.0.1:{LOCAL_PORT}")

# ---------- Chrome 打开 ----------
r = subprocess.run(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--virtual-time-budget=25000", "--dump-dom",
     f"http://127.0.0.1:{LOCAL_PORT}/admin/"],
    capture_output=True, encoding="utf-8", errors="replace", timeout=180)
dom = r.stdout
srv.shutdown()

print("=" * 60)
print("后台侧边栏面板切换验证")
print("=" * 60)

m = re.search(r"<title>PANELRESULT\|([^<]*)</title>", dom)
ck("页面跑完探针", bool(m), "title 里没有 PANELRESULT")
if m:
    info = m.group(1)
    total = int(re.search(r"total=(\d+)", info).group(1))
    bad = int(re.search(r"bad=(\d+)", info).group(1))
    print(f"  侧边栏入口 {total} 个,切换错误 {bad} 个")
    if bad:
        print("  错误明细:", re.search(r"BAD=([^|]*)", info).group(1)
              if "BAD=" in info else "?")
    ck("所有面板切换正确", bad == 0, f"bad={bad}")
    ck("侧边栏入口数=24", total == 24, f"total={total}")

# 明细
mp = re.search(r'<pre id="__PANELS__">(.*?)</pre>', dom, re.S)
if mp:
    import html as H
    rows = json.loads(H.unescape(mp.group(1)))
    print("\n  逐项:")
    for o in rows:
        flag = "✓" if o["ok"] else "✗"
        print(f"   {flag} {o['want']:16s} -> {o['got']:16s} | {o.get('title','')}")
else:
    ck("拿到逐项明细", False)

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
for f in FAILS:
    print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
