#!/usr/bin/env python3
"""查谁在改 fx 设置(审计日志)"""
import sqlite3
import time

c = sqlite3.connect("/var/www/mysite/admin/data/mysite.db")
c.row_factory = sqlite3.Row

print("=== 最近的 fx_settings 审计记录 ===")
rows = c.execute("""SELECT * FROM audit WHERE action LIKE '%fx%'
                    ORDER BY id DESC LIMIT 10""").fetchall()
if not rows:
    print("  (无)")
for r in rows:
    d = dict(r)
    ts = d.get("ts") or 0
    when = time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"
    print(f"  {when}  {d.get('action')}  ip={d.get('ip')}  detail={str(d.get('detail'))[:80]}")

print()
print("=== 审计表结构 ===")
cols = [r[1] for r in c.execute("PRAGMA table_info(audit)")]
print(" ", cols)

print()
print("=== 最近 10 条任意审计(看有无后台登录) ===")
for r in c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 10"):
    d = dict(r)
    ts = d.get("ts") or 0
    when = time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"
    print(f"  {when}  {d.get('action')}  ip={d.get('ip')}")
c.close()
