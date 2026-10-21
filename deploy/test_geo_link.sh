#!/bin/bash
# 验证 track -> geo 异步回填 -> /api/map 完整链路
B="http://127.0.0.1:5102"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"

echo "=== 1. track(模拟南京 IP 114.114.114.114) ==="
curl -s -X POST "$B/api/track" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 114.114.114.114" \
  -H "User-Agent: $UA" \
  -d '{"path": "/map.html"}'
echo
echo "=== 2. track(模拟北京 IP 61.135.169.125) ==="
curl -s -X POST "$B/api/track" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 61.135.169.125" \
  -H "User-Agent: $UA" \
  -d '{"path": "/"}'
echo
echo "=== 3. 等 3 秒让异步 geo 完成 ==="
sleep 3
echo "=== 4. /api/map 城市聚合 ==="
curl -s "$B/api/map"
echo
echo "=== 5. 最近访问含城市? (看库) ==="
cd /tmp/testapp && /var/www/mysite/admin/venv/bin/python -c "
import sqlite3
c = sqlite3.connect('/tmp/testapp/data/test.db')
c.row_factory = sqlite3.Row
for r in c.execute('SELECT path, city FROM visits ORDER BY id DESC LIMIT 4'):
    print(dict(r))
"
