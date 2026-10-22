#!/bin/bash
# v1.9.0 生产备份 + 迁移(建新表,不动旧数据)
set -e
TS=$(date +%Y%m%d%H%M%S)
BAK=/root/interact.bak.$TS
mkdir -p $BAK
cd /var/www/mysite
cp index.html about.html skills.html works.html campus.html map.html contact.html $BAK/
cp js/interact.js $BAK/ 2>/dev/null || true
cp css/widgets.css $BAK/
cp admin/app.py admin/db.py $BAK/
cp admin/templates/admin.html $BAK/
cp admin/static/js/admin.js $BAK/
cp admin/static/css/admin.css $BAK/
echo "备份完成: $BAK"

# 迁移:CREATE TABLE IF NOT EXISTS,对已有数据无影响
cd /var/www/mysite/admin
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, "/var/www/mysite/admin")
import db
db.init_db("/var/www/mysite/admin/data/mysite.db")
print("迁移 OK: messages + likes 表已就绪")
import sqlite3
c = sqlite3.connect("/var/www/mysite/admin/data/mysite.db")
tabs = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("表:", ", ".join(sorted(tabs)))
c.close()
PY
