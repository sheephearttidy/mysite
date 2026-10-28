# 至尊杰的小窝 · v5.0(React + FastAPI)

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)

学生个人主页。**前台 React SPA + 后台 React 管理面板 + FastAPI REST 后端。**

> 🏫 燕京理工学院 · 计算机科学与技术
> 🏎️ 智能车 AI · learning and building

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 动画组件 | [React Bits](https://reactbits.dev/) 风格组件(源码级集成) |
| 后端 | FastAPI + SQLAlchemy 2.x + Pydantic 2 |
| 数据库 | SQLite(沿用 v3 的老库,零迁移) |
| 部署 | nginx(静态) + uvicorn(systemd) |

## 目录结构

```
backend/
  app/
    core/       config · db · security · deps
    models/     22 张表的 ORM 模型
    schemas/    Pydantic 请求/响应模型
    services/   content · site
    api/        content · interact · stats · auth · admin
  scripts/      冒烟/回归测试
frontend/
  src/
    components/ SplitText · CountUp · SpotlightCard · TiltedCard · Aurora · Nav · Footer
    pages/      前台 8 页
    admin/      后台面板
    lib/        api · theme · useApi
  dist/         构建产物
deploy/         nginx 与 systemd 配置
DEPLOY.md       部署手册
```

## 快速开始

```bash
# 后端
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
MYSITE_COOKIE_SECURE=0 .venv/Scripts/python -m uvicorn app.main:app --reload --port 5100

# 前端
cd frontend && npm install && npm run dev
```

访问 <http://127.0.0.1:5173>(前台)/ <http://127.0.0.1:5173/admin.html>(后台)。

## 测试

```bash
python backend/scripts/smoke.py            # 43 项:公开接口 / 未授权 / 输入校验
python backend/scripts/test_auth_crud.py   # 22 项:登录 + CRUD + 导出
python backend/scripts/browser_check.py    # 9 页真实渲染(headless Chrome)
python backend/scripts/admin_check.py      # 17 项:后台接口 + 资源
```

## React Bits 组件

从 [reactbits.dev](https://reactbits.dev/) 按其设计思路源码级实现(不引运行时依赖):

| 组件 | 对应 | 用途 |
|---|---|---|
| `SplitText` | Split Text | 标题逐字入场 |
| `CountUp` | Count Up | 数字滚动 |
| `SpotlightCard` | Spotlight Card | 光标聚光灯卡片 |
| `TiltedCard` | Tilted Card | 3D 倾斜卡片 |
| `Aurora` | Aurora | 首屏柔光背景 |

均为纯 CSS/transform 实现,尊重 `prefers-reduced-motion`,移动端不掉帧。

## API 概览

完整文档:运行后访问 `/api/docs`(Swagger)。

```
GET  /api/health                 健康检查
GET  /api/site                   站点信息
GET  /api/page/{name}            按页取数(index/about/skills/works/campus/contact/map/gallery)
GET  /api/content                全量内容
GET  /api/content/{kind}         某类内容列表
POST /api/content/{kind}         新增(需登录)
PUT  /api/content/{kind}/{id}    部分更新(需登录)
DELETE /api/content/{kind}/{id}  删除(需登录)
GET  /api/messages               留言墙(已审核)
POST /api/messages               发留言
POST /api/messages/{id}/follow   凭凭证追问
GET  /api/questions              已答公开问答
POST /api/questions              匿名提问
POST /api/likes                  点赞
GET  /api/map                    来访城市聚合
POST /api/track                  访问上报
GET  /api/captcha.svg            图形验证码
POST /api/login                  登录
POST /api/logout                 登出
GET  /api/me                     当前会话
```

后台专属接口(需登录)挂在 `/api/admin/*` 与 `/api/stats/*`、`/api/security/*`。

## 从 v3 升级

- 数据库表结构**完全不变**,22 张表逐一对应
- 密码哈希格式沿用 `pbkdf2:iters:salt:hash`,**站主无需重置密码**
- 旧版完整保留在 Git tag `v3.2.2-pre-react-refactor`

详见 [DEPLOY.md](DEPLOY.md)。

## 版本

| 版本 | 说明 |
|---|---|
| `v1.0.0` ~ `v3.2.2` | Flask + Jinja 单体,23 个版本迭代(见 Git 历史) |
| `v4.0.0` ~ `v4.2.0` | React 实验版(已归档到 `v4-react-archive` 分支) |
| **`v5.0.0`** | **当前:React SPA + FastAPI 重构** |

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
