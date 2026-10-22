#!/bin/bash
B=/root/v22pack.bak.$(date +%Y%m%d%H%M%S)
mkdir -p "$B"
cp -r /var/www/mysite/js /var/www/mysite/css "$B/" 2>/dev/null
cp /var/www/mysite/*.html "$B/" 2>/dev/null
cp /var/www/mysite/admin/app.py /var/www/mysite/admin/db.py "$B/" 2>/dev/null
cp -r /var/www/mysite/admin/static/js "$B/admin_js" 2>/dev/null
cp -r /var/www/mysite/admin/static/css "$B/admin_css" 2>/dev/null
cp /var/www/mysite/admin/templates/admin.html "$B/" 2>/dev/null
echo "备份完成: $B"
ls "$B" | head
