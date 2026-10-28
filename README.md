# 至尊杰的小窝

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)

学生个人主页。前台 React SPA、后台 React 管理面板、FastAPI REST 后端。

> 🏫 燕京理工学院 · 计算机科学与技术
> 🏎️ 智能车 AI · learning and building

---

## 快速开始

### 环境要求

| 工具 | 版本 |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |

### 1. 启动后端

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

本地调试必须关掉 Secure Cookie（HTTP 环境下否则无法登录）：

```bash
# Windows PowerShell
$env:MYSITE_COOKIE_SECURE='0'

# macOS / Linux
export MYSITE_COOKIE_SECURE=0
```

```bash
uvicorn app.main:app --reload --port 5100
```

后端跑在 <http://127.0.0.1:5100>,接口文档见 <http://127.0.0.1:5100/api/docs>。

### 2. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

访问 <http://127.0.0.1:5173>。Vite 已把 `/api` 代理到 5100,无需额外配置。

### 3. 登录后台

访问 <http://127.0.0.1:5173/admin.html>。

初始密码是 `admin`,首次登录会强制改密码。本地开发若没有数据库,首次启动会自动建库并灌入示例内容。

### 4. 生产构建

```bash
cd frontend
npm run build     # 产物在 frontend/dist/
```

后端用 uvicorn 直接跑（不要 `--reload`）：

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 5200 --workers 2
```

完整部署（nginx + systemd）见 [DEPLOY.md](DEPLOY.md)。

---

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | React 18 · TypeScript · Vite · Tailwind CSS |
| 动画组件 | [React Bits](https://reactbits.dev/) 风格,源码级集成 |
| 后端 | FastAPI · SQLAlchemy 2 · Pydantic 2 |
| 数据库 | SQLite |

## 目录结构

```
backend/
├── app/
│   ├── core/       config · db · security · deps
│   ├── models/     22 张表的 ORM 模型
│   ├── schemas/    Pydantic 请求/响应模型
│   ├── services/   content · site
│   ├── api/        content · interact · stats · auth · admin
│   └── main.py     应用入口
├── scripts/        冒烟与回归测试
└── requirements.txt

frontend/
├── src/
│   ├── components/ 通用组件与动画
│   ├── pages/      前台 8 页
│   ├── admin/      后台面板
│   └── lib/        api · theme · useApi
├── index.html      前台入口
└── admin.html      后台入口

admin/data/         本地 SQLite 数据库(gitignore)
assets/             站点图片素材
deploy/             nginx 与 systemd 配置
```

## 动画组件

从 [reactbits.dev](https://reactbits.dev/) 按其设计思路源码级实现,不引运行时依赖:

| 组件 | 对应 | 用途 |
|---|---|---|
| `SplitText` | Split Text | 标题逐字入场 |
| `CountUp` | Count Up | 数字滚动 |
| `SpotlightCard` | Spotlight Card | 光标聚光灯卡片 |
| `TiltedCard` | Tilted Card | 3D 倾斜卡片 |
| `Aurora` | Aurora | 首屏柔光背景 |

均为纯 CSS / transform 实现,尊重 `prefers-reduced-motion`。

## API

运行后访问 `/api/docs` 查看交互式文档。

### 公开接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/site` | 站点信息 |
| GET | `/api/page/{name}` | 按页取数(`index` `about` `skills` `works` `campus` `contact` `map` `gallery`) |
| GET | `/api/content/{kind}` | 某类内容列表 |
| GET | `/api/messages` | 留言墙(仅已审核) |
| POST | `/api/messages` | 发留言 |
| POST | `/api/messages/{id}/follow` | 凭凭证追问 |
| GET | `/api/questions` | 已回答的公开问答 |
| POST | `/api/questions` | 匿名提问 |
| POST | `/api/likes` | 点赞 |
| GET | `/api/map` | 来访城市聚合 |
| POST | `/api/track` | 访问上报 |

### 认证

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/captcha.svg` | 图形验证码 |
| POST | `/api/login` | 登录(密码 + 验证码) |
| POST | `/api/logout` | 登出 |
| GET | `/api/me` | 当前会话 |
| POST | `/api/password` | 修改密码 |

### 后台(需登录)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST/PUT/DELETE | `/api/content/{kind}[/{id}]` | 内容增删改查 |
| GET | `/api/admin/alerts` | 侧边栏角标 |
| GET | `/api/stats/visits` | 数据看板 |
| GET | `/api/stats/visits/csv` | 访问明细导出 |
| GET/POST | `/api/admin/upload` · `/api/admin/uploads` | 图片上传与管理 |
| GET/POST | `/api/admin/backup/export` · `/import` | 数据备份与恢复 |
| GET/POST | `/api/security/*` | 会话 / 审计 / 封锁名单 |

内容类型 `{kind}` 支持:`skills` `timeline` `stats` `works` `profile` `honors` `notes` `friendlinks` `songs` `photos`。

## 设计要点

**输入严格,输出宽松。** 写入时 Pydantic 完整校验(长度、范围、枚举),脏数据进不来;读取时只约束类型不约束范围。历史库里存着 `percent=99999` 这类越界值时,页面照常渲染,不会整页 500。

**新增内容类型只需两处注册。** 在 `services/content.py` 的 `REGISTRY` 和 `api/content.py` 的 `SCHEMAS` 各加一行,CRUD 路由自动生效。

**密码哈希格式沿用旧版。** `pbkdf2:iters:salt:hash`,从 Flask 版本迁移过来时站主无需重置密码。

**SPA 深链回退。** nginx `try_files $uri /index.html`,FastAPI 也做了带路径穿越防护的兜底,`/about` 这类前端路由不会 404。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MYSITE_DB_PATH` | `admin/data/mysite.db` | SQLite 路径 |
| `MYSITE_SECRET_KEY` | 开发占位 | 会话密钥,**线上必须设置** |
| `MYSITE_COOKIE_SECURE` | `true` | 本地 HTTP 调试设为 `0` |
| `MYSITE_UPLOAD_DIR` | `assets/uploads` | 上传目录 |
| `MYSITE_FRONTEND_DIST` | `frontend/dist` | 前端产物目录 |
| `MYSITE_SITE_ORIGIN` | `https://imyxj.xyz` | 站点源 |

## 测试

```bash
# 后端(需先启动服务)
python backend/scripts/smoke.py http://127.0.0.1:5100        # 43 项公开接口
python backend/scripts/test_auth_crud.py                      # 22 项认证 + CRUD
python backend/scripts/browser_check.py http://127.0.0.1:5100 # 9 页真实渲染
python backend/scripts/admin_check.py                         # 17 项后台
```

`test_auth_crud.py` 与 `admin_check.py` 需要指定临时库,避免污染开发数据:

```bash
# Windows PowerShell
$env:SMOKE_DB='D:\tmp\test.db'
$env:SMOKE_BASE='http://127.0.0.1:5100'
```

## 版本

| 版本 | 说明 |
|---|---|
| `v1.0.0` ~ `v3.2.2` | Flask + Jinja 单体(见 Git 历史) |
| `v4.0.0` ~ `v4.2.0` | React 实验版(归档于 `v4-react-archive` 分支) |
| **`v5.0.0`** | **当前:React SPA + FastAPI 重构** |

旧版可通过 `git checkout v3.2.2-pre-react-refactor` 找回。

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
