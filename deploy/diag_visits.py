#!/usr/bin/env python3
import sqlite3

DB = "/var/www/mysite/admin/data/mysite.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== visits 表结构 ===")
for r in c.execute("PRAGMA table_info(visits)"):
    print(f"  {r['name']:12s} {r['type']:8s} notnull={r['notnull']} default={r['dflt_value']}")

print("\n=== 总行数 ===")
print(" ", c.execute("SELECT COUNT(*) FROM visits").fetchone()[0])

print("\n=== 按 path 分组 ===")
for r in c.execute("SELECT path, COUNT(*) n FROM visits GROUP BY path ORDER BY n DESC"):
    print(f"  {r['path']:20s} {r['n']}")

print("\n=== 按 city 分组 ===")
for r in c.execute("""SELECT CASE WHEN city IS NULL OR city='' THEN '(空)' ELSE city END c,
                             COUNT(*) n FROM visits GROUP BY c ORDER BY n DESC"""):
    print(f"  {r['c']:20s} {r['n']}")

print("\n=== is_bot 分布 ===")
for r in c.execute("SELECT is_bot, COUNT(*) n FROM visits GROUP BY is_bot"):
    print(f"  is_bot={r['is_bot']}  {r['n']}")

print("\n=== 最近 15 条 ===")
for r in c.execute("SELECT id,path,city,is_bot,day,ts FROM visits ORDER BY id DESC LIMIT 15"):
    print(f"  #{r['id']:<4} {r['path']:14s} city={r['city'] or '(空)':14s} bot={r['is_bot']} {r['day']} ts={r['ts']}")

print("\n=== day 分布(最近 10 天) ===")
for r in c.execute("SELECT day, COUNT(*) n FROM visits GROUP BY day ORDER BY day DESC LIMIT 10"):
    print(f"  {r['day']}  {r['n']}")

print("\n=== 全部表 ===")
for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" ", r["name"])
