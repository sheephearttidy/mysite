#!/bin/bash
# 生产备份(v1.7.0 部署前)
TS=$(date +%Y%m%d%H%M%S)
DIR="/root/mapfx.bak.$TS"
mkdir -p "$DIR"
cp /var/www/mysite/index.html \
   /var/www/mysite/about.html \
   /var/www/mysite/skills.html \
   /var/www/mysite/works.html \
   /var/www/mysite/campus.html \
   /var/www/mysite/contact.html \
   /var/www/mysite/css/base.css \
   /var/www/mysite/css/home.css \
   /var/www/mysite/css/widgets.css \
   /var/www/mysite/css/dark.css \
   /var/www/mysite/css/responsive.css \
   /var/www/mysite/js/main.js \
   /var/www/mysite/js/theme.js \
   /var/www/mysite/admin/app.py \
   /var/www/mysite/admin/db.py \
   /var/www/mysite/admin/static/css/admin.css \
   /var/www/mysite/admin/static/js/admin.js \
   /var/www/mysite/admin/templates/admin.html \
   /var/www/mysite/admin/templates/login.html \
   "$DIR/"
echo "备份到 $DIR : $(ls "$DIR" | wc -l) 个文件"
