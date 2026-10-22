#!/bin/bash
# v2.4.1 部署:只改前台静态文件,不需要重启后端
set -e
STAMP=$(date +%Y%m%d%H%M%S)
ROOT=/var/www/mysite
BAK=/root/v241bak.$STAMP
S=/root/agent_sync

echo "== 备份到 $BAK =="
mkdir -p "$BAK"
for f in map.html about.html index.html skills.html works.html campus.html contact.html; do
  [ -f "$ROOT/$f" ] && cp -a "$ROOT/$f" "$BAK/$f"
done
cp -a "$ROOT/js" "$BAK/js"
cp -a "$ROOT/css" "$BAK/css"
echo "备份完成"

echo "== 同步前台 =="
for f in "$S"/frontend/*.html; do install -m 644 "$f" "$ROOT/"; done
for f in "$S"/frontend/js/*.js; do install -m 644 "$f" "$ROOT/js/"; done
for f in "$S"/frontend/css/*.css; do install -m 644 "$f" "$ROOT/css/"; done
echo "同步完成"

echo "== 冒烟 =="
curl -s -o /dev/null -w "map=%{http_code} " https://imyxj.xyz/map.html
curl -s -o /dev/null -w "about=%{http_code} " https://imyxj.xyz/about.html
curl -s -o /dev/null -w "mapjs=%{http_code} " https://imyxj.xyz/js/map.js
echo
echo "部署完成(备份:$BAK)"
