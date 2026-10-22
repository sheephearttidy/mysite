#!/usr/bin/env python3
"""查生产留言状态分布"""
import sqlite3

c = sqlite3.connect("file:/var/www/mysite/admin/data/mysite.db?mode=ro", uri=True)
c.row_factory = sqlite3.Row
rows = c.execute("SELECT shown, COUNT(*) n FROM messages GROUP BY shown").fetchall()
for r in rows:
    print(f"shown={r['shown']}: {r['n']} 条")
print("--- 最近 5 条 ---")
for r in c.execute("SELECT id,name,substr(body,1,20) body,shown,ts FROM messages ORDER BY ts DESC LIMIT 5"):
    print(dict(r))
