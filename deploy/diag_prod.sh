#!/bin/bash
# 生产资产诊断:widgets.css 哈希、页面引用、qrcode 加载
cd /var/www/mysite
echo "--- 本地 sha256[:8] ---"
sha256sum css/widgets.css js/interact.js admin/static/js/qrcode.min.js 2>&1 | awk '{print substr($1,1,8), $2}'
echo "--- 页面引用 ---"
grep -o 'widgets.css?v=[a-f0-9]*' index.html | head -1
grep -o 'interact.js?v=[a-f0-9]*' index.html | head -1
grep -o 'qrcode[^"]*"' admin/templates/admin.html | head -2
echo "--- 生产 qrcode 文件 ---"
ls -la admin/static/js/qrcode.min.js 2>&1
echo "--- HTTP ---"
curl -s -o /dev/null -w 'qrcode.min.js:%{http_code}\n' https://imyxj.xyz/admin/static/js/qrcode.min.js
curl -s -o /dev/null -w 'widgets.css:%{http_code}\n' "https://imyxj.xyz/css/widgets.css?v=$(sha256sum css/widgets.css | cut -c1-8)"
echo "--- admin.html 模板是否在用(检查 Flask 渲染源) ---"
grep -c 'qrcode' /var/www/mysite/admin/templates/admin.html
