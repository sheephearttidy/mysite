#!/bin/bash
# v1.8.0 部署:后台控制前台特效 + 安全多级菜单
set -e
TS=$(date +%Y%m%d%H%M%S)
BAK="/root/fxctl.bak.$TS"
mkdir -p "$BAK"
echo "备份到 $BAK"

# 需要备份/替换的文件
FILES="
admin/app.py
admin/db.py
admin/templates/admin.html
admin/static/js/admin.js
admin/static/js/holiday.js
js/holiday.js
"

for f in $FILES; do
  if [ -f "/var/www/mysite/$f" ]; then
    mkdir -p "$BAK/$(dirname $f)"
    cp "/var/www/mysite/$f" "$BAK/$f"
  fi
done
echo "备份完成"
ls -R "$BAK" | head -20
