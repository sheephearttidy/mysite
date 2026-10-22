#!/bin/bash
# v2.4 同步到测试环境:后台 py + 模板 + 静态 JS + 前台页面/CSS/JS
set -e
SRC=/root/agent_sync
DST=/tmp/testapp

cp -f "$SRC/admin/app.py" "$SRC/admin/db.py" "$DST/"

mkdir -p "$DST/templates"
cp -f "$SRC/templates/"*.html "$DST/templates/" 2>/dev/null || true

mkdir -p "$DST/static/js/admin" "$DST/static/css"
cp -f "$SRC/static/js/admin/"*.js "$DST/static/js/admin/" 2>/dev/null || true
cp -f "$SRC/static/js/"*.js "$DST/static/js/" 2>/dev/null || true
cp -f "$SRC/static/css/"*.css "$DST/static/css/" 2>/dev/null || true

mkdir -p "$DST/frontend/css" "$DST/frontend/js"
cp -f "$SRC/frontend/"*.html "$DST/frontend/"
cp -f "$SRC/frontend/css/"*.css "$DST/frontend/css/"
cp -f "$SRC/frontend/js/"*.js "$DST/frontend/js/"

echo "同步完成:"
ls "$DST" | head -25
echo "--- frontend ---"
ls "$DST/frontend"
