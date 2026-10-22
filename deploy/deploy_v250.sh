#!/bin/bash
# v2.5 部署:站点信息可配置(后端 + 后台面板 + 前台动态套用)
set -e
STAMP=$(date +%Y%m%d%H%M%S)
ROOT=/var/www/mysite
ADM=$ROOT/admin
BAK=/root/v25bak.$STAMP
S=/root/agent_sync

echo "== 备份到 $BAK =="
mkdir -p "$BAK/admin/static/js/admin" "$BAK/admin/static/css" "$BAK/admin/templates" "$BAK/js"
cp -a "$ADM/app.py" "$ADM/db.py" "$BAK/admin/"
cp -a "$ADM/templates/admin.html" "$BAK/admin/templates/"
cp -a "$ADM/static/js/admin/admin-panel.js" "$BAK/admin/static/js/admin/"
cp -a "$ADM/static/css/admin.css" "$BAK/admin/static/css/"
cp -a "$ROOT"/js/main.js "$BAK/js/"
for f in "$ROOT"/*.html; do cp -a "$f" "$BAK/"; done
echo "备份完成"

echo "== 同步后端 =="
install -m 644 "$S/admin/app.py" "$ADM/app.py"
install -m 644 "$S/admin/db.py" "$ADM/db.py"
install -m 644 "$S/admin/templates/admin.html" "$ADM/templates/admin.html"
install -m 644 "$S/admin/static/js/admin/admin-panel.js" "$ADM/static/js/admin/admin-panel.js"
install -m 644 "$S/admin/static/css/admin.css" "$ADM/static/css/admin.css"

echo "== 同步前台 =="
for f in "$S"/frontend/*.html; do install -m 644 "$f" "$ROOT/"; done
for f in "$S"/frontend/js/*.js; do install -m 644 "$f" "$ROOT/js/"; done
for f in "$S"/frontend/css/*.css; do install -m 644 "$f" "$ROOT/css/"; done

echo "== 重启后端 =="
systemctl restart mysite-admin
sleep 3
systemctl is-active mysite-admin

echo "== 冒烟 =="
curl -s -o /dev/null -w "index=%{http_code} " https://imyxj.xyz/
curl -s -o /dev/null -w "api_page=%{http_code} " https://imyxj.xyz/api/page/index
curl -s -o /dev/null -w "admin=%{http_code} " https://imyxj.xyz/admin/
echo
echo "site 字段:"
curl -s https://imyxj.xyz/api/page/index | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('site'),ensure_ascii=False))"
echo "部署完成(备份:$BAK)"
