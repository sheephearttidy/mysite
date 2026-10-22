#!/bin/bash
# v2.3.0 生产备份:后台代码+模板+前台资产+HTML 全量
TS=$(date +%Y%m%d%H%M%S)
D=/root/v23pack.bak.$TS
mkdir -p "$D"
cd /var/www/mysite
cp -a admin/app.py admin/db.py "$D/" 2>/dev/null
cp -a admin/templates "$D/"
cp -a admin/static "$D/"
cp -a js css "$D/" 2>/dev/null
cp -a *.html "$D/" 2>/dev/null
echo "备份完成: $D"
ls "$D" | head
