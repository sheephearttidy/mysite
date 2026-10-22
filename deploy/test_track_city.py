#!/usr/bin/env python3
"""实测:模拟一次带公网 IP 的访问,验证城市正确入库"""
import json
import sqlite3
import subprocess
import sys
import time
import urllib.request

DB = "/var/www/mysite/admin/data/mysite.db"


def count():
    c = sqlite3.connect(DB)
    n = c.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
    c.close()
    return n


before = count()
print("访问前记录数:", before)

# 直接调 track(带 X-Forwarded-For,模拟 nginx 传真实 IP)
req = urllib.request.Request(
    "http://127.0.0.1:5100/api/track",
    data=json.dumps({"path": "/"}).encode(),
    headers={"Content-Type": "application/json",
             "X-Forwarded-For": "114.114.114.114",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"})
r = urllib.request.urlopen(req, timeout=15)
print("track 响应:", r.read().decode())

time.sleep(1)
after = count()
print("访问后记录数:", after)

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
row = c.execute("SELECT id,path,city,is_bot FROM visits ORDER BY id DESC LIMIT 1").fetchone()
print(f"最新记录: #{row['id']} path={row['path']} city={row['city']!r} bot={row['is_bot']}")
c.close()

ok = after == before + 1 and row["city"]
print()
print(f"{'PASS' if ok else 'FAIL'}  新访问城市正确入库")
sys.exit(0 if ok else 1)
