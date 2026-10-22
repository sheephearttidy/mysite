#!/usr/bin/env python3
import json
import sqlite3
import urllib.request

print("=== /api/fx ===")
print(json.loads(urllib.request.urlopen("https://imyxj.xyz/api/fx", timeout=20).read()))

print()
print("=== DB settings ===")
c = sqlite3.connect("/var/www/mysite/admin/data/mysite.db")
for row in c.execute("SELECT key, value FROM settings WHERE key LIKE 'fx%'"):
    print(f"  {row[0]:22s} = {row[1]!r}")
c.close()
