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
└── admin/                ← 后台管理系统(Flask + SQLite)
    ├── app.py            ← 路由 / API / 登录
    ├── db.py             ← 建表 + 初始数据 + 增删改查
    ├── gen_pass.py       ← 生成管理员密码哈希的小工具
    ├── requirements.txt
    ├── templates/
    │   ├── login.html    ← 后台登录页
    │   └── admin.html    ← 后台管理页(增删改都在这)
    └── data/mysite.db    ← SQLite 数据库(gitignore,首次启动自动生成)
```

## 后台能管什么

| 板块 | 对应前台 | 字段 |
|---|---|---|
| 🎯 技能树 | 「技能树」两列技能条 | 名称、熟练度%、吐槽、分类(认真/被动)、颜色、排序 |
| 🗺️ 校园日常 | 「校园打怪升级记录」时间线 | emoji、时间、标题、描述、排序 |
| 🧮 趣味统计 | 首屏「不正经数据统计」 | emoji、数字、单位、说明、排序 |

改完保存,前台刷新即可生效(前台加载的是 `/api/content` 接口)。

## 想改内容去哪改

| 想改什么 | 去哪里改 |
|---|---|
| 名字、简介、项目墙、联系方式 | `index.html`(或上后台改可管理板块) |
| 技能 / 时间线 / 统计 | 后台 <https://imyxj.xyz/admin> 在线改 |
| 配色 | `css/style.css` 顶部 `:root` 里的颜色变量 |
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

部署时通过环境变量注入,不进代码不进仓库:

```bash
cd admin && python gen_pass.py "你的密码"
# 输出 pbkdf2:120000:xxxx:yyyy 写进 /etc/mysite-admin.env 的 MYSITE_ADMIN_PASS_HASH
```

连续输错 8 次会封 IP 10 分钟,所以别乱试我的密码 😏

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
