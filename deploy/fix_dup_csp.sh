#!/bin/bash
# v2.4 修复:后台 CSP 重复头导致内联脚本被拦(浏览器取交集,nginx 那份没有 nonce)
# 做法:拆成两份 snippet —— 带 CSP 的给前台静态页,不带 CSP 的给 /admin/ 和 /api/
set -e
cd /etc/nginx/snippets

STAMP=$(date +%Y%m%d%H%M%S)
cp -a mysite-headers.conf "mysite-headers.conf.bak-v24-$STAMP"

# 1) 前台用(保留 CSP)
cat > mysite-headers.conf <<'EOF'
# 通用安全响应头 —— 前台静态页用(含 CSP)
# 注意:nginx 的 add_header 不会被子级 location 继承(子级一旦有 add_header 就全丢),
# 所以每个返回内容的 location 都要 include 本文件。
# 后台 /admin/ 和 /api/ 用 mysite-headers-nocsp.conf:
# 后台 CSP 由 Flask(app.py)动态加 nonce,nginx 再发一份会取交集把内联脚本拦掉。

add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# v2.3:前台静态页 CSP(纯静态+Google Fonts,脚本全外链;风格需 unsafe-inline)
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; object-src 'none'" always;
EOF

# 2) 后台用(不含 CSP)
cat > mysite-headers-nocsp.conf <<'EOF'
# 通用安全响应头 —— 后台 /admin/ 与 /api/ 用(不含 CSP)
# 理由:CSP 由 Flask 按请求动态生成(带 nonce);nginx 若再发一份,
# 浏览器会对多条 CSP 取交集,把带 nonce 的内联脚本全部拦掉,
# 表现就是后台侧边栏计数全 0、面板不渲染(v2.4 已踩过这个坑)。

add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
EOF

# 3) 站点配置:/admin/ 与 /api/ 改用不带 CSP 的版本
SITE=/etc/nginx/sites-available/mysite
cp -a "$SITE" "$SITE.bak-v24-$STAMP"

python3 - "$SITE" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()

def fix_block(text, header):
    # 找到 location 块,把块内的 include mysite-headers.conf 换成 nocsp 版
    out, i = [], 0
    while True:
        j = text.find(header, i)
        if j < 0:
            out.append(text[i:])
            break
        # 块结束:从 j 往后找第一个 "\n    }"
        k = text.find("\n    }", j)
        if k < 0:
            out.append(text[i:])
            break
        block = text[i:k]
        block = block.replace("include /etc/nginx/snippets/mysite-headers.conf;",
                              "include /etc/nginx/snippets/mysite-headers-nocsp.conf;")
        out.append(block)
        i = k
    return "".join(out)

for header in ("location ^~ /admin/ {", "location ^~ /api/ {",
               "location = /admin/login {", "location = /admin/captcha.svg {"):
    s = fix_block(s, header)

open(p, "w", encoding="utf-8").write(s)
print("站点配置已更新")
PY

nginx -t && systemctl reload nginx && echo "nginx 已重载"
echo "备份: mysite-headers.conf.bak-v24-$STAMP , $SITE.bak-v24-$STAMP"
