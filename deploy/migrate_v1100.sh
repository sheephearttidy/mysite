#!/bin/bash
# v1.10.0 生产迁移 + 重启
set -e
cd /var/www/mysite/admin
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, "/var/www/mysite/admin")
import db
db.init_db("/var/www/mysite/admin/data/mysite.db")
print("migrate ok")
PY
chown -R mysite:mysite /var/www/mysite
systemctl restart mysite-admin
sleep 2
systemctl is-active mysite-admin
