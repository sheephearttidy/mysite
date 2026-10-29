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

### 3. 初始化数据库(首次必须)

```bash
cd backend
python seed.py
```

这一步会建表、灌示例内容、并把后台密码设为 `admin`(同时标记「下次登录必须改密」)。

常用参数:

```bash
python seed.py --reset-password    # 忘记密码时重置回 admin
python seed.py --password 新密码    # 设为指定密码
python seed.py --no-seed           # 只建表与默认设置,不灌示例内容
python seed.py --db 路径            # 指定数据库文件
```

脚本是幂等的:重复执行不会重复插入内容,也不会覆盖已有密码。

### 4. 登录后台

访问 <http://127.0.0.1:5173/admin.html>,初始密码 `admin`。

**首次登录会强制跳到改密页**——新密码至少 8 位、含至少 2 类字符,改完才能进后台。
这是后端强制的:未改密时所有后台接口返回 `403 MUST_CHANGE_PASSWORD`,
绕过前端直接调接口也一样被拒。

### 5. 生产构建

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
│   ├── core/       config · db · security · deps · keys
│   ├── models/     22 张表的 ORM 模型
│   ├── schemas/    Pydantic 请求/响应模型
│   ├── services/   content · site
│   ├── api/        content · interact · stats · auth · admin
│   └── main.py     应用入口
├── scripts/        冒烟与回归测试
├── seed.py         建库 / 灌数据 / 重置密码
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
| `GradientText` | Gradient Text | 流动渐变文字(站名) |
| `TextType` | Text Type | 打字机效果(副标题轮播) |
| `ShinyText` | Shiny Text | 高光扫过文字 |
| `Particles` | Particles | canvas 漂浮粒子背景 |
| `GridBackground` | Cursor Grid | 光标聚光网格底纹 |
| `Meteors` | Meteors | 流星划过背景 |

均为纯 CSS / canvas 实现,零运行时依赖,全部尊重 `prefers-reduced-motion`。

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

**强制改密在后端拦截。** 首次登录(或重置密码后)`must_change_pass=1`,此时所有走 `require_admin` 的后台接口返回 `403 {"code":"MUST_CHANGE_PASSWORD"}`。`/api/me` 和 `/api/password` 走 `require_login`,不受拦截——否则用户连改密页都进不去,会把自己锁死。前端跳转只是体验,真正兜底的是接口。

**settings 键名必须与历史库一致。** 密码存 `pass_hash`、改密标记存 `must_change_pass`、验证码开关存 `sec_captcha`。这些键由旧 Flask 版本写入,新代码若改名就会「读不到密码 → 永远登录失败」。所有键集中定义在 `core/keys.py`。

**输入严格,输出宽松。** 写入时 Pydantic 完整校验(长度、范围、枚举),脏数据进不来;读取时只约束类型不约束范围。历史库里存着 `percent=99999` 这类越界值时,页面照常渲染,不会整页 500。

**新增内容类型只需两处注册。** 在 `services/content.py` 的 `REGISTRY` 和 `api/content.py` 的 `SCHEMAS` 各加一行,CRUD 路由自动生效。

**SPA 深链回退。** nginx `try_files $uri /index.html`,FastAPI 也做了带路径穿越防护的兜底,`/about` 这类前端路由不会 404。

**SQLite 路径在 Windows 上要转 POSIX。** `sqlite:///` + `Path.as_posix()`,反斜杠直接拼进 URL 会被当转义序列,报 `unable to open database file`。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MYSITE_DB_PATH` | `admin/data/mysite.db` | SQLite 路径 |
| `MYSITE_SECRET_KEY` | 开发占位 | 会话密钥,**线上必须设置** |
| `MYSITE_COOKIE_SECURE` | `true` | 本地 HTTP 调试设为 `0` |
| `MYSITE_UPLOAD_DIR` | `assets/uploads` | 上传目录 |
| `MYSITE_FRONTEND_DIST` | `frontend/dist` | 前端产物目录 |
| `MYSITE_SITE_ORIGIN` | `https://imyxj.xyz` | 站点源 |
| `MYSITE_EMIT_SECURITY_HEADERS` | `false` | 安全响应头由 nginx 下发;仅本地直连调试设 `1` |

