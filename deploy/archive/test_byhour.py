#!/usr/bin/env python3
"""验证 by_hour 用 ts+8h 计算,不依赖服务器/SQLite 时区"""
import os
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, "/tmp/dbtest2")
import db

tmp = os.path.join(tempfile.mkdtemp(), "t.db")
db.DB_PATH = tmp
db.init_db(tmp)

# 构造:北京时间 08:04、07:59、00:59、23:30 各一条
BJ = 8 * 3600
cases = [
    ("2026-10-22 08:04", 1792627461),
    ("2026-10-22 07:59", 1792627157),
    ("2026-10-22 00:59", 1792601985),
    ("2026-10-21 23:30", 1792596618),
]
with sqlite3.connect(tmp) as c:
    for label, ts in cases:
        c.execute("INSERT INTO visits(day,ts,path,referer,ua,is_bot,city) "
                  "VALUES(?,?,?,?,?,?,?)", ("2026-10-22", ts, "/", "", "Chrome / Windows", 0, ""))

d = db.get_visit_stats(30)
bh = d["by_hour"]
print("北京时间应落在:")
expect = {}
for label, ts in cases:
    h = time.gmtime(ts + BJ).tm_hour
    expect[h] = expect.get(h, 0) + 1
    print(f"  {label} -> 小时 {h}")

print()
print("by_hour 非零:", {h: n for h, n in enumerate(bh) if n})
print("期望        :", expect)

ok = {h: n for h, n in enumerate(bh) if n} == expect
print()
print(f"{'PASS' if ok else 'FAIL'}  小时分布正确(不依赖服务器时区)")
sys.exit(0 if ok else 1)
