#!/bin/bash
# v1.10.0 生产备份 + 部署
set -e
TS=$(date +%Y%m%d%H%M%S)
BAK=/root/datapack.bak.$TS
mkdir -p $BAK
cd /var/www/mysite
cp index.html about.html skills.html works.html campus.html map.html contact.html $BAK/ 2>/dev/null || true
cp js/main.js js/site-extra.js css/widgets.css $BAK/ 2>/dev/null || true
cp admin/app.py admin/db.py $BAK/
cp admin/templates/admin.html $BAK/
cp admin/static/js/admin.js $BAK/
echo "备份: $BAK"
