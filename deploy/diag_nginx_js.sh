#!/bin/bash
echo "=== 通过 nginx 拿 holiday.js ==="
curl -s -o /tmp/hj.js -w "HTTP=%{http_code} size=%{size_download} cache=%{header_json}\n" \
  https://imyxj.xyz/js/holiday.js 2>/dev/null | head -2

echo
echo "=== 响应头 ==="
curl -sI https://imyxj.xyz/js/holiday.js | head -20

echo
echo "=== 文件内容前 5 行 ==="
head -5 /tmp/hj.js

echo
echo "=== 是否含 /api/fx ==="
grep -c "api/fx" /tmp/hj.js || echo "0 (不含!)"

echo
echo "=== nginx 静态文件缓存配置 ==="
grep -n -A3 "expires\|Cache-Control\|\.js" /etc/nginx/sites-enabled/mysite | head -30

echo
echo "=== 直接访问首页,看 html 里 holiday.js 引用 ==="
curl -s https://imyxj.xyz/ | grep -o 'holiday[^"]*\.js[^"]*' | head -5
