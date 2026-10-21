#!/bin/bash
# 把本地项目同步到测试环境 /tmp/testapp/(v1.7.0)
set -e
SRC=/root/agent_sync   # 本地上传暂存目录(由 PowerShell scp 填充)
DST=/tmp/testapp

# 后台
cp -f "$SRC/admin/app.py" "$SRC/admin/db.py" "$SRC/admin/geo.py" "$SRC/admin/captcha.py" "$DST/"
# 前台
mkdir -p "$DST/frontend/css" "$DST/frontend/js" "$DST/frontend/assets"
cp -f "$SRC/frontend/"*.html "$DST/frontend/"
cp -f "$SRC/frontend/css/"*.css "$DST/frontend/css/"
cp -f "$SRC/frontend/js/"*.js "$DST/frontend/js/"
# 测试服务器
cp -f "$SRC/run_test.py" "$DST/run.py"
cp -f "$SRC/map_test.py" "$DST/map_test.py"
cp -f "$SRC/pages_test.py" "$DST/pages_test.py"

echo "同步完成:"
ls "$DST" | head -20
echo "---"
ls "$DST/frontend"
