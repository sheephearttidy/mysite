# 我的小窝 · 至尊杰的个人主页

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)

青春贴纸风的学生个人主页,前台纯 HTML / CSS / JavaScript 手搓,零框架零依赖;
后台是一个 Flask + SQLite 的轻量管理系统,改内容不用再碰代码。

> 🏫 燕京理工学院 · 计算机科学与技术 2026 级
> 🏎️ 正在沉迷智能车 AI · 状态:learning and building

## 版本

| 版本 | 说明 |
|---|---|
| `v1.0.0` | 纯静态贴纸风主页(全内容写死在 HTML 里) |
| `v1.1.0` | 新增后台管理系统:技能树 / 校园日常 / 趣味统计可在线编辑,前台动态加载(后台挂了自动回退到内置内容) |
| `v1.1.1` | 后台密码机制升级:初始密码 `admin`,首次登录自动弹窗强制引导修改;右上角「🔑 改密码」随时可改;密码哈希从环境变量迁移进数据库 |
| `v1.1.2` | 安全加固:修复登录限速伪造绕过、后台降权运行、安全响应头、Cookie Secure、请求体限制、SSH 仅公钥 |
| `v1.2.0` | 内容补全:项目墙 / 关于我 / 信息卡片进后台;图片上传(校验真实文件类型);数据导出导入;前台深色模式 |

## 预览

- 线上地址:<https://imyxj.xyz>
- 后台入口:<https://imyxj.xyz/admin>(输密码进入)
- 本地看前台:直接双击 `index.html` 即可,动态内容会静默回退,页面照常显示
- 本地跑后台:`cd admin && python -m venv venv && venv\Scripts\pip install -r requirements.txt && venv\Scripts\python app.py`,然后访问 <http://127.0.0.1:5100/admin>

## 文件结构

```
my-portfolio/
├── index.html            ← 前台页面(同时是动态内容的离线兜底)
├── css/
│   └── style.css         ← 前台全部样式
├── js/
│   └── main.js           ← 前台交互 + 从后台拉内容(失败自动回退)
├── assets/
│   └── wechat-qr.jpg     ← 微信二维码
│   └── uploads/          ← 后台传的图片(gitignore,线上自动创建)
└── admin/                ← 后台管理系统(Flask + SQLite)
    ├── app.py            ← 路由 / API / 登录 / 改密码 / 上传 / 备份
    ├── db.py             ← 建表 + 初始数据 + 增删改查 + 密码哈希 + 导入导出
    ├── gen_pass.py       ← 生成密码哈希的小工具(备用)
    ├── requirements.txt
    ├── templates/
    │   ├── login.html    ← 后台登录页(初始密码提示在这里)
    │   └── admin.html    ← 后台管理页(增删改 + 改密码 + 上传 + 备份)
    └── data/mysite.db    ← SQLite 数据库(gitignore,首次启动自动生成,初始密码 admin)
```

## 后台能管什么

| 板块 | 对应前台 | 字段 |
|---|---|---|
| 🎯 技能树 | 「技能树」两列技能条 | 名称、熟练度%、吐槽、分类(认真/被动)、颜色、排序 |
| 🗺️ 校园日常 | 「校园打怪升级记录」时间线 | emoji、时间、标题、描述、排序 |
| 🧮 趣味统计 | 首屏「不正经数据统计」 | emoji、数字、单位、说明、排序 |
| 🛠️ 项目墙 | 「我的小破项目们」卡片墙 | emoji、封面底色、项目名、描述、状态标签、链接、排序 |
| 🧍 关于我 | 「关于我这只人类」段落 + 右侧信息卡片 | 类型(段落/卡片)、emoji、小标题、正文、排序 |
| 🖼️ 图片 | 全站图片素材 | 拖拽/点选上传,自动校验真实文件类型,可复制路径 |
| 💾 数据备份 | —— | 一键导出 JSON / 从 JSON 恢复 / 清空并恢复 |

改完保存,前台刷新即可生效(前台加载的是 `/api/content` 接口)。

## 深色模式

导航栏右侧 ☀️/🌙 按钮切换,偏好存在 `localStorage`。首次访问跟随系统设置。
配色通过 `[data-theme="dark"]` 覆盖 `:root` 变量实现,想调深色配色改 `style.css` 里那段即可。

## 想改内容去哪改

| 想改什么 | 去哪里改 |
|---|---|
| 技能 / 时间线 / 统计 / 项目墙 / 关于我 | 后台 <https://imyxj.xyz/admin> 在线改(推荐) |
| 图片素材 | 后台上传,或直接替换 `assets/` 里的文件 |
| 名字、首屏大字、跑马灯文案、联系方式按钮 | `index.html`(这几块没做进后台) |
| 配色 | `css/style.css` 顶部 `:root`(深色模式在同文件 `[data-theme="dark"]`) |
| 微信二维码 | 替换 `assets/wechat-qr.jpg`(保持文件名不变最省事) |

## 部署结构(线上)

```
浏览器 → Nginx(80/443, 证书 Let's Encrypt)
   ├── /            → /var/www/mysite 静态文件
   ├── /api/...     → 反代到 127.0.0.1:5100(Flask, gunicorn)
   └── /admin/...   → 同上
Flask 服务由 systemd 守护(mysite-admin.service),开机自启、挂了自动拉起
```

## 后台密码

- **初始密码是 `admin`**,第一次用 admin 登录后台会自动弹出改密码窗口,改完才算完事(改密码规则:至少 6 位、不能还是 `admin`、要输两遍确认)
- 没改初始密码期间:登录页会提示「首次使用初始密码 admin」,后台顶部挂黄色警示横幅
- 改完密码会强制退出重新登录;之后随时点后台右上角「🔑 改密码」再改
- 密码以 PBKDF2(120k 迭代)哈希存在数据库 settings 表里,明文不落盘
- 连续输错 8 次封 IP 10 分钟,所以别乱试我的密码 😏

## 安全加固(v1.1.2)

| 层面 | 措施 |
|---|---|
| 登录防爆破 | nginx 层 `limit_req` 限速(10 次/分钟/IP,基于真实 TCP 源,`X-Forwarded-For` 改为 `$remote_addr` **覆盖**,伪造无效);应用层再叠 8 次/10 分钟封锁 |
| 运行权限 | 后台以专用系统用户 `mysite` 运行(非 root);`data/` 750、数据库 640、`/etc/mysite-admin.env` 640 root:mysite |
| 传输安全 | 全站 HTTPS,HSTS 一年;Session Cookie 带 `Secure` + `HttpOnly` + `SameSite=Lax` |
| 响应头 | `X-Content-Type-Options` / `X-Frame-Options` / `Referrer-Policy` / `Permissions-Policy`;`server_tokens off` 隐藏版本 |
| 输入防护 | 请求体上限 64KB;`escAttr()` 对属性值额外转义引号,防属性逃逸 XSS |
| 资源隔离 | 隐藏文件(`.git`/`.env`)与 `.db/.sql/.py/.bak` 一律 403;数据库和源码不在 webroot 可访问路径 |
| SSH | 仅公钥登录(`PasswordAuthentication no`),root 仅密钥(`prohibit-password`),`MaxAuthTries 3` |
| 备份 | 加固前的 nginx / app.py / sshd_config / env 均备份在服务器 `/root/*.bak.*` |

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
