#!/bin/bash
# v2.3 安全加固:更新 nginx 头 snippet + 超时收紧,测试并重载
set -e
cp /etc/nginx/snippets/mysite-headers.conf /etc/nginx/snippets/mysite-headers.conf.bak-v23
cp /tmp/mysite-headers.conf /etc/nginx/snippets/mysite-headers.conf
# 代理超时收紧(原来没显式配,默认 60s):慢速攻击面缩小
if ! grep -q 'proxy_read_timeout' /etc/nginx/sites-available/mysite; then
  sed -i 's|proxy_pass http://127.0.0.1:5100/admin/;|proxy_pass http://127.0.0.1:5100/admin/;\n        proxy_read_timeout 30s; proxy_send_timeout 30s;|' /etc/nginx/sites-available/mysite
fi
nginx -t && systemctl reload nginx && echo "nginx 加固完成"
