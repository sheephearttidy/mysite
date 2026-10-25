#!/usr/bin/env python3
"""清理:删除刚才测试插入的模拟记录(#23, city=江苏 南京, 由 114.114.114.114 模拟)"""
import sqlite3

DB = "/var/www/mysite/admin/data/mysite.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

rows = c.execute("SELECT id,path,city,ts FROM visits ORDER BY id DESC LIMIT 5").fetchall()
print("最近 5 条:")
for r in rows:
    print(f"  #{r['id']} {r['path']:14s} {r['city']!r} ts={r['ts']}")

# 只删 id=23 且 city=江苏 南京 的那条(测试插入)
target = c.execute("SELECT id FROM visits WHERE id=23 AND city='江苏 南京'").fetchone()
if target:
    c.execute("DELETE FROM visits WHERE id=23")
    c.commit()
    print("\n已删除测试记录 #23")
else:
    print("\n未找到 #23,跳过")

print("\n删除后城市分布:")
for r in c.execute("""SELECT CASE WHEN city='' THEN '(空)' ELSE city END c, COUNT(*) n
                      FROM visits GROUP BY c ORDER BY n DESC"""):
    print(f"  {r['c']:16s} {r['n']}")
print("\n总记录数:", c.execute("SELECT COUNT(*) FROM visits").fetchone()[0])
c.close()
