#!/bin/bash
# v2.0.0 生产部署:备份 → 传文件 → 迁移 → 重启
set -e
TS=$(date +%Y%m%d%H%M%S)
BAK=/root/techpack.bak.$TS
mkdir -p $BAK
cd /var/www/mysite
cp index.html about.html skills.html works.html campus.html map.html contact.html $BAK/ 2>/dev/null || true
cp admin/app.py admin/templates/login.html admin/templates/admin.html $BAK/
cp admin/static/js/admin.js $BAK/
echo "备份: $BAK"
echo "OK 备份阶段"
