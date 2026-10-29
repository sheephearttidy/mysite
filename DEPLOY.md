# 至尊杰的小窝 · 新架构部署说明(v5.2)

## 架构

```
浏览器
  ├── 静态资源(React 产物) → nginx 直出 /var/www/mysite/dist/
  └── /api/*               → 反代到 127.0.0.1:5200(FastAPI / uvicorn)
```

- 前台与后台都是 React SPA(两个入口:`index.html` / `admin.html`)
- 后端纯 REST(FastAPI),不渲染 HTML
- 数据库沿用原 SQLite(`admin/data/mysite.db`),零迁移

## 目录

```
backend/           FastAPI 后端
  app/
    core/          配置 / 数据库 / 安全 / 依赖
    models/        SQLAlchemy 模型(22 张表)
    schemas/       Pydantic 请求响应模型
    services/      业务逻辑
    api/           路由:content / interact / stats / auth / admin
  scripts/         冒烟与回归测试
  requirements.txt
frontend/          React + TS + Tailwind
  src/pages/       前台 8 页
  src/admin/       后台面板
  dist/            构建产物
```

## 本地开发

```bash
# 后端
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
MYSITE_COOKIE_SECURE=0 .venv/Scripts/python -m uvicorn app.main:app --reload --port 5100

# 前端(另开一个终端)
cd frontend
npm install
npm run dev          # http://127.0.0.1:5173,已代理 /api 到 5100
```

## 构建

```bash
cd frontend && npm run build      # 产出 dist/
```

## 测试

```bash
python backend/scripts/smoke.py                 # 43 项公开接口
python backend/scripts/test_auth_crud.py        # 22 项认证 + CRUD
python backend/scripts/browser_check.py         # 9 页真实渲染
python backend/scripts/admin_check.py           # 17 项后台
```

v5.2 起另有一套审计脚本(权限矩阵 / 安全攻击面 / CSRF / 世界地图 / 文档与
部署一致性),完整清单与参数见 README「测试」一节。上线后跑线上终验:

```bash
python backend/scripts/verify_prod_v52.py       # 线上页面 + 接口 + 安全头 + 世界地图
```

## 线上部署(替换现有 Flask 服务)

关键点:**新服务跑 5200,nginx 改指向;旧 Flask 5100 先别删,留作回滚。**

```bash
# 1. 上传代码
rsync -av --exclude 'node_modules' --exclude '.venv' backend/ root@SERVER:/var/www/mysite/backend/
rsync -av --exclude 'node_modules' frontend/dist/ root@SERVER:/var/www/mysite/dist/

# 2. 装依赖
ssh root@SERVER 'cd /var/www/mysite/backend && python3 -m venv .venv && \
  .venv/bin/pip install -r requirements.txt'

# 3. 启动新服务(systemd)
#    /etc/systemd/system/mysite-api.service
#    ExecStart=/var/www/mysite/backend/.venv/bin/uvicorn app.main:app \
#      --host 127.0.0.1 --port 5200 --workers 2
#    Environment=MYSITE_SECRET_KEY=...
#    Environment=MYSITE_DB_PATH=/var/www/mysite/admin/data/mysite.db

# 4. nginx 改指向 5200,静态资源指向 dist/
#    location /api/ { proxy_pass http://127.0.0.1:5200/api/; }
#    location /     { root /var/www/mysite/dist; try_files $uri /index.html; }
#    location = /admin { return 302 /admin.html; }

# 4.1 安全响应头片段:每个返回内容的 location 都 include 它
scp deploy/nginx/mysite-headers.conf root@SERVER:/etc/nginx/snippets/mysite-headers.conf
ssh root@SERVER 'nginx -t && systemctl reload nginx'

# 4.2 线上终验(页面 / 接口 / 安全头 / CSRF / 世界地图)
python backend/scripts/verify_prod_v52.py

# 5. 验证后停旧服务
systemctl stop mysite-admin.service
```

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MYSITE_DB_PATH` | `admin/data/mysite.db` | SQLite 路径 |
| `MYSITE_SECRET_KEY` | 开发占位 | 会话密钥,线上必须设置 |
| `MYSITE_COOKIE_SECURE` | `true` | 本地 HTTP 调试设 `0` |
| `MYSITE_UPLOAD_DIR` | `assets/uploads` | 上传目录 |
| `MYSITE_FRONTEND_DIST` | `frontend/dist` | 前端产物目录 |
| `MYSITE_SITE_ORIGIN` | `https://imyxj.xyz` | 站点源 |
| `MYSITE_EMIT_SECURITY_HEADERS` | `false` | 安全头由 nginx 下发,保持 `false` |

## 安全配置(v5.2)

### 响应头职责划分

安全头(CSP / nosniff / X-Frame-Options 等)**只在 nginx 下发**:
- HTML 由 nginx 直出、不经过 FastAPI,nginx 是唯一出口
- 片段源文件是 `deploy/nginx/mysite-headers.conf`(含 CSP),部署到
  `/etc/nginx/snippets/mysite-headers.conf`;每个返回内容的 location 都要
  `include` 它(nginx 的 `add_header` 不会被子级 location 继承)
- v5.2 起不再分 nocsp 版本:前后台都是 SPA,没有服务端动态 nonce;
  API location 也 include 同一份,CSP 对 JSON 响应无副作用
- FastAPI 的同名中间件由 `MYSITE_EMIT_SECURITY_HEADERS` 控制,保持 `false`,
  否则响应出现重复头

修改安全头后必须:

```bash
nginx -t && systemctl reload nginx
```

### CSRF(跨站请求伪造)

后台写操作(POST/PUT/DELETE)在应用层校验 `Origin` 主机名与请求 `Host` 一致,
跨站或无 Origin 一律 403。nginx 反代时**必须**带上这两个头
(已配置 `proxy_set_header Host $host; proxy_set_header X-Forwarded-For $remote_addr;`),
否则应用看到的 Host 全是 127.0.0.1,会误拦真实请求。

### CSP 注意事项

`script-src 'self'` 不允许任何内联脚本。若要在 `index.html` 加脚本,
必须放 `frontend/public/` 下作为外链文件引入(参考 `theme-init.js`),
否则深色模式防闪烁会失效且浏览器控制台报 CSP 违规。

### 更新世界地图数据

国界数据是预生成的内嵌文件,更新步骤:

```bash
cd backend
python scripts/gen_world_map.py     # 重新下载 world-atlas 并生成
cd ../frontend && npm run build     # 重新构建
```

## 回滚

旧版完整保留:
- Git tag `v3.2.2-pre-react-refactor`
- 分支 `v4-react-archive`(React 实验版)
- 服务器 `/root/v322-deploy-bak-*/`,以及 v5.1/v5.2 各次部署的备份目录
