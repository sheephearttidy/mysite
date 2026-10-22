#!/bin/bash
# 给前台 HTML 加 no-cache(每次都回源验证,ETag 命中则 304,不浪费带宽)
# 静态资源(js/css/img)仍保持 7d 强缓存,靠 ?v= 哈希失效
set -e

F=/etc/nginx/sites-enabled/mysite
BAK=/root/nginx_html_cache.bak.$(date +%Y%m%d%H%M%S)
cp "$F" "$BAK"
echo "已备份: $BAK"

# 在 "location / {" 块里插入 HTML 的 no-cache 规则
python3 - "$F" <<'PY'
import re
import sys

p = sys.argv[1]
with open(p, encoding="utf-8") as f:
    s = f.read()

if "location ~* \\.html$" in s:
    print("已存在 .html location,跳过")
    sys.exit(0)

anchor = """    # ---- 静态站 ----
    location / {"""
if anchor not in s:
    print("未找到锚点,中止")
    sys.exit(1)

insert = """    # HTML 不缓存(每次回源验证,靠 ETag 走 304);
    # 否则浏览器可能启发式缓存 HTML,导致里面的 ?v= 哈希更新不到
    location ~* \\.html$ {
        add_header Cache-Control 'no-cache' always;
        include /etc/nginx/snippets/mysite-headers.conf;
    }

    # ---- 静态站 ----
    location / {"""

s = s.replace(anchor, insert, 1)
with open(p, "w", encoding="utf-8") as f:
    f.write(s)
print("已插入 .html no-cache 规则")
PY

nginx -t && systemctl reload nginx
echo "nginx 已重载"
