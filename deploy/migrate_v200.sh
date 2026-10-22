#!/bin/bash
# v2.0.0 生产迁移 + 重启 + 探活
set -e
cd /var/www/mysite/admin
./venv/bin/python -c 'import sys; sys.path.insert(0, "/var/www/mysite/admin"); import app; print("import ok")'
systemctl restart mysite-admin
sleep 2
systemctl is-active mysite-admin
chown -R mysite:mysite /var/www/mysite
curl -s -o /dev/null -w 'manifest:%{http_code} ' https://imyxj.xyz/manifest.json
curl -s -o /dev/null -w 'sw:%{http_code} ' https://imyxj.xyz/sw.js
curl -s -o /dev/null -w 'icon:%{http_code}\n' https://imyxj.xyz/assets/icon-192.png
