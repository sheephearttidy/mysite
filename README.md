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
| `v1.2.1` | 后台改为左侧边栏布局:4 组多级导航(内容/个人信息/媒体/维护)、9 个面板切换、数量角标、分组折叠、移动端抽屉、记住上次位置 |
| `v1.3.0` | 分享卡片 + SEO 基础(og 标签/favicon/robots/sitemap/JSON-LD);自建访问统计 + 后台数据看板 |
| `v1.4.0` | 登录图形验证码(纯标准库 SVG、一次性、答案哈希存储);安全设置面板全面扩充(7 项可调参数、封锁 IP 管理、会话踢下线、15 类操作审计、应急解锁工具);移除简历 PDF 下载功能 |

## 预览

- 线上地址:<https://imyxj.xyz>
- 后台入口:<https://imyxj.xyz/admin>(输密码进入)
- 本地看前台:直接双击 `index.html` 即可,动态内容会静默回退,页面照常显示
- 本地跑后台:`cd admin && python -m venv venv && venv\Scripts\pip install -r requirements.txt && venv\Scripts\python app.py`,然后访问 <http://127.0.0.1:5100/admin>

## 文件结构

```
my-portfolio/
├── index.html            ← 前台页面(同时是动态内容的离线兜底)
├── robots.txt            ← 搜索引擎规则(禁收录 /admin 和 /api)
├── sitemap.xml           ← 站点地图
├── css/
│   └── style.css         ← 前台全部样式
├── js/
│   └── main.js           ← 前台交互 + 拉内容 + 访问上报
├── assets/
│   ├── wechat-qr.jpg     ← 微信二维码
│   ├── favicon.svg       ← 站点图标
│   ├── og-image.png      ← 分享卡片图(1200×630)
│   ├── apple-touch-icon.png
│   └── uploads/          ← 后台传的图片(gitignore,线上自动创建)
└── admin/                ← 后台管理系统(Flask + SQLite)
    ├── app.py            ← 路由 / API / 登录 / 改密码 / 上传 / 备份 / 统计 / 安全
    ├── db.py             ← 建表 + 初始数据 + 增删改查 + 密码哈希 + 导入导出 + 统计 + 安全
    ├── captcha.py        ← 图形验证码生成(纯标准库 SVG,零依赖)
    ├── unlock.py         ← 安全应急工具(SSH 里解锁 IP / 踢会话 / 关验证码)
    ├── gen_pass.py       ← 生成密码哈希的小工具(备用)
    ├── requirements.txt
    ├── templates/
    │   ├── login.html    ← 后台登录页(密码 + 验证码)
    │   └── admin.html    ← 后台管理页(侧边栏 + 10 个面板)
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
| 📊 数据看板 | —— | 访问量趋势、来源、浏览器/系统、活跃时段、最近访问 |
| 💾 数据备份 | —— | 一键导出 JSON / 从 JSON 恢复 / 清空并恢复 |

改完保存,前台刷新即可生效(前台加载的是 `/api/content` 接口)。

## 分享卡片与 SEO

发到微信 / QQ / 群里的链接会显示标题、描述和预览图,不再是光秃秃的网址。

| 文件 | 作用 |
|---|---|
| `assets/og-image.png` | 分享预览图(1200×630),想换就重新生成同名文件 |
| `assets/favicon.svg` | 浏览器标签页图标 |
| `robots.txt` | 允许收录首页,禁止收录 `/admin` 和 `/api` |
| `sitemap.xml` | 站点地图,提交给搜索引擎 |

`index.html` 头部有完整的 `og:*`、`twitter:*` 和 JSON-LD 结构化数据。

## 访问统计

自建轻量统计,不引第三方(没有 Google Analytics,不涉及隐私外传)。

- 前台打开首页时用 `sendBeacon` 上报一次,**同一标签页会话只报一次**(刷新不刷量)
- 只记录首页访问,其他路径一律拒收,防止被扫描器刷爆数据库
- 自动识别并过滤爬虫(Googlebot、curl、python-requests 等)
- 来源只留域名,站内跳转不算外部来源
- 后台「📊 数据看板」看:今天/区间/累计访问、每日趋势、来源排行、浏览器系统占比、24 小时活跃分布、最近 20 条明细

想清空统计:`sqlite3 admin/data/mysite.db "DELETE FROM visits;"`

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
- 改完密码会强制退出重新登录;之后随时点后台「🔐 安全设置 → 修改密码」再改
- 密码以 PBKDF2(120k 迭代)哈希存在数据库 settings 表里,明文不落盘

## 登录验证码

登录页除密码外还要输图形验证码。

- **纯标准库 SVG 生成**,不依赖 Pillow、不依赖字体文件,服务器上零额外安装
- 4 位字符,**去掉了容易看错的 `0O1lI2Z5S8B`**,只剩 `ACDEFGHJKLMNPQRTUVWXY34679`
- 每个字符随机旋转 ±22°、上下偏移、字号粗细变化,再叠 4 条贝塞尔干扰线 + 26 个噪点
- **答案不存明文**:session 里只存 `sha256("cap:" + 大写答案)`,数据库泄露也反推不出来
- **一次性**:不管输对输错,校验完立刻从 session 删掉,不能复用
- **3 分钟过期**,超时提示刷新
- 点图片换一张,响应头 `Cache-Control: no-store`,不会被浏览器缓存住
- 可在后台「安全设置」里关闭或调位数(3~6 位)

## 安全设置面板

后台「⚙️ 站点维护 → 🔐 安全设置」,一屏管完所有安全项。

**顶部四张状态卡**:验证码状态 / 24 小时登录失败次数 / 封锁中 IP 数 / 活跃会话数,
数量异常时卡片自动变黄或变红。

**可调参数**(全部有范围校验,非法值直接 400):

| 设置 | 默认 | 范围 | 作用 |
|---|---|---|---|
| 登录验证码 | 开 | 开/关 | 关掉后只验密码 |
| 验证码位数 | 4 | 3~6 | 越长越难认 |
| 失败几次后封锁 | 5 | 1~50 | 达到次数临时禁登 |
| 封锁时长 | 15 分钟 | 1~1440 | 期间该 IP 无法登录 |
| 空闲自动登出 | 60 分钟 | 0~1440 | 0 = 不自动登出 |
| 会话有效期 | 168 小时 | 1~720 | 超时重新登录 |
| 审计日志保留 | 500 条 | 50~5000 | 面板显示上限 |

**封锁中的 IP**:实时倒计时 + 一键解除。

**登录会话**:列出 IP、设备、登录时间、最后活动时间,当前会话带绿色标记。
可以单个「踢下线」,也可以「踢掉其他所有会话」——改完密码后建议点一下。

**操作审计日志**:记录登录成功/失败/触发封锁/封锁期尝试/退出/改密码/改安全设置/
踢会话/解除封锁/上传图片/删图片/导入/导出/清空日志/空闲登出,共 15 类动作,
带时间、IP、详情。可刷新可清空(清空本身也会被记录)。

### 应急:把自己锁在门外了怎么办

如果输错太多次把自己 IP 封了,SSH 上去跑:

```bash
cd /var/www/mysite/admin
venv/bin/python unlock.py              # 看当前封了哪些 IP
venv/bin/python unlock.py --all        # 全部解除
venv/bin/python unlock.py 1.2.3.4      # 解除指定 IP
venv/bin/python unlock.py --sessions   # 看登录会话
venv/bin/python unlock.py --kill-all   # 踢掉所有会话
venv/bin/python unlock.py --captcha off  # 临时关验证码(应急)
venv/bin/python unlock.py --audit 30   # 看最近 30 条审计
```

## 安全加固

| 层面 | 措施 |
|---|---|
| 登录防爆破 | **图形验证码**(一次性、3 分钟过期、答案哈希存储);nginx 层 `limit_req` 限速(登录 10 次/分钟、验证码 30 次/分钟,基于真实 TCP 源,`X-Forwarded-For` 改为 `$remote_addr` **覆盖**,伪造无效);应用层失败次数**落库**(重启不丢),达阈值自动封锁 IP |
| 会话安全 | 登录成功 `session.clear()` 防会话固定;会话登记入库,支持远程踢下线;空闲超时自动登出;`Secure` + `HttpOnly` + `SameSite=Lax` |
| 审计留痕 | 15 类敏感操作全部记入 `audit` 表,后台可视、可清空,应急工具也能查 |
| 运行权限 | 后台以专用系统用户 `mysite` 运行(非 root);`data/` 750、数据库 640、`/etc/mysite-admin.env` 640 root:mysite |
| 传输安全 | 全站 HTTPS,HSTS 一年 |
| 响应头 | `X-Content-Type-Options` / `X-Frame-Options` / `Referrer-Policy` / `Permissions-Policy`;`server_tokens off` 隐藏版本 |
| 输入防护 | 请求体上限 64KB;`escAttr()` 对属性值额外转义引号,防属性逃逸 XSS;安全设置项全部做范围与类型校验 |
| 上传防护 | 校验真实文件头(magic bytes),扩展名与真实类型不符以真实类型为准,防改扩展名 webshell |
| 资源隔离 | 隐藏文件(`.git`/`.env`)与 `.db/.sql/.py/.bak` 一律 403;数据库和源码不在 webroot 可访问路径 |
| SSH | 仅公钥登录(`PasswordAuthentication no`),root 仅密钥(`prohibit-password`),`MaxAuthTries 3` |
| 备份 | 每次部署前自动备份 nginx / app.py / db.py / admin.html / 数据库到 `/root/*.bak.<时间戳>` |

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