## 安全模型

**CSRF 防护。** 后台写操作(POST/PUT/DELETE)要求 Origin 主机名与请求 Host 一致,跨站或无 Origin 的请求一律 403。公开互动接口(留言/提问/点赞/上报)不校验 Origin——它们只接受 `application/json` 请求体,浏览器跨站表单伪造不出这个 Content-Type,再叠加限流防护。

**CSP。** `script-src 'self'` 严格策略,所有脚本外链(包括防闪烁的 `theme-init.js`)。React 的内联样式靠 `style-src 'unsafe-inline'` 放行。上线后浏览器控制台零违规。

**响应头职责划分。** HTML 由 nginx 直出、不经过 FastAPI,所以安全头(CSP/nosniff/X-Frame-Options 等)由 nginx 在每个 location 统一下发(`deploy/nginx/mysite-headers.conf`);FastAPI 侧的中间件默认关闭(`MYSITE_EMIT_SECURITY_HEADERS`),避免重复头——浏览器虽取更严格的值,但重复头不规范。

**会话。** Cookie 仅存随机会话指纹,`HttpOnly + SameSite=Lax + Secure`,库里可撤销(支持踢下线);登录成功换新 sid 防会话固定;空闲超时、绝对有效期、可选 IP 绑定三重约束。

**上传。** 按真实文件头(magic bytes)识别类型,扩展名与内容不符以内容为准,拒绝 PHP/JSP 等 webshell。

## 测试

```bash
# 后端(需先启动服务)
python backend/scripts/smoke.py http://127.0.0.1:5100         # 43 项公开接口
python backend/scripts/test_auth_crud.py                       # 22 项认证 + CRUD
python backend/scripts/browser_check.py http://127.0.0.1:5100  # 9 页真实渲染
python backend/scripts/admin_check.py                          # 17 项后台
python backend/scripts/test_force_password.py                  # 25 项强制改密
python backend/scripts/test_admin_ui.py                        # 17 项后台界面
```

审计脚本(全量检查用,部分需先启动服务):

```bash
python backend/scripts/audit_permissions.py http://127.0.0.1:5100  # 41 项权限矩阵
python backend/scripts/audit_actions.py                            # 27 项管理写操作
python backend/scripts/audit_visual.py http://127.0.0.1:5100       # 34 项视觉/CSP
python backend/scripts/audit_security.py                           # 54 项安全攻击面
python backend/scripts/test_csrf_matrix.py                         # 11 项同源判定
python backend/scripts/audit_worldmap.py http://127.0.0.1:5100     # 9 项世界地图
python backend/scripts/audit_projection.py                         # 10 项投影校验
python backend/scripts/audit_schema.py 数据库路径                    # 表结构一致性
python backend/scripts/audit_docs.py                               # 文档真实性
python backend/scripts/audit_deploy.py                             # 本地 vs 线上
python backend/scripts/verify_prod_v52.py                          # 线上终验(页面/安全头/世界地图)
```

部分脚本需要指定测试库与服务地址,避免污染开发数据:

```bash
# Windows PowerShell
$env:SMOKE_DB='D:\tmp\test.db'      # test_auth_crud.py / admin_check.py
$env:TEST_DB='D:\tmp\test.db'       # test_force_password.py / audit_actions.py
$env:TEST_ORIGIN='http://127.0.0.1:5100'   # CSRF 同源校验用
$env:SMOKE_BASE='http://127.0.0.1:5100'
$env:TEST_BASE='http://127.0.0.1:5100'
```

## 版本

| 版本 | 说明 |
|---|---|
| `v1.0.0` ~ `v3.2.2` | Flask + Jinja 单体(见 Git 历史) |
| `v4.0.0` ~ `v4.2.0` | React 实验版(归档于 `v4-react-archive` 分支) |
| `v5.0.0` | React SPA + FastAPI 重构 |
| `v5.1.0` | 样式体系补全 + 动态组件 + 强制改密 |
| **`v5.2.0`** | **当前:真实世界地图 + CSRF/CSP/安全响应头加固** |

旧版可通过 `git checkout v3.2.2-pre-react-refactor` 找回。

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
