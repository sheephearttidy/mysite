#!/usr/bin/env python3
"""验证 by_hour 时区 bug + 淘宝 API 对各 IP 的真实返回"""
import json
import sqlite3
import subprocess
import sys
import urllib.request

DB = "/var/www/mysite/admin/data/mysite.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== 时区验证 ===")
print("SQLite localtime 与 Python localtime 对比:")
row = c.execute("SELECT ts FROM visits ORDER BY ts DESC LIMIT 1").fetchone()
ts = row["ts"]
import time
py_h = time.localtime(ts).tm_hour
sq = c.execute(
    "SELECT CAST(strftime('%H', ?, 'unixepoch', 'localtime') AS INTEGER) h", (ts,)).fetchone()["h"]
print(f"  ts={ts}")
print(f"  Python localtime 小时: {py_h}")
print(f"  SQLite localtime 小时: {sq}")
print(f"  一致? {'是' if py_h == sq else '否 <-- BUG'}")

print()
print("=== 逐条访问的真实小时 ===")
for r in c.execute("SELECT id,ts,day,path FROM visits ORDER BY ts DESC LIMIT 8"):
    print(f"  #{r['id']} {r['path']:14s} py={time.strftime('%H:%M', time.localtime(r['ts']))} "
          f"sqlite={c.execute(chr(83)+'ELECT strftime(%H, ?, unixepoch, localtime)', (r['ts'],)).fetchone()[0] if False else ''}")

print()
print("=== 淘宝 API 逐个测试 nginx 里的真实 IP ===")
API = "https://ip.taobao.com/outGetIpInfo?ip={}&accessKey=alibaba-inc"
ips = ["223.104.101.73", "34.175.42.73", "45.138.12.51", "39.144.87.218",
       "113.215.189.82", "82.102.18.188", "59.82.83.223", "121.40.40.105",
       "111.55.24.203", "66.132.186.183"]
for ip in ips:
    try:
        req = urllib.request.Request(API.format(ip), headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=6).read().decode("utf-8", "replace")
        j = json.loads(raw)
        d = j.get("data") or {}
        print(f"  {ip:18s} code={j.get('code')} country={d.get('country')!r} "
              f"region={d.get('region')!r} city={d.get('city')!r} isp={d.get('isp')!r}")
    except Exception as e:
        print(f"  {ip:18s} ERROR {type(e).__name__}: {e}")
