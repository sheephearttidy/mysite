#!/usr/bin/env python3
"""验证 by_day 补零修复(用临时库,不动生产数据)"""
import os
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, "/tmp/dbtest")
import db

# 临时库
tmp = os.path.join(tempfile.mkdtemp(), "t.db")
db.DB_PATH = tmp
db.init_db(tmp)

now = int(time.time())
day = time.strftime("%Y-%m-%d")
with sqlite3.connect(tmp) as c:
    # 今天 3 条,昨天 2 条,5 天前 1 条
    for ts, d in [(now, day),
                  (now - 60, day),
                  (now - 120, day),
                  (now - 86400, time.strftime("%Y-%m-%d", time.localtime(now - 86400))),
                  (now - 86460, time.strftime("%Y-%m-%d", time.localtime(now - 86460))),
                  (now - 5 * 86400, time.strftime("%Y-%m-%d", time.localtime(now - 5 * 86400)))]:
        c.execute("INSERT INTO visits(day,ts,path,referer,ua,is_bot,city) "
                  "VALUES(?,?,?,?,?,?,?)", (d, ts, "/", "", "Chrome / Windows", 0, "江苏 南京"))

P = F = 0


def ck(n, cond, e=""):
    global P, F
    if cond:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


for days in (7, 30, 90):
    d = db.get_visit_stats(days)
    bd = d["by_day"]
    ck(f"{days} 天返回 {days} 个点", len(bd) == days, f"实际 {len(bd)}")
    ck(f"{days} 天最后一个是今天", bd[-1]["day"] == day, bd[-1]["day"])
    ck(f"{days} 天总和 = 真实访问", sum(x["n"] for x in bd) == d["total_real"],
       f'{sum(x["n"] for x in bd)} vs {d["total_real"]}')
    ck(f"{days} 天今天有数", bd[-1]["n"] == 3, str(bd[-1]["n"]))
    # 日期连续
    import datetime
    ds = [datetime.date.fromisoformat(x["day"]) for x in bd]
    gaps = [(ds[i + 1] - ds[i]).days for i in range(len(ds) - 1)]
    ck(f"{days} 天日期连续", all(g == 1 for g in gaps), str(set(gaps)))

print()
print("7 天数据:", [(x["day"][5:], x["n"]) for x in db.get_visit_stats(7)["by_day"]])
print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
