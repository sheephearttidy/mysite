# 至尊杰的小窝 · 新架构部署说明(v5.0)

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

## 回滚

旧版完整保留:
- Git tag `v3.2.2-pre-react-refactor`
- 分支 `v4-react-archive`(React 实验版)
- 服务器 `/root/v322-deploy-bak-*/`
