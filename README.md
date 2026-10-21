# 我的小窝 · 至尊杰的个人主页

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)

青春贴纸风的学生个人主页,纯 HTML / CSS / JavaScript 手搓,零框架零依赖。

> 🏫 燕京理工学院 · 计算机科学与技术 2026 级
> 🏎️ 正在沉迷智能车 AI · 状态:learning and building

## 预览

直接双击 `index.html` 用浏览器打开即可,或者访问 GitHub Pages(如果已开启)。
(联网时会自动加载可爱的标题字体;断网也能正常看,只是标题字体会退化成系统字体。)

页面包含:首屏拍立得卡片、不正经数据统计、弹幕跑马灯、技能树 + 技能背包、
小破项目墙、校园时间线、微信扫码弹窗,全部响应式适配手机 / 平板 / 电脑。

## 文件结构

```
my-portfolio/
├── index.html            ← 网页内容(所有文字都在这里)
├── css/
│   └── style.css         ← 全部样式(颜色、布局、动画)
├── js/
│   └── main.js           ← 交互脚本(滚动动画、二维码弹窗、菜单)
└── assets/
    └── wechat-qr.jpg     ← 微信二维码(点「微信」按钮弹出)
```

## 想改内容去哪改

| 想改什么 | 去哪里改 |
|---|---|
| 名字、简介等所有文字 | `index.html` |
| 配色 | `css/style.css` 顶部 `:root` 里的颜色变量 |
| 技能熟练度 | `index.html` 里 `--w:78%` 这些样式变量 |
| 统计数字 | `index.html` 里 `data-count="999"` 这些属性 |
| 微信二维码 | 替换 `assets/wechat-qr.jpg`(保持文件名不变最省事) |

## 部署到 GitHub Pages(可选)

1. 把仓库推送到 GitHub 后,进入仓库 **Settings → Pages**
2. Source 选择 `main` 分支 / root,保存
3. 稍等片刻,`https://sheephearttidy.github.io/mysite/` 就能访问了

## 小提示

- 手机 / 平板 / 电脑都自适应,可以拖动浏览器窗口宽度试试效果
- 所有交互都是原生 JavaScript,没有引入任何库
- 如果不希望二维码进仓库,把 `assets/wechat-qr.jpg` 加进 `.gitignore` 并删除弹窗模块即可

---

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
