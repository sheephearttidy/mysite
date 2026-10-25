# ============================================================
# 数据库层:SQLite + 初始数据
# 所有函数线程安全(每次调用独立连接)
# ============================================================

import os
import time
import sqlite3
import hashlib
from contextlib import contextmanager

DB_PATH = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,           -- 技能名,如 "🐍 Python"
    percent INTEGER NOT NULL DEFAULT 50,
    note TEXT DEFAULT '',         -- 下方吐槽小字
    category TEXT NOT NULL DEFAULT 'serious',  -- serious / passive
    color TEXT NOT NULL DEFAULT 'teal',        -- f-teal / f-pink / ...
    sort INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emoji TEXT NOT NULL DEFAULT '🚀',
    time_label TEXT NOT NULL,     -- 如 "2026.09" / "现在"
    title TEXT NOT NULL,
    content TEXT DEFAULT '',
    sort INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emoji TEXT NOT NULL DEFAULT '😄',
    number INTEGER NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL,
    sort INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emoji TEXT NOT NULL DEFAULT '🛠️',
    cover TEXT NOT NULL DEFAULT 'pink',   -- 封面底色 key: pink/yellow/teal/purple/orange/blue
    title TEXT NOT NULL,
    desc TEXT DEFAULT '',
    pill TEXT DEFAULT '进行中',            -- 状态小标签
    link TEXT DEFAULT '',                  -- 外部链接,空则不显示
    sort INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL DEFAULT 'info',     -- about(自我介绍段落) / info(信息卡片)
    emoji TEXT DEFAULT '',
    label TEXT DEFAULT '',                 -- about: 小标题; info: 卡片标题
    value TEXT DEFAULT '',                 -- about: 正文; info: 卡片内容
    sort INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 访问统计:每次页面访问记一条
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,              -- YYYY-MM-DD(按服务器本地时区)
    ts INTEGER NOT NULL,            -- unix 时间戳
    path TEXT NOT NULL DEFAULT '/', -- 访问路径
    referer TEXT DEFAULT '',        -- 来源域名(已裁剪)
    ua TEXT DEFAULT '',             -- 简化的浏览器/系统标签
    is_bot INTEGER NOT NULL DEFAULT 0,
    city TEXT DEFAULT '',           -- 访客城市(如 "江苏 南京"),隐私起见不存 IP
    is_new INTEGER DEFAULT 1,       -- v1.10:1=新访客 0=回访(前端 localStorage 匿名标识)
    dur_s INTEGER DEFAULT 0         -- v1.10:本页停留秒数(visibility 心跳,无 cookie)
);
CREATE INDEX IF NOT EXISTS idx_visits_day ON visits(day);
CREATE INDEX IF NOT EXISTS idx_visits_ts  ON visits(ts);

-- 登录失败记录(落库版,重启不丢)
CREATE TABLE IF NOT EXISTS login_fails (
    ip TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    blocked_until INTEGER NOT NULL DEFAULT 0,
    last_ts INTEGER NOT NULL DEFAULT 0
);

-- 操作审计日志
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    ip TEXT DEFAULT '',
    action TEXT NOT NULL,           -- login_ok / login_fail / captcha_fail / ...
    detail TEXT DEFAULT '',
    ua TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit(ts);

-- 登录会话(可远程踢下线)
CREATE TABLE IF NOT EXISTS sessions (
    sid TEXT PRIMARY KEY,           -- 会话指纹(随机串,不存 cookie 原文)
    ip TEXT DEFAULT '',
    ua TEXT DEFAULT '',
    created INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);

-- 留言板(前台公开写,后台审核后展示)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT '匿名',     -- 昵称(不超 20 字)
    body TEXT NOT NULL,                    -- 留言内容(不超 140 字)
    color TEXT DEFAULT 'pink',             -- 贴纸颜色键(后台不用管,前端给随机)
    ts INTEGER NOT NULL,                   -- 发布时间戳
    ip TEXT DEFAULT '',                    -- 仅后台可见(风控用)
    shown INTEGER NOT NULL DEFAULT 0,      -- 0=待审核 1=展示中 2=已隐藏
    reply TEXT DEFAULT '',                 -- 站长回复(可空,v2.7起作为首条 owner 线程的兼容字段)
    token TEXT DEFAULT ''                  -- v2.7.0:访客凭证,只有原留言人能继续追问
);
CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);

-- v2.7.0:留言对话线程(留言 -> 站主回复 -> 访客追问 -> 站主再回复)
CREATE TABLE IF NOT EXISTS message_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id INTEGER NOT NULL,               -- 关联 messages.id
    role TEXT NOT NULL DEFAULT 'guest',    -- owner=站主 / guest=访客追问
    body TEXT NOT NULL,                    -- 内容(不超 140 字)
    ts INTEGER NOT NULL,                   -- 发送时间戳
    ip TEXT DEFAULT '',                    -- 仅后台可见
    shown INTEGER NOT NULL DEFAULT 1       -- 1=公开 0=待审核(访客追问默认待审)
);
CREATE INDEX IF NOT EXISTS idx_mthread_msg ON message_threads(msg_id, ts);

-- v3.0.0:相册(图片元数据;图片文件本身仍在 assets/uploads/ 下)
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file TEXT NOT NULL,                    -- 文件名(assets/uploads/ 下)
    title TEXT DEFAULT '',                 -- 标题(可空)
    desc TEXT DEFAULT '',                  -- 描述/拍摄故事
    category TEXT DEFAULT '',              -- 分类(旅行/校园/日常…)
    shot_at TEXT DEFAULT '',               -- 拍摄日期 YYYY-MM-DD(可空)
    width INTEGER DEFAULT 0,               -- 像素宽(灯箱算比例用)
    height INTEGER DEFAULT 0,              -- 像素高
    shown INTEGER NOT NULL DEFAULT 1,      -- 1=公开 0=隐藏
    sort INTEGER NOT NULL DEFAULT 0,       -- 排序(小的在前)
    ts INTEGER NOT NULL DEFAULT 0          -- 加入时间
);
CREATE INDEX IF NOT EXISTS idx_photos_sort ON photos(sort, ts);
CREATE INDEX IF NOT EXISTS idx_photos_cat ON photos(category);

-- 点赞(按页面计数,无 cookie 无 IP,纯计数)
CREATE TABLE IF NOT EXISTS likes (
    page TEXT PRIMARY KEY,
    n INTEGER NOT NULL DEFAULT 0
);

-- 站点公告(后台发,前台顶部横幅,可开关)
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body TEXT NOT NULL,               -- 公告内容(不超 100 字)
    ts INTEGER NOT NULL,              -- 发布时间
    active INTEGER NOT NULL DEFAULT 1  -- 1=前台显示 0=下架
);

-- 倒计时(后台配置,前台挂角标;active=1 的最近一个展示)
CREATE TABLE IF NOT EXISTS countdowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,              -- 事件名,如「蓝桥杯」
    target TEXT NOT NULL,             -- 目标日期 YYYY-MM-DD
    emoji TEXT DEFAULT '⏳',
    active INTEGER NOT NULL DEFAULT 1
);

-- v2.2 荣誉墙(获奖/证书/成就,about 页展示)
CREATE TABLE IF NOT EXISTS honors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emoji TEXT NOT NULL DEFAULT '🏆',  -- 奖项图标
    year TEXT NOT NULL,                -- 年份/日期,如 "2025" / "2024.11"
    title TEXT NOT NULL,               -- 奖项名
    desc TEXT DEFAULT '',              -- 一句话说明(可空)
    level TEXT NOT NULL DEFAULT 'school', -- national/provincial/school/other
    sort INTEGER NOT NULL DEFAULT 0
);

-- v2.2 随手记(短想法/日志,campus 页展示)
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emoji TEXT NOT NULL DEFAULT '✏️',
    text TEXT NOT NULL,                -- 一句话(不超 80 字)
    mood TEXT DEFAULT 'teal',          -- 便签底色键 teal/pink/yellow/purple/blue/orange
    ts INTEGER NOT NULL,               -- 记录时间
    sort INTEGER NOT NULL DEFAULT 0
);

-- v2.2 友情链接(朋友们的站点,contact 页展示)
CREATE TABLE IF NOT EXISTS friendlinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- 站点名
    url TEXT NOT NULL,                 -- 链接
    emoji TEXT DEFAULT '🔗',
    desc TEXT DEFAULT '',              -- 一句话介绍(可空)
    sort INTEGER NOT NULL DEFAULT 0
);

-- v2.4 音乐(关于我页「最近在听」,官方外链 iframe 播放器)
-- 官方播放器只认数字 songid:https://i.y.qq.com/n2/m/outchain/player/index.html?songid=<数字id>
-- 后台允许贴分享链接(mid),app.py 会自动换成数字 id 再存这里。
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,               -- 歌名(自己填,展示用)
    artist TEXT DEFAULT '',            -- 歌手(可空)
    emoji TEXT DEFAULT '🎵',
    song_id TEXT NOT NULL,             -- QQ 音乐数字 songid(如 97773)
    note TEXT DEFAULT '',              -- 一句话安利(可空)
    sort INTEGER NOT NULL DEFAULT 0
);

-- v3.1.0 提问箱(访客匿名提问,站主回答后才公开)
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body TEXT NOT NULL,                -- 问题(不超 200 字)
    ts INTEGER NOT NULL,               -- 提问时间戳
    ip TEXT DEFAULT '',                -- 仅后台可见(风控用)
    shown INTEGER NOT NULL DEFAULT 0,  -- 0=待回答 1=已公开 2=已隐藏
    answer TEXT DEFAULT '',            -- 站主回答(不超 500 字,空=未答)
    answered_ts INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_questions_ts ON questions(ts);

-- v3.1.0 涂鸦墙(canvas 画完上传,默认待审核;文件在 assets/uploads/ 下)
CREATE TABLE IF NOT EXISTS doodles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file TEXT NOT NULL,                -- 文件名(assets/uploads/ 下)
    ts INTEGER NOT NULL,               -- 上传时间戳
    ip TEXT DEFAULT '',                -- 仅后台可见
    shown INTEGER NOT NULL DEFAULT 0,  -- 0=待审核 1=展示中 2=已隐藏
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_doodles_ts ON doodles(ts);
"""

# 首次建库时灌入的初始数据(与 v1.0.0 静态页一致)
SEED = {
    "skills": [
        ("🏎️ 智能车 / 嵌入式", 78, "主线任务,小车就是我的另一半", "serious", "teal", 1),
        ("🐍 Python", 75, "调车、调 AI、调 DeepSeek 都靠它", "serious", "blue", 2),
        ("⚙️ C / C++", 72, "写底层的感觉,又痛又上头", "serious", "pink", 3),
        ("🌐 全栈开发", 65, "Flask / Node.js / 前端三件套", "serious", "purple", 4),
        ("🍚 干饭", 100, "干饭不积极,思想有问题", "passive", "orange", 5),
        ("🌙 熬夜", 99, "留 1% 是怕妈妈看到这个网页", "passive", "purple", 6),
        ("🤖 调教 AI", 96, "DeepSeek 见了我都要喊声师傅", "passive", "teal", 7),
        ("🐌 拖延症", 90, "正在改,明天开始(真的)", "passive", "yellow", 8),
    ],
    "timeline": [
        ("🎒", "2026.09", "开学!踏入燕京理工",
         "计算机科学与技术 2026 级新生报到,从此笔记本里装的不只是游戏,还有 IDE。", 1),
        ("💻", "第一学期", "Hello World 启动",
         "从 C 语言的 printf 开始,一路学到 C++ / Python,越学越觉得有意思。", 2),
        ("🏎️", "入坑", "一脚踏进智能车",
         "见到智能车的那一刻 DNA 动了:小车 + AI + 代码,这不就是我要搞的东西吗!", 3),
        ("🚀", "现在", "learning and building",
         "学算法、学系统设计、玩 AI 和 Agent,同时把这个网页搓了出来。持续施工中 🔨", 4),
    ],
    "stats": [
        ("🏁", 999, " 次", "小车跑过的圈数(含撞墙)", 1),
        ("🌙", 999, " 次", "熬夜次数(保守估计)", 2),
        ("💬", 1000, " 条", "调教 DeepSeek 的 prompt", 3),
        ("🍚", 100, " %", "干饭热情(从不迟到)", 4),
    ],
    "works": [
        ("🏎️", "pink", "智能车 · 主线任务",
         "正在攻关的核心项目:循迹、避障、PID 控制,目标是让它自己稳稳跑完赛道。",
         "进行中", "https://github.com/sheephearttidy", 1),
        ("🤖", "yellow", "AI / Agent 探索",
         "学习路线上的副本任务:折腾大模型、写 Agent,这个网页就有一部分是 AI 协作的产物。",
         "探索中", "https://github.com/sheephearttidy", 2),
        ("🌐", "teal", "全栈小项目",
         "Flask / Node.js + 前端三件套练手,从接口到页面一手包办,顺便练 Docker 部署。",
         "练手作", "https://github.com/sheephearttidy", 3),
        ("💻", "purple", "GitHub 仓库",
         "所有公开代码都在 @sheephearttidy,欢迎来逛,点个 star 就是最大的鼓励。",
         "持续更新", "https://github.com/sheephearttidy", 4),
        ("📄", "orange", "这个网页本身",
         "纯 HTML/CSS/JS 手搓的青春贴纸风主页,分文件结构,算是一次小小的前端实战。",
         "你现在看着呢", "https://github.com/sheephearttidy", 5),
        ("🚧", "blue", "更多项目装修中",
         "位子先占上,等我做出更酷的东西就填进来。敬请期待(并不是敷衍)。",
         "敬请期待", "https://github.com/sheephearttidy", 6),
    ],
    "profile": [
        ("about", "", "是谁",
         "至尊杰,燕京理工学院计算机科学与技术 2026 级。每天在上课、写代码和调车之间反复横跳。", 1),
        ("about", "", "在干嘛",
         "主攻方向是智能车 AI——从循迹、避障到让小车自己学会跑圈。前后端也都有涉猎,坚信「能用代码解决的事就不算事」。", 2),
        ("about", "", "小目标",
         "让小车稳稳跑完全程不撞墙,顺便把 AI 和 Agent 玩明白,做出真正能跑起来、有人用的东西。", 3),
        ("info", "🎓", "专业", "计算机科学与技术", 1),
        ("info", "🏫", "学校", "燕京理工学院", 2),
        ("info", "🔥", "正在沉迷", "智能车 AI", 3),
        ("info", "⚡", "当前状态", "learning & building", 4),
    ],
    "honors": [
        ("🏎️", "2025", "全国大学生智能汽车竞赛", "第一次参赛,目标:跑完全程不撞墙", "provincial", 1),
        ("🏅", "2024", "校程序设计新生赛", "写代码的手感,是从这里开始的", "school", 2),
        ("🎖️", "2024", "院级优秀学生", "被认可的感觉,是继续卷的燃料", "school", 3),
    ],
    "notes": [
        ("🛠️", "今天给小车换了新的循迹算法,弯道终于不画龙了!", "teal", 0, 1),
        ("🌙", "凌晨的实验室和泡面更配,代码跑通那一刻什么都值了。", "purple", 0, 2),
        ("📚", "期末周生存指南:把「临时抱佛脚」拆成每天抱一点点。", "yellow", 0, 3),
    ],
    "friendlinks": [
        ("GitHub", "https://github.com/sheephearttidy", "🐙", "我的全部公开代码都在这里", 1),
        ("DeepSeek", "https://chat.deepseek.com", "🐋", "写代码与改 bug 的最佳搭子", 2),
    ],
    # v2.4 音乐(示例:周杰伦《晴天》mid,后台可改)
    "songs": [
        ("晴天", "周杰伦", "🌧️", "97773", "写代码循环曲第一名", 1),
    ],
}


# ---------------- 密码(PBKDF2) ----------------

def hash_password(pwd: str, iters: int = 120_000, salt: bytes | None = None) -> str:
    """返回 pbkdf2:iters:salt_hex:hash_hex"""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, iters)
    return f"pbkdf2:{iters}:{salt.hex()}:{digest.hex()}"


def verify_password(pwd: str, stored: str) -> bool:
    if not stored:
        return False
    parts = stored.split(":")
    if len(parts) != 4 or parts[0] != "pbkdf2":
        return False
    _, iters, salt_hex, hash_hex = parts
    try:
        calc = hashlib.pbkdf2_hmac("sha256", pwd.encode(), bytes.fromhex(salt_hex), int(iters))
        return calc.hex() == hash_hex
    except ValueError:
        return False


# ---------------- settings(key-value) ----------------

def get_setting(key: str, default=None):
    with get_db() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_db() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


# ---------------- v2.5 站点信息(前台可配置字段) ----------------
# 站点不是给一个人写死的:姓名/站名/学校/专业/年级/方向/标语/版权后缀
# 全部存进 settings 表,后台「站点信息」面板可改,前台各页动态套用。
# 表里没有时用这里的默认值(就是原来硬编码的内容),保证老站升级后不变样。

SITE_FIELDS = {
    "site_owner":       ("姓名",        "至尊杰"),
    "site_name":        ("站名",        "至尊杰的小窝"),
    "site_school":      ("学校",        "燕京理工学院"),
    "site_major":       ("专业",        "计算机科学与技术"),
    "site_grade":       ("年级",        "2026 级"),
    "site_focus":       ("方向/标签",   "智能车 AI"),
    "site_slogan":      ("标语",        "learning and building"),
    "site_credit":      ("版权后缀",    "纯手搓 + AI 协作"),
    "site_start_year":  ("建站年份",    "2026"),
}


def get_site():
    """返回全部站点信息(缺的用默认值补)"""
    with get_db() as c:
        rows = c.execute(
            "SELECT key, value FROM settings WHERE key LIKE 'site\\_%' ESCAPE '\\'"
        ).fetchall()
    saved = {r["key"]: r["value"] for r in rows}
    out = {}
    for key, (_label, default) in SITE_FIELDS.items():
        v = saved.get(key)
        out[key] = v if v not in (None, "") else default
    return out


def set_site(data: dict) -> dict:
    """批量保存站点信息,只接受白名单字段,空值回落默认"""
    with get_db() as c:
        for key, val in data.items():
            if key not in SITE_FIELDS:
                continue
            val = (val or "").strip()
            if not val:
                val = SITE_FIELDS[key][1]
            c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                      "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (key, val))
    return get_site()


def get_pass_hash() -> str | None:
    return get_setting("pass_hash")


def set_pass_hash(h: str):
    set_setting("pass_hash", h)


def must_change_password() -> bool:
    return get_setting("must_change_pass", "1") == "1"


def clear_must_change():
    set_setting("must_change_pass", "0")


# ---------------- 登录失败记录(落库) ----------------

def get_fail(ip: str) -> tuple[int, int]:
    """返回 (失败次数, 封锁截止时间戳)"""
    with get_db() as c:
        row = c.execute(
            "SELECT count, blocked_until FROM login_fails WHERE ip=?", (ip,)).fetchone()
        return (row["count"], row["blocked_until"]) if row else (0, 0)


def bump_fail(ip: str, threshold: int, block_seconds: int) -> tuple[int, int]:
    """失败次数 +1,达到阈值则封锁。返回新的 (次数, 封锁截止)"""
    now = int(time.time())
    cnt, blocked = get_fail(ip)
    cnt += 1
    if cnt >= threshold:
        blocked = now + block_seconds
        cnt = 0
    with get_db() as c:
        c.execute(
            """INSERT INTO login_fails(ip,count,blocked_until,last_ts) VALUES(?,?,?,?)
               ON CONFLICT(ip) DO UPDATE SET
                 count=excluded.count,
                 blocked_until=excluded.blocked_until,
                 last_ts=excluded.last_ts""",
            (ip, cnt, blocked, now))
    return cnt, blocked


def clear_fails(ip: str):
    with get_db() as c:
        c.execute("DELETE FROM login_fails WHERE ip=?", (ip,))


def list_blocked():
    """当前还在封锁中的 IP 列表"""
    now = int(time.time())
    with get_db() as c:
        rows = c.execute(
            "SELECT * FROM login_fails WHERE blocked_until > ? ORDER BY blocked_until DESC",
            (now,)).fetchall()
        return [dict(r) for r in rows]


def unblock(ip: str):
    with get_db() as c:
        cur = c.execute("DELETE FROM login_fails WHERE ip=?", (ip,))
        return cur.rowcount > 0


# ---------------- 审计日志 ----------------

def add_audit(action: str, ip: str = "", detail: str = "", ua: str = ""):
    with get_db() as c:
        c.execute(
            "INSERT INTO audit(ts,ip,action,detail,ua) VALUES(?,?,?,?,?)",
            (int(time.time()), ip[:64], action[:40], detail[:300], ua[:200]))


def list_audit(limit: int = 100):
    with get_db() as c:
        rows = c.execute(
            "SELECT * FROM audit ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def clear_audit(before_ts: int = None):
    with get_db() as c:
        if before_ts:
            cur = c.execute("DELETE FROM audit WHERE ts < ?", (before_ts,))
        else:
            cur = c.execute("DELETE FROM audit")
        return cur.rowcount


# ---------------- 会话管理 ----------------

def add_session(sid: str, ip: str, ua: str):
    now = int(time.time())
    with get_db() as c:
        c.execute(
            "INSERT OR REPLACE INTO sessions(sid,ip,ua,created,last_seen,revoked) "
            "VALUES(?,?,?,?,?,0)", (sid, ip[:64], ua[:200], now, now))


def touch_session(sid: str):
    with get_db() as c:
        c.execute("UPDATE sessions SET last_seen=? WHERE sid=?",
                  (int(time.time()), sid))


def session_revoked(sid: str) -> bool:
    """True 表示这个会话已被踢下线(或根本不存在)"""
    with get_db() as c:
        row = c.execute("SELECT revoked FROM sessions WHERE sid=?", (sid,)).fetchone()
        if not row:
            return True
        return row["revoked"] == 1


def revoke_session(sid: str):
    with get_db() as c:
        c.execute("UPDATE sessions SET revoked=1 WHERE sid=?", (sid,))


def revoke_all_sessions(keep_sid: str = None):
    with get_db() as c:
        if keep_sid:
            cur = c.execute("UPDATE sessions SET revoked=1 WHERE sid<>?", (keep_sid,))
        else:
            cur = c.execute("UPDATE sessions SET revoked=1")
        return cur.rowcount


def list_sessions():
    with get_db() as c:
        rows = c.execute(
            "SELECT * FROM sessions WHERE revoked=0 ORDER BY last_seen DESC").fetchall()
        return [dict(r) for r in rows]


def purge_old_sessions(days: int = 30):
    """清理很早以前的会话记录,避免表无限增长"""
    cutoff = int(time.time()) - days * 86400
    with get_db() as c:
        cur = c.execute("DELETE FROM sessions WHERE last_seen < ?", (cutoff,))
        return cur.rowcount


# ---------------- 安全设置项 ----------------

SEC_DEFAULTS = {
    "sec_captcha": "1",          # 登录验证码开关
    "sec_captcha_len": "4",      # 验证码位数
    "sec_fail_threshold": "5",   # 几次失败后封锁
    "sec_block_minutes": "15",   # 封锁时长(分钟)
    "sec_session_hours": "168",  # 会话有效期(小时)
    "sec_idle_minutes": "60",    # 空闲多久自动登出(分钟)
    "sec_audit_keep": "500",     # 审计日志保留条数
    # v2.3 新增:密码策略/失败时延/会话 IP 绑定
    "sec_pass_minlen": "8",      # 密码最小长度(6~64)
    "sec_pass_classes": "2",     # 至少几种字符(1~4)
    "sec_login_delay": "1",      # 登录失败时延(秒,0~10)
    "sec_bind_ip": "0",          # 会话绑定登录 IP(0/1)
}

# 前台特效设置(与安全设置分开,后台独立面板)
FX_DEFAULTS = {
    "fx_holiday_mode": "auto",   # auto=按日期自动 / manual=手动指定 / off=全关
    "fx_holiday_key": "",        # manual 模式下生效:节日 key
    "fx_effects": "1",           # 前台动效总开关(1 开 / 0 关)
    "pet_mode": "on",            # v3.1.0 小鲸鱼桌宠(on 开 / off 关)
}

HOLIDAY_KEYS = ("national-day", "valentine", "memorial", "new-year",
                "christmas", "labor", "children", "teacher")


def get_sec(key: str):
    return get_setting(key, SEC_DEFAULTS.get(key, ""))


def set_sec(key: str, value: str):
    set_setting(key, str(value))


def get_sec_all() -> dict:
    out = {}
    for k, d in SEC_DEFAULTS.items():
        out[k] = get_setting(k, d)
    return out


def get_fx(key: str):
    return get_setting(key, FX_DEFAULTS.get(key, ""))


def set_fx(key: str, value: str):
    set_setting(key, str(value))


def get_fx_all() -> dict:
    out = {}
    for k, d in FX_DEFAULTS.items():
        out[k] = get_setting(k, d)
    return out


# ---------------- 初始建库 ----------------

DEFAULT_ADMIN_PASS = "admin"  # 初始密码,首次登录会被要求修改


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path):
    global DB_PATH
    DB_PATH = path
    with get_db() as c:
        c.executescript(SCHEMA)
        # 旧库迁移:visits 表加 city 列(v1.7.0 访客地图)
        cols = [r["name"] for r in c.execute("PRAGMA table_info(visits)")]
        if "city" not in cols:
            c.execute("ALTER TABLE visits ADD COLUMN city TEXT DEFAULT ''")
        # v1.10.0:新老访客 + 停留时长
        if "is_new" not in cols:
            c.execute("ALTER TABLE visits ADD COLUMN is_new INTEGER DEFAULT 1")
        if "dur_s" not in cols:
            c.execute("ALTER TABLE visits ADD COLUMN dur_s INTEGER DEFAULT 0")
        if c.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO skills(name,percent,note,category,color,sort) VALUES(?,?,?,?,?,?)",
                SEED["skills"])
        if c.execute("SELECT COUNT(*) FROM timeline").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO timeline(emoji,time_label,title,content,sort) VALUES(?,?,?,?,?)",
                SEED["timeline"])
        if c.execute("SELECT COUNT(*) FROM stats").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO stats(emoji,number,unit,label,sort) VALUES(?,?,?,?,?)",
                SEED["stats"])
        if c.execute("SELECT COUNT(*) FROM works").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO works(emoji,cover,title,desc,pill,link,sort) VALUES(?,?,?,?,?,?,?)",
                SEED["works"])
        if c.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO profile(kind,emoji,label,value,sort) VALUES(?,?,?,?,?)",
                SEED["profile"])
        # v2.2 新表:建表即灌种子(旧库升级时这三张表是新建的,必然为空)
        if c.execute("SELECT COUNT(*) FROM honors").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO honors(emoji,year,title,desc,level,sort) VALUES(?,?,?,?,?,?)",
                SEED["honors"])
        if c.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO notes(emoji,text,mood,ts,sort) VALUES(?,?,?,?,?)",
                SEED["notes"])
        if c.execute("SELECT COUNT(*) FROM friendlinks").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO friendlinks(name,url,emoji,desc,sort) VALUES(?,?,?,?,?)",
                SEED["friendlinks"])
        # v2.7.0:留言对话线程
        # 1) messages 加 token 列(访客追问凭证)
        mcols = [r["name"] for r in c.execute("PRAGMA table_info(messages)")]
        if "token" not in mcols:
            c.execute("ALTER TABLE messages ADD COLUMN token TEXT DEFAULT ''")
        # 2) 老数据的站长回复(reply 字段)搬进 message_threads,只搬一次
        c.execute("""INSERT INTO message_threads(msg_id,role,body,ts,ip,shown)
                     SELECT m.id,'owner',m.reply,m.ts,'',1 FROM messages m
                     WHERE m.reply!='' AND NOT EXISTS(
                       SELECT 1 FROM message_threads t WHERE t.msg_id=m.id AND t.role='owner')""")
        # v2.4 音乐:旧库/中间版本的 songs 表可能用的是 song_mid,统一迁到 song_id
        # (官方外链播放器只认数字 songid,mid 喂进去是白屏)
        song_cols = [r["name"] for r in c.execute("PRAGMA table_info(songs)")]
        if "song_mid" in song_cols and "song_id" not in song_cols:
            c.execute("ALTER TABLE songs RENAME TO songs_old")
            c.execute("""CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL, artist TEXT DEFAULT '', emoji TEXT DEFAULT '🎵',
                song_id TEXT NOT NULL, note TEXT DEFAULT '', sort INTEGER NOT NULL DEFAULT 0
            )""")
            c.execute("""INSERT INTO songs(id,title,artist,emoji,song_id,note,sort)
                         SELECT id,title,artist,emoji,song_mid,note,sort FROM songs_old""")
            c.execute("DROP TABLE songs_old")
        if c.execute("SELECT COUNT(*) FROM songs").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO songs(title,artist,emoji,song_id,note,sort) VALUES(?,?,?,?,?,?)",
                SEED["songs"])
        # 初始密码 admin,标记必须修改
        if c.execute("SELECT COUNT(*) FROM settings WHERE key='pass_hash'").fetchone()[0] == 0:
            c.execute("INSERT INTO settings(key,value) VALUES('pass_hash',?)",
                      (hash_password(DEFAULT_ADMIN_PASS),))
            c.execute("INSERT INTO settings(key,value) VALUES('must_change_pass','1')")


# ---------------- 内容表 CRUD 工厂(v3.2.0) ----------------
# 9 类纯内容表(技能/时间线/统计/项目/关于我/荣誉/随手记/友链/音乐)共用
# 一套四件套语义。v3.2 之前是同一段代码复制 9 遍,现在每类只注册一份规格:
#   insert:item.get(字段, 默认);枚举非法回退默认;数字 int() 强转
#   update :只覆盖出现的字段;枚举非法忽略(保留原值);数字强转
#   get    :按 order 排序;delete:rowcount>0
# 特例都在规格里:notes 的 ts 缺省=现在(传 0/None 也取现在,旧行为)、
# 按 ts 倒序;honors/notes 有枚举校验,其余类不校验(skills 传啥存啥)。
# songs 的 QQ 链接解析在 app.py 路由层,这里就是普通四件套。
# 行为基线:tests/test_db.py(工厂化前后同一套必须全绿)。

HONOR_LEVELS = {"national": "国家级", "provincial": "省级", "school": "校级", "other": "其他"}
NOTE_MOODS = ("teal", "pink", "yellow", "purple", "blue", "orange")


def _now_ts():
    return int(time.time())


TABLE_SPECS = {
    "skills": {
        "fields": ("name", "percent", "note", "category", "color", "sort"),
        "defaults": {"name": "", "percent": 50, "note": "",
                     "category": "serious", "color": "teal", "sort": 99},
        "ints": ("percent", "sort"),
        "order": "category, sort, id",
    },
    "timeline": {
        "fields": ("emoji", "time_label", "title", "content", "sort"),
        "defaults": {"emoji": "🚀", "time_label": "", "title": "",
                     "content": "", "sort": 99},
        "ints": ("sort",),
        "order": "sort, id",
    },
    "stats": {
        "fields": ("emoji", "number", "unit", "label", "sort"),
        "defaults": {"emoji": "😄", "number": 0, "unit": "",
                     "label": "", "sort": 99},
        "ints": ("number", "sort"),
        "order": "sort, id",
    },
    "works": {
        "fields": ("emoji", "cover", "title", "desc", "pill", "link", "sort"),
        "defaults": {"emoji": "🛠️", "cover": "pink", "title": "", "desc": "",
                     "pill": "进行中", "link": "", "sort": 99},
        "ints": ("sort",),
        "order": "sort, id",
    },
    "profile": {
        "fields": ("kind", "emoji", "label", "value", "sort"),
        "defaults": {"kind": "info", "emoji": "", "label": "",
                     "value": "", "sort": 99},
        "ints": ("sort",),
        "order": "kind, sort, id",
    },
    "honors": {
        "fields": ("emoji", "year", "title", "desc", "level", "sort"),
        "defaults": {"emoji": "🏆", "year": "", "title": "", "desc": "",
                     "level": "school", "sort": 99},
        "enums": {"level": HONOR_LEVELS},
        "ints": ("sort",),
        "order": "sort, id",
    },
    "notes": {
        "fields": ("emoji", "text", "mood", "ts", "sort"),
        "defaults": {"emoji": "✏️", "text": "", "mood": "teal",
                     "ts": _now_ts, "sort": 0},
        "enums": {"mood": NOTE_MOODS},
        "ints": ("ts", "sort"),
        "now_falsy": ("ts",),      # 显式传 0/None 也取当前时间(旧实现 or 语义)
        "order": "ts DESC, id DESC",
    },
    "friendlinks": {
        "fields": ("name", "url", "emoji", "desc", "sort"),
        "defaults": {"name": "", "url": "", "emoji": "🔗",
                     "desc": "", "sort": 99},
        "ints": ("sort",),
        "order": "sort, id",
    },
    "songs": {
        "fields": ("title", "artist", "emoji", "song_id", "note", "sort"),
        "defaults": {"title": "", "artist": "", "emoji": "🎵",
                     "song_id": "", "note": "", "sort": 99},
        "ints": ("sort",),
        "order": "sort, id",
    },
}


def crud_get(kind):
    """全部行,按规格排序"""
    with get_db() as c:
        rows = c.execute(
            f"SELECT * FROM {kind} ORDER BY {TABLE_SPECS[kind]['order']}").fetchall()
        return [dict(r) for r in rows]


def crud_insert(kind, item):
    spec = TABLE_SPECS[kind]
    enums = spec.get("enums", {})
    now_falsy = spec.get("now_falsy", ())
    vals = []
    for f in spec["fields"]:
        default = spec["defaults"][f]
        dv = default() if callable(default) else default
        if f in now_falsy:
            v = item.get(f) or dv
        elif f in item:
            v = item[f]
        else:
            v = dv
        if f in enums and v not in enums[f]:
            v = dv
        if f in spec["ints"]:
            v = int(v)
        vals.append(v)
    cols = ",".join(spec["fields"])
    marks = ",".join("?" * len(vals))
    with get_db() as c:
        cur = c.execute(f"INSERT INTO {kind}({cols}) VALUES({marks})", vals)
        row = c.execute(f"SELECT * FROM {kind} WHERE id=?",
                        (cur.lastrowid,)).fetchone()
        return dict(row)


def crud_update(kind, rid, item):
    """只覆盖 item 里出现的字段;枚举非法忽略(保留原值);数字强转"""
    spec = TABLE_SPECS[kind]
    enums = spec.get("enums", {})
    with get_db() as c:
        row = c.execute(f"SELECT * FROM {kind} WHERE id=?", (rid,)).fetchone()
        if not row:
            return None
        merged = dict(row)
        for f in spec["fields"]:
            if f not in item:
                continue
            v = item[f]
            if f in enums:
                if v in enums[f]:
                    merged[f] = v
            elif f in spec["ints"]:
                merged[f] = int(v)
            else:
                merged[f] = v
        sets = ",".join(f"{f}=?" for f in spec["fields"])
        c.execute(f"UPDATE {kind} SET {sets} WHERE id=?",
                  [merged[f] for f in spec["fields"]] + [rid])
        return merged


def crud_delete(kind, rid):
    with get_db() as c:
        cur = c.execute(f"DELETE FROM {kind} WHERE id=?", (rid,))
        return cur.rowcount > 0


# ---- 兼容薄壳:保留 v1.0 以来的函数名(app.py 路由 / PAGE_FIELDS 的
# getattr / 导出 / 历史脚本都按这些名字调用),每个只是一行委托。 ----

def get_skills(): return crud_get("skills")
def insert_skill(item): return crud_insert("skills", item)
def update_skill(sid, item): return crud_update("skills", sid, item)
def delete_skill(sid): return crud_delete("skills", sid)

def get_timeline(): return crud_get("timeline")
def insert_timeline(item): return crud_insert("timeline", item)
def update_timeline(eid, item): return crud_update("timeline", eid, item)
def delete_timeline(eid): return crud_delete("timeline", eid)

def get_stats(): return crud_get("stats")
def insert_stat(item): return crud_insert("stats", item)
def update_stat(sid, item): return crud_update("stats", sid, item)
def delete_stat(sid): return crud_delete("stats", sid)

def get_works(): return crud_get("works")
def insert_work(item): return crud_insert("works", item)
def update_work(wid, item): return crud_update("works", wid, item)
def delete_work(wid): return crud_delete("works", wid)

def get_profile(): return crud_get("profile")
def insert_profile(item): return crud_insert("profile", item)
def update_profile(pid, item): return crud_update("profile", pid, item)
def delete_profile(pid): return crud_delete("profile", pid)

def get_honors(): return crud_get("honors")
def insert_honor(item): return crud_insert("honors", item)
def update_honor(hid, item): return crud_update("honors", hid, item)
def delete_honor(hid): return crud_delete("honors", hid)

def get_notes(): return crud_get("notes")
def insert_note(item): return crud_insert("notes", item)
def update_note(nid, item): return crud_update("notes", nid, item)
def delete_note(nid): return crud_delete("notes", nid)

def get_friendlinks(): return crud_get("friendlinks")
def insert_friendlink(item): return crud_insert("friendlinks", item)
def update_friendlink(fid, item): return crud_update("friendlinks", fid, item)
def delete_friendlink(fid): return crud_delete("friendlinks", fid)

def get_songs(): return crud_get("songs")
def insert_song(item): return crud_insert("songs", item)
def update_song(sid, item): return crud_update("songs", sid, item)
def delete_song(sid): return crud_delete("songs", sid)


# ---------------- v3.1.0 提问箱 ----------------

QUESTION_MAX_BODY = 200
QUESTION_MAX_ANSWER = 500


def add_question(body: str, ip: str = "") -> dict:
    """公开匿名提问:默认待回答池(不对访客展示)"""
    import time as _t
    body = _as_text(body).strip()[:QUESTION_MAX_BODY]
    if not body:
        return {"ok": False, "error": "问题不能为空"}
    with get_db() as c:
        c.execute("INSERT INTO questions(body,ts,ip,shown) VALUES(?,?,?,0)",
                  (body, int(_t.time()), (ip or "")[:64]))
        qid = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": qid}


def list_questions_public(limit: int = 60) -> list:
    """前台:只有已回答且公开的,新回答在前(不吐 IP)"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,body,answer,ts,answered_ts FROM questions
               WHERE shown=1 AND answer!='' ORDER BY answered_ts DESC LIMIT ?""",
            (limit,)).fetchall()
    return [dict(r) for r in rows]


def list_questions_admin() -> list:
    """后台:全部状态(待回答的排前面),含 IP"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,body,answer,ts,ip,shown,answered_ts FROM questions
               ORDER BY shown ASC, answered_ts DESC, ts DESC LIMIT 500""").fetchall()
    return [dict(r) for r in rows]


def answer_question(qid: int, answer: str) -> dict:
    """站主回答:写入答案、盖上回答时间,并把状态切到公开"""
    answer = _as_text(answer).strip()[:QUESTION_MAX_ANSWER]
    if not answer:
        return {"ok": False, "error": "回答不能为空"}
    import time as _t
    with get_db() as c:
        row = c.execute("SELECT id FROM questions WHERE id=?", (qid,)).fetchone()
        if not row:
            return {"ok": False, "error": "问题不存在"}
        c.execute("UPDATE questions SET answer=?,answered_ts=?,shown=1 WHERE id=?",
                  (answer, int(_t.time()), qid))
        out = c.execute("SELECT id,body,answer,ts,shown,answered_ts FROM questions WHERE id=?",
                        (qid,)).fetchone()
    return {"ok": True, "question": dict(out)}


def set_question_shown(qid: int, shown: int) -> bool:
    if shown not in (0, 1, 2):
        return False
    with get_db() as c:
        cur = c.execute("UPDATE questions SET shown=? WHERE id=?", (shown, qid))
        return cur.rowcount > 0


def delete_question(qid: int) -> bool:
    with get_db() as c:
        cur = c.execute("DELETE FROM questions WHERE id=?", (qid,))
        return cur.rowcount > 0


def question_counts() -> dict:
    with get_db() as c:
        pending = c.execute("SELECT COUNT(*) n FROM questions WHERE shown=0").fetchone()["n"]
        shown = c.execute("SELECT COUNT(*) n FROM questions WHERE shown=1").fetchone()["n"]
        total = c.execute("SELECT COUNT(*) n FROM questions").fetchone()["n"]
    return {"pending": pending, "shown": shown, "total": total}


def get_questions_for_export() -> list:
    """备份用:全部问题(含待答/隐藏)"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,body,ts,ip,shown,answer,answered_ts
               FROM questions ORDER BY id ASC""").fetchall()
    return [dict(r) for r in rows]


# ---------------- v3.1.0 涂鸦墙 ----------------


def get_doodles_for_export() -> list:
    """v3.1.1 补:备份用涂鸦列表。

    之前 export 只带了 questions 没带 doodles,换服务器恢复后涂鸦墙会全空。
    涂鸦的图片文件本身在 assets/uploads/ 下,这里只备份元数据。
    """
    with get_db() as c:
        rows = c.execute(
            """SELECT id,file,ts,ip,shown,width,height
               FROM doodles ORDER BY id ASC""").fetchall()
    return [dict(r) for r in rows]


def _doodle_row(r) -> dict:
    d = dict(r)
    d["url"] = f"/assets/uploads/{d['file']}"
    return d


def add_doodle(file: str, ip: str = "", width: int = 0, height: int = 0) -> dict:
    """访客涂鸦上传后登记(文件已由 app.py 校验并落盘),默认待审核"""
    import time as _t
    file = _as_text(file).strip()
    if not file or "/" in file or "\\" in file or file.startswith("."):
        return {"ok": False, "error": "文件名不合法"}
    try:
        width = max(0, min(20000, int(width or 0)))
        height = max(0, min(20000, int(height or 0)))
    except (TypeError, ValueError):
        width = height = 0
    with get_db() as c:
        c.execute("INSERT INTO doodles(file,ts,ip,shown,width,height) VALUES(?,?,?,0,?,?)",
                  (file, int(_t.time()), (ip or "")[:64], width, height))
        did = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": did}


def list_doodles_public(limit: int = 36) -> list:
    """前台:展示中的涂鸦,新的在前(不吐 IP)"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,file,width,height,ts FROM doodles
               WHERE shown=1 ORDER BY ts DESC LIMIT ?""", (limit,)).fetchall()
    return [_doodle_row(r) for r in rows]


def list_doodles_admin() -> list:
    """后台:全部涂鸦(待审核排前面),含 IP"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,file,ts,ip,shown,width,height FROM doodles
               ORDER BY shown ASC, ts DESC LIMIT 500""").fetchall()
    return [_doodle_row(r) for r in rows]


def set_doodle_shown(did: int, shown: int) -> bool:
    if shown not in (0, 1, 2):
        return False
    with get_db() as c:
        cur = c.execute("UPDATE doodles SET shown=? WHERE id=?", (shown, did))
        return cur.rowcount > 0


def delete_doodle(did: int) -> dict:
    """删记录并返回文件名,由调用方决定是否连文件删"""
    with get_db() as c:
        row = c.execute("SELECT file FROM doodles WHERE id=?", (did,)).fetchone()
        if not row:
            return {"ok": False, "error": "涂鸦不存在"}
        c.execute("DELETE FROM doodles WHERE id=?", (did,))
    return {"ok": True, "file": row["file"]}


def doodle_counts() -> dict:
    with get_db() as c:
        pending = c.execute("SELECT COUNT(*) n FROM doodles WHERE shown=0").fetchone()["n"]
        shown = c.execute("SELECT COUNT(*) n FROM doodles WHERE shown=1").fetchone()["n"]
        total = c.execute("SELECT COUNT(*) n FROM doodles").fetchone()["n"]
    return {"pending": pending, "shown": shown, "total": total}


# ---------------- v3.1.0 那年今日(首页回看卡片) ----------------


def get_onthisday() -> dict:
    """往年同月日的随手记 + 相册照片。今年内的不要(回看才有意思),没数据返回空列表。

    timeline.time_label 是 "2026.09" 这类人读文本,没法可靠解析日期,所以不参与。
    """
    import time as _t
    now = time.localtime(_t.time())
    if now.tm_mon == 2 and now.tm_mday == 29:      # 闰日没有"往年同一天",直接空
        return {"notes": [], "photos": []}
    md = f"{now.tm_mon:02d}-{now.tm_mday:02d}"
    year = now.tm_year
    notes, photos = [], []
    with get_db() as c:
        # notes.ts 是 unix 时间戳:sqlite 的 strftime 按本地时区?否,unixepoch 是 UTC,
        # 站点按北京时间运营,直接在 SQL 里算会差 8 小时,拿回 Python 里比
        rows = c.execute(
            """SELECT id,emoji,text,mood,ts FROM notes
               WHERE ts>0 ORDER BY ts DESC LIMIT 2000""").fetchall()
        for r in rows:
            lt = _t.localtime(r["ts"])
            if lt.tm_year < year and (lt.tm_mon, lt.tm_mday) == (now.tm_mon, now.tm_mday):
                notes.append(dict(r))
                if len(notes) >= 5:
                    break
        # photos.shot_at 是 YYYY-MM-DD 文本,可以直接字符串比较
        prows = c.execute(
            f"""SELECT id,file,title,shot_at,width,height FROM photos
                WHERE shown=1 AND length(shot_at)=10 AND substr(shot_at,6,5)=?
                  AND substr(shot_at,1,4)+0 < ?
                ORDER BY shot_at DESC LIMIT 3""", (md, year)).fetchall()
        photos = [_photo_row(r) for r in prows]
    return {"notes": notes, "photos": photos}


# ---------------- 备份导入 ----------------

IMPORT_FIELDS = {
    "skills": ("name", "percent", "note", "category", "color", "sort"),
    "timeline": ("emoji", "time_label", "title", "content", "sort"),
    "stats": ("emoji", "number", "unit", "label", "sort"),
    "works": ("emoji", "cover", "title", "desc", "pill", "link", "sort"),
    "profile": ("kind", "emoji", "label", "value", "sort"),
    "honors": ("emoji", "year", "title", "desc", "level", "sort"),
    "notes": ("emoji", "text", "mood", "ts", "sort"),
    "friendlinks": ("name", "url", "emoji", "desc", "sort"),
    "songs": ("title", "artist", "emoji", "song_id", "note", "sort"),
    # questions / doodles / messages / message_threads 走 import_payload 里的
    # 特殊分支(要保留 id、带凭证),不能登记在这里——否则通用循环先插一遍、
    # 特殊分支再插一遍,恢复一次备份每条提问翻倍(v3.2.0 测试套件抓到)。
}


def get_messages_for_export() -> list:
    """v2.7.3 备份用:全部留言(含待审/隐藏),带上 token 以便恢复后原留言人还能追问"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,name,body,color,ts,ip,shown,reply,token
               FROM messages ORDER BY id ASC""").fetchall()
    return [dict(r) for r in rows]


def get_threads_for_export() -> list:
    """v2.7.3 备份用:全部对话线程(含待审追问)"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,msg_id,role,body,ts,ip,shown
               FROM message_threads ORDER BY id ASC""").fetchall()
    return [dict(r) for r in rows]


# 导入时的字段约束:v2.7.5 加固。以前直接把 JSON 里的值塞进 SQL,
# percent 传 99999 也能落库(前台进度条会画出界),category 传任意串也能进。
IMPORT_TEXT_LIMITS = {
    "name": 80, "note": 200, "title": 120, "desc": 300, "label": 120,
    "value": 2000, "content": 2000, "emoji": 8, "category": 20,
    "color": 20, "pill": 40, "link": 500, "url": 500, "level": 20,
    "time_label": 60, "mood": 20, "text": 500, "artist": 100,
    "song_id": 40, "cover": 40, "kind": 20, "unit": 20, "year": 20,
    "body": 200, "answer": 500,
}
IMPORT_NUM_RANGES = {
    "percent": (0, 100),
    "sort": (-100000, 100000),
    "ts": (0, 4102444800),      # 到 2100 年
    "answered_ts": (0, 4102444800),
    "shown": (0, 2),
}
IMPORT_ENUMS = {
    "category": ("serious", "passive"),
}


def _clean_import_value(table: str, field: str, v):
    """把导入值规整到合法范围,非法值退回默认值而不是写脏数据"""
    if field in IMPORT_NUM_RANGES:
        lo, hi = IMPORT_NUM_RANGES[field]
        try:
            n = int(float(v))
        except (TypeError, ValueError):
            return 0
        return max(lo, min(hi, n))
    if field in IMPORT_ENUMS:
        s = _as_text(v)
        return s if s in IMPORT_ENUMS[field] else IMPORT_ENUMS[field][0]
    if field in ("ts",):
        try:
            return max(0, int(float(v)))
        except (TypeError, ValueError):
            return 0
    s = _as_text(v)
    lim = IMPORT_TEXT_LIMITS.get(field)
    if lim:
        s = s[:lim]
    return s


def import_payload(payload: dict, replace: bool = False) -> dict:
    """把导出的 JSON 写回数据库,返回各表恢复条数

    replace=False:合并 —— 有 id 就覆盖同 id,没 id 就新增
    replace=True :先清空该表再全量写入
    """
    counts = {}
    with get_db() as c:
        for table, fields in IMPORT_FIELDS.items():
            rows = payload.get(table)
            if not isinstance(rows, list):
                continue
            if replace:
                c.execute(f"DELETE FROM {table}")

            n = 0
            for row in rows:
                if not isinstance(row, dict):
                    continue
                vals = tuple(_clean_import_value(table, f, row.get(f))
                             for f in fields)
                rid = row.get("id")
                if rid is not None and not replace:
                    exists = c.execute(
                        f"SELECT 1 FROM {table} WHERE id=?", (rid,)).fetchone()
                    if exists:
                        sets = ",".join(f"{f}=?" for f in fields)
                        c.execute(f"UPDATE {table} SET {sets} WHERE id=?",
                                  vals + (rid,))
                        n += 1
                        continue
                cols = ",".join(fields)
                marks = ",".join("?" * len(fields))
                c.execute(f"INSERT INTO {table}({cols}) VALUES({marks})", vals)
                n += 1
            counts[table] = n

        # v2.7.3:留言与对话线程。结构特殊(要保留 id、带 token),单独处理,
        # 且必须「先留言后线程」,否则线程会找不到所属留言。
        if replace:
            c.execute("DELETE FROM message_threads")
            c.execute("DELETE FROM messages")

        msg_rows = payload.get("messages")
        if isinstance(msg_rows, list):
            n = 0
            for row in msg_rows:
                if not isinstance(row, dict) or not row.get("body"):
                    continue
                fields = ("id", "name", "body", "color", "ts", "ip", "shown",
                          "reply", "token")
                vals = tuple(row.get(f) for f in fields)
                vals = (vals[0], vals[1] or "匿名", vals[2], vals[3] or "pink",
                        vals[4] or 0, vals[5] or "", vals[6] if vals[6] is not None else 1,
                        vals[7] or "", vals[8] or "")
                rid = vals[0]
                exists = (rid is not None and c.execute(
                    "SELECT 1 FROM messages WHERE id=?", (rid,)).fetchone())
                if exists:
                    sets = ",".join(f"{f}=?" for f in fields[1:])
                    c.execute(f"UPDATE messages SET {sets} WHERE id=?",
                              vals[1:] + (rid,))
                elif rid is not None:
                    cols = ",".join(fields)
                    marks = ",".join("?" * len(fields))
                    c.execute(f"INSERT INTO messages({cols}) VALUES({marks})", vals)
                else:
                    c.execute(
                        """INSERT INTO messages(name,body,color,ts,ip,shown,reply,token)
                           VALUES(?,?,?,?,?,?,?,?)""", vals[1:])
                n += 1
            counts["messages"] = n

        thr_rows = payload.get("message_threads")
        if isinstance(thr_rows, list):
            n = 0
            for row in thr_rows:
                if not isinstance(row, dict) or not row.get("body"):
                    continue
                fields = ("id", "msg_id", "role", "body", "ts", "ip", "shown")
                vals = tuple(row.get(f) for f in fields)
                vals = (vals[0], vals[1], vals[2] or "guest", vals[3],
                        vals[4] or 0, vals[5] or "",
                        vals[6] if vals[6] is not None else 1)
                # 所属留言不存在就跳过,避免留下孤儿线程
                if not vals[1] or not c.execute(
                        "SELECT 1 FROM messages WHERE id=?", (vals[1],)).fetchone():
                    continue
                rid = vals[0]
                exists = (rid is not None and c.execute(
                    "SELECT 1 FROM message_threads WHERE id=?", (rid,)).fetchone())
                if exists:
                    sets = ",".join(f"{f}=?" for f in fields[1:])
                    c.execute(f"UPDATE message_threads SET {sets} WHERE id=?",
                              vals[1:] + (rid,))
                elif rid is not None:
                    cols = ",".join(fields)
                    marks = ",".join("?" * len(fields))
                    c.execute(f"INSERT INTO message_threads({cols}) VALUES({marks})", vals)
                else:
                    c.execute(
                        """INSERT INTO message_threads(msg_id,role,body,ts,ip,shown)
                           VALUES(?,?,?,?,?,?)""", vals[1:])
                n += 1
            counts["message_threads"] = n

        # v3.1.1 补:提问箱与涂鸦墙也要能恢复,否则换服务器后这两块全空。
        if replace:
            c.execute("DELETE FROM questions")
            c.execute("DELETE FROM doodles")

        q_rows = payload.get("questions")
        if isinstance(q_rows, list):
            n = 0
            for row in q_rows:
                if not isinstance(row, dict) or not row.get("body"):
                    continue
                fields = ("id", "body", "ts", "ip", "shown", "answer", "answered_ts")
                vals = tuple(row.get(f) for f in fields)
                vals = (vals[0], _as_text(vals[1])[:300], vals[2] or 0,
                        vals[3] or "", vals[4] if vals[4] is not None else 0,
                        _as_text(vals[5])[:500], vals[6] or 0)
                rid = vals[0]
                exists = (rid is not None and c.execute(
                    "SELECT 1 FROM questions WHERE id=?", (rid,)).fetchone())
                if exists:
                    sets = ",".join(f"{f}=?" for f in fields[1:])
                    c.execute(f"UPDATE questions SET {sets} WHERE id=?", vals[1:] + (rid,))
                elif rid is not None:
                    cols = ",".join(fields)
                    marks = ",".join("?" * len(fields))
                    c.execute(f"INSERT INTO questions({cols}) VALUES({marks})", vals)
                else:
                    c.execute(
                        """INSERT INTO questions(body,ts,ip,shown,answer,answered_ts)
                           VALUES(?,?,?,?,?,?)""", vals[1:])
                n += 1
            counts["questions"] = n

        d_rows = payload.get("doodles")
        if isinstance(d_rows, list):
            n = 0
            for row in d_rows:
                if not isinstance(row, dict) or not row.get("file"):
                    continue
                fields = ("id", "file", "ts", "ip", "shown", "width", "height")
                vals = tuple(row.get(f) for f in fields)
                vals = (vals[0], _as_text(vals[1]).strip()[:120], vals[2] or 0,
                        vals[3] or "", vals[4] if vals[4] is not None else 0,
                        vals[5] or 0, vals[6] or 0)
                if "/" in vals[1] or "\\" in vals[1] or vals[1].startswith("."):
                    continue
                rid = vals[0]
                exists = (rid is not None and c.execute(
                    "SELECT 1 FROM doodles WHERE id=?", (rid,)).fetchone())
                if exists:
                    sets = ",".join(f"{f}=?" for f in fields[1:])
                    c.execute(f"UPDATE doodles SET {sets} WHERE id=?", vals[1:] + (rid,))
                elif rid is not None:
                    cols = ",".join(fields)
                    marks = ",".join("?" * len(fields))
                    c.execute(f"INSERT INTO doodles({cols}) VALUES({marks})", vals)
                else:
                    c.execute(
                        """INSERT INTO doodles(file,ts,ip,shown,width,height)
                           VALUES(?,?,?,?,?,?)""", vals[1:])
                n += 1
            counts["doodles"] = n
    # site is exported as a key/value object, not a table-shaped list.
    # Restore only whitelisted fields through the same validation/default path
    # as the site settings editor.
    site = payload.get("site")
    if isinstance(site, dict):
        allowed_site = {k: v for k, v in site.items()
                        if k in SITE_FIELDS and isinstance(v, str)}
        if allowed_site:
            set_site(allowed_site)
            counts["site"] = len(allowed_site)
    return counts


# ---------------- 访问统计 ----------------

BOT_PATTERNS = (
    "bot", "spider", "crawl", "slurp", "curl", "wget", "python-requests",
    "httpclient", "scrapy", "headless", "phantom", "facebookexternalhit",
    "whatsapp", "telegram", "preview", "monitor", "uptime", "pingdom",
)


def _classify_ua(ua: str):
    """把 UA 简化成 '浏览器 / 系统' 标签,并判断是不是爬虫"""
    if not ua:
        return "未知", 1
    low = ua.lower()
    is_bot = 1 if any(p in low for p in BOT_PATTERNS) else 0

    if "edg/" in low:
        browser = "Edge"
    elif "opr/" in low or "opera" in low:
        browser = "Opera"
    elif "firefox/" in low:
        browser = "Firefox"
    elif "chrome/" in low or "crios/" in low:
        browser = "Chrome"
    elif "safari/" in low:
        browser = "Safari"
    elif "micromessenger" in low:
        browser = "微信"
    else:
        browser = "其他"

    if "iphone" in low or "ipad" in low:
        os_name = "iOS"
    elif "android" in low:
        os_name = "Android"
    elif "windows" in low:
        os_name = "Windows"
    elif "mac os" in low or "macintosh" in low:
        os_name = "macOS"
    elif "linux" in low:
        os_name = "Linux"
    else:
        os_name = "其他"

    return f"{browser} / {os_name}", is_bot


def record_visit(path: str, referer: str, ua: str, day: str, ts: int,
                 city: str = "", is_new: int = 1, dur_s: int = 0):
    """记录一次访问。调用方负责把 referer 裁成域名,city 可为空(查不到就留空)。
    返回新行 id,供前端离开时补报停留时长。"""
    label, is_bot = _classify_ua(ua)
    with get_db() as c:
        c.execute(
            "INSERT INTO visits(day,ts,path,referer,ua,is_bot,city,is_new,dur_s) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (day, ts, path[:200], referer[:200], label[:60], is_bot,
             city[:40], 1 if is_new else 0, max(0, int(dur_s))))
        return c.execute("SELECT last_insert_rowid() id").fetchone()["id"]


def update_visit_dur(vid: int, dur_s: int) -> bool:
    """补报停留时长(上限 2 小时,防异常值)。只增不减,取已报的最大值。"""
    try:
        dur_s = max(0, min(int(dur_s), 7200))
    except (TypeError, ValueError):
        return False
    with get_db() as c:
        cur = c.execute(
            "UPDATE visits SET dur_s=MAX(dur_s,?) WHERE id=?", (dur_s, vid))
        return cur.rowcount > 0


def get_visit_cities(limit: int = 200) -> list:
    """访客城市聚合(去 IP 化):返回 [{city, count}],按次数降序。空城市不返回。"""
    with get_db() as c:
        rows = c.execute(
            "SELECT city, COUNT(*) n FROM visits "
            "WHERE city != '' AND is_bot = 0 "
            "GROUP BY city ORDER BY n DESC, MAX(ts) DESC LIMIT ?",
            (limit,)).fetchall()
    return [{"city": r["city"], "count": r["n"]} for r in rows]


def get_visit_stats(days: int = 30) -> dict:
    """返回看板需要的聚合数据"""
    import datetime as _dt
    import time as _t
    now = int(_t.time())
    since = now - days * 86400

    # 统一用北京时间(与 track 写入时的 day 口径一致,不依赖服务器时区)
    _BJ = _dt.timezone(_dt.timedelta(hours=8))
    today_dt = _dt.datetime.now(_BJ)
    today_str = today_dt.strftime("%Y-%m-%d")

    with get_db() as c:
        total = c.execute("SELECT COUNT(*) n FROM visits").fetchone()["n"]
        total_real = c.execute(
            "SELECT COUNT(*) n FROM visits WHERE is_bot=0").fetchone()["n"]

        today = c.execute(
            "SELECT COUNT(*) n FROM visits WHERE day=? AND is_bot=0",
            (today_str,)).fetchone()["n"]

        # 按天(只取真实访问),缺的日期补 0,保证图表 X 轴连续
        rows = c.execute(
            """SELECT day, COUNT(*) n FROM visits
               WHERE is_bot=0 AND ts>=? GROUP BY day ORDER BY day""",
            (since,)).fetchall()
        day_map = {r["day"]: r["n"] for r in rows}
        by_day = []
        for i in range(days - 1, -1, -1):        # 从最早到最近
            dstr = (today_dt - _dt.timedelta(days=i)).strftime("%Y-%m-%d")
            by_day.append({"day": dstr, "n": day_map.get(dstr, 0)})

        # 来源(空 = 直接访问)
        refs = c.execute(
            """SELECT referer, COUNT(*) n FROM visits
               WHERE is_bot=0 AND referer<>'' GROUP BY referer
               ORDER BY n DESC LIMIT 10""").fetchall()
        by_ref = [{"referer": r["referer"], "n": r["n"]} for r in refs]

        # 浏览器/系统
        uas = c.execute(
            """SELECT ua, COUNT(*) n FROM visits
               WHERE is_bot=0 GROUP BY ua ORDER BY n DESC LIMIT 8""").fetchall()
        by_ua = [{"ua": r["ua"], "n": r["n"]} for r in uas]

        # 最近访问
        recent = c.execute(
            """SELECT day,ts,path,referer,ua FROM visits
               WHERE is_bot=0 ORDER BY ts DESC LIMIT 20""").fetchall()
        recent = [dict(r) for r in recent]

        # 按小时分布(帮助判断活跃时段)
        # 用 ts 直接算,显式 +8 小时,不依赖 SQLite localtime(容器里常是 UTC)
        hours = c.execute(
            """SELECT CAST((((ts + 28800) % 86400) / 3600) AS INTEGER) h,
                      COUNT(*) n FROM visits WHERE is_bot=0 GROUP BY h""").fetchall()
        by_hour = {r["h"]: r["n"] for r in hours}

    return {
        "total": total,
        "total_real": total_real,
        "today": today,
        "by_day": by_day,
        "by_ref": by_ref,
        "by_ua": by_ua,
        "recent": recent,
        "by_hour": [by_hour.get(h, 0) for h in range(24)],
        "cities": get_visit_cities(30),
        "days": days,
    }


# ============================================================
# 留言板
# ============================================================

MESSAGE_MAX_BODY = 140      # 留言上限,和微博早期一样长,够说一句话
MESSAGE_MAX_NAME = 20
MSG_COLORS = ("pink", "orange", "teal", "purple", "yellow", "blue")


def _as_text(v, default: str = "") -> str:
    """v2.7.5 加固:把任意 JSON 值安全转成字符串。

    之前直接 (name or "匿名").strip(),若前端传 {"name": {...}} 或 ["x"]
    会抛 AttributeError → 500。公开接口不能因为畸形输入崩掉。
    """
    if isinstance(v, str):
        return v
    if v is None:
        return default
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    return default


def add_message(name: str, body: str, color: str = "", ip: str = "") -> dict:
    """公开写留言:默认进待审核池。返回一次性访客凭证 token,用于之后继续追问"""
    import time as _t
    import secrets
    name = _as_text(name).strip()[:MESSAGE_MAX_NAME] or "匿名"
    body = _as_text(body).strip()[:MESSAGE_MAX_BODY]
    color = _as_text(color)
    if not body:
        return {"ok": False, "error": "内容不能为空"}
    if color not in MSG_COLORS:
        import random
        color = random.choice(MSG_COLORS)
    token = secrets.token_urlsafe(16)
    with get_db() as c:
        c.execute(
            "INSERT INTO messages(name,body,color,ts,ip,shown,token) VALUES(?,?,?,?,?,0,?)",
            (name, body, color, int(_t.time()), (ip or "")[:64], token))
        mid = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": mid, "name": name, "body": body,
            "color": color, "token": token}


def _threads_of(c, msg_ids) -> dict:
    """批量取一批留言的公开线程,避免 N+1"""
    if not msg_ids:
        return {}
    qs = ",".join("?" * len(msg_ids))
    rows = c.execute(
        f"""SELECT id,msg_id,role,body,ts FROM message_threads
            WHERE shown=1 AND msg_id IN ({qs}) ORDER BY ts ASC""",
        tuple(msg_ids)).fetchall()
    out = {}
    for r in rows:
        out.setdefault(r["msg_id"], []).append(
            {"id": r["id"], "role": r["role"], "body": r["body"], "ts": r["ts"]})
    return out


def list_messages_public(limit: int = 30) -> list:
    """前台:只给展示中的,新的在前;每条带上公开的对话线程"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,name,body,color,ts FROM messages
               WHERE shown=1 ORDER BY ts DESC LIMIT ?""", (limit,)).fetchall()
        items = [dict(r) for r in rows]
        ths = _threads_of(c, [m["id"] for m in items])
    for m in items:
        m["threads"] = ths.get(m["id"], [])
    return items


def list_messages_admin() -> list:
    """后台:全部状态 + 全部线程(含待审追问),旧的待审核排前面方便处理"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,name,body,color,ts,ip,shown FROM messages
               ORDER BY shown ASC, ts DESC LIMIT 500""").fetchall()
        items = [dict(r) for r in rows]
        ids = [m["id"] for m in items]
        ths = {}
        if ids:
            qs = ",".join("?" * len(ids))
            for r in c.execute(
                f"""SELECT id,msg_id,role,body,ts,shown FROM message_threads
                    WHERE msg_id IN ({qs}) ORDER BY ts ASC""", tuple(ids)):
                ths.setdefault(r["msg_id"], []).append(
                    {"id": r["id"], "role": r["role"], "body": r["body"],
                     "ts": r["ts"], "shown": r["shown"]})
    for m in items:
        m["threads"] = ths.get(m["id"], [])
    return items


def alert_snapshot() -> dict:
    """v2.7.1 后台实时提醒:待审留言/追问计数 + 最新一条摘要(不含 IP)
    v3.1.0 追加:待答提问 / 待审涂鸦"""
    with get_db() as c:
        mp = c.execute("SELECT COUNT(*) n FROM messages WHERE shown=0").fetchone()["n"]
        tp = c.execute(
            "SELECT COUNT(*) n FROM message_threads WHERE shown=0 AND role='guest'"
        ).fetchone()["n"]
        latest_msg = c.execute(
            """SELECT id,name,body,ts FROM messages WHERE shown=0
               ORDER BY ts DESC LIMIT 1""").fetchone()
        latest_thr = c.execute(
            """SELECT t.id,t.msg_id,t.body,t.ts,m.name FROM message_threads t
               JOIN messages m ON m.id=t.msg_id
               WHERE t.shown=0 AND t.role='guest'
               ORDER BY t.ts DESC LIMIT 1""").fetchone()
        newest_ts = c.execute(
            "SELECT COALESCE(MAX(ts),0) t FROM messages").fetchone()["t"]
        # v3.1.0 提问箱 / 涂鸦墙
        qp = c.execute("SELECT COUNT(*) n FROM questions WHERE shown=0").fetchone()["n"]
        dp = c.execute("SELECT COUNT(*) n FROM doodles WHERE shown=0").fetchone()["n"]
        latest_q = c.execute(
            """SELECT id,body,ts FROM questions WHERE shown=0
               ORDER BY ts DESC LIMIT 1""").fetchone()
    return {
        "pending_messages": mp,
        "pending_threads": tp,
        "newest_ts": newest_ts,
        "latest_message": dict(latest_msg) if latest_msg else None,
        "latest_thread": dict(latest_thr) if latest_thr else None,
        "pending_questions": qp,
        "pending_doodles": dp,
        "latest_question": dict(latest_q) if latest_q else None,
    }


def message_counts() -> dict:
    """后台卡片:待审留言 / 展示中 / 总留言 / 待审追问"""
    with get_db() as c:
        pending = c.execute(
            "SELECT COUNT(*) n FROM messages WHERE shown=0").fetchone()["n"]
        shown = c.execute(
            "SELECT COUNT(*) n FROM messages WHERE shown=1").fetchone()["n"]
        total = c.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        tpending = c.execute(
            "SELECT COUNT(*) n FROM message_threads WHERE shown=0").fetchone()["n"]
    return {"pending": pending, "shown": shown, "total": total,
            "thread_pending": tpending}


def set_message_shown(mid: int, shown: int) -> bool:
    """审核:0 待审 / 1 展示 / 2 隐藏"""
    if shown not in (0, 1, 2):
        return False
    with get_db() as c:
        cur = c.execute("UPDATE messages SET shown=? WHERE id=?", (shown, mid))
        return cur.rowcount > 0


def reply_message(mid: int, reply: str) -> bool:
    """v2.7.0:站主回复改为追加一条 owner 线程(不再覆盖),同时回写 reply 兼容字段"""
    import time as _t
    reply = (reply or "").strip()[:MESSAGE_MAX_BODY]
    if not reply:
        return False
    with get_db() as c:
        if not c.execute("SELECT 1 FROM messages WHERE id=?", (mid,)).fetchone():
            return False
        c.execute(
            """INSERT INTO message_threads(msg_id,role,body,ts,ip,shown)
               VALUES(?,'owner',?,?,'',1)""", (mid, reply, int(_t.time())))
        c.execute("UPDATE messages SET reply=? WHERE id=?", (reply, mid))
        return True


def verify_guest_token(mid: int, token: str) -> bool:
    """校验访客凭证是否属于该留言(v2.7.0)"""
    token = _as_text(token)
    if not token:
        return False
    with get_db() as c:
        row = c.execute("SELECT token FROM messages WHERE id=?", (mid,)).fetchone()
    return bool(row and row["token"] and row["token"] == token)


def add_guest_followup(mid: int, body: str, token: str, ip: str = "") -> dict:
    """访客继续追问:必须带原留言的 token。默认待审核"""
    import time as _t
    body = _as_text(body).strip()[:MESSAGE_MAX_BODY]
    token = _as_text(token)
    if not body:
        return {"ok": False, "error": "内容不能为空"}
    if not token:
        return {"ok": False, "error": "缺少追问凭证"}
    with get_db() as c:
        row = c.execute("SELECT token,shown FROM messages WHERE id=?", (mid,)).fetchone()
        if not row:
            return {"ok": False, "error": "留言不存在"}
        if not row["token"] or row["token"] != token:
            return {"ok": False, "error": "只有原留言人可以继续追问"}
        c.execute(
            """INSERT INTO message_threads(msg_id,role,body,ts,ip,shown)
               VALUES(?,'guest',?,?,?,0)""", (mid, body, int(_t.time()), (ip or "")[:64]))
        tid = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": tid}


def set_thread_shown(tid: int, shown: int) -> bool:
    """审核访客追问:0 待审 / 1 公开 / 2 隐藏"""
    if shown not in (0, 1, 2):
        return False
    with get_db() as c:
        cur = c.execute("UPDATE message_threads SET shown=? WHERE id=?", (shown, tid))
        return cur.rowcount > 0


def del_thread(tid: int) -> bool:
    with get_db() as c:
        cur = c.execute("DELETE FROM message_threads WHERE id=?", (tid,))
        return cur.rowcount > 0


def del_message(mid: int) -> bool:
    """删除留言(连带线程)"""
    with get_db() as c:
        c.execute("DELETE FROM message_threads WHERE msg_id=?", (mid,))
        cur = c.execute("DELETE FROM messages WHERE id=?", (mid,))
        return cur.rowcount > 0


# ============================================================
# 点赞(按页计数)
# ============================================================

LIKE_PAGES = ("home", "about", "skills", "works", "campus", "map", "contact")


def like_counts() -> dict:
    """全部页面的点赞数(没点过的页面给 0)"""
    with get_db() as c:
        rows = c.execute("SELECT page,n FROM likes").fetchall()
    m = {r["page"]: r["n"] for r in rows}
    return {p: m.get(p, 0) for p in LIKE_PAGES}


def like_total() -> int:
    with get_db() as c:
        return c.execute("SELECT COALESCE(SUM(n),0) n FROM likes").fetchone()["n"]


def add_like(page: str) -> dict:
    """点赞 +1(公开接口,轻防刷:单页计数,不做个人维度)"""
    if page not in LIKE_PAGES:
        return {"ok": False, "error": "unknown page"}
    with get_db() as c:
        c.execute(
            "INSERT INTO likes(page,n) VALUES(?,1) "
            "ON CONFLICT(page) DO UPDATE SET n=n+1", (page,))
        n = c.execute("SELECT n FROM likes WHERE page=?", (page,)).fetchone()["n"]
    return {"ok": True, "page": page, "n": n}


# ============================================================
# 相册(v3.0.0)
# ============================================================

PHOTO_MAX_TITLE = 80
PHOTO_MAX_DESC = 500
PHOTO_MAX_CATEGORY = 20


def _photo_row(r) -> dict:
    d = dict(r)
    d["url"] = f"/assets/uploads/{d['file']}"
    return d


def list_photos_public(category: str = "", limit: int = 500) -> list:
    """前台:只给公开的,按 sort 再按加入时间倒序"""
    with get_db() as c:
        if category:
            rows = c.execute(
                """SELECT id,file,title,desc,category,shot_at,width,height,ts
                   FROM photos WHERE shown=1 AND category=?
                   ORDER BY sort ASC, ts DESC LIMIT ?""",
                (category, limit)).fetchall()
        else:
            rows = c.execute(
                """SELECT id,file,title,desc,category,shot_at,width,height,ts
                   FROM photos WHERE shown=1
                   ORDER BY sort ASC, ts DESC LIMIT ?""", (limit,)).fetchall()
    return [_photo_row(r) for r in rows]


def photo_categories() -> list:
    """前台:有照片的分类及数量(按数量倒序)"""
    with get_db() as c:
        rows = c.execute(
            """SELECT category, COUNT(*) n FROM photos
               WHERE shown=1 AND category!=''
               GROUP BY category ORDER BY n DESC, category ASC""").fetchall()
    return [{"name": r["category"], "count": r["n"]} for r in rows]


def list_photos_admin() -> list:
    """后台:全部照片(含隐藏)"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,file,title,desc,category,shot_at,width,height,shown,sort,ts
               FROM photos ORDER BY sort ASC, ts DESC""").fetchall()
    return [_photo_row(r) for r in rows]


def add_photo(file: str, title: str = "", desc: str = "", category: str = "",
              shot_at: str = "", width: int = 0, height: int = 0) -> dict:
    """把一张已上传的图片加进相册"""
    import time as _t
    file = _as_text(file).strip()
    if not file or "/" in file or "\\" in file or file.startswith("."):
        return {"ok": False, "error": "文件名不合法"}
    title = _as_text(title).strip()[:PHOTO_MAX_TITLE]
    desc = _as_text(desc).strip()[:PHOTO_MAX_DESC]
    category = _as_text(category).strip()[:PHOTO_MAX_CATEGORY]
    shot_at = _as_text(shot_at).strip()[:10]
    try:
        width = max(0, min(20000, int(width or 0)))
        height = max(0, min(20000, int(height or 0)))
    except (TypeError, ValueError):
        width = height = 0
    with get_db() as c:
        if c.execute("SELECT 1 FROM photos WHERE file=?", (file,)).fetchone():
            return {"ok": False, "error": "这张图已经在相册里了"}
        c.execute(
            """INSERT INTO photos(file,title,desc,category,shot_at,width,height,
                                  shown,sort,ts)
               VALUES(?,?,?,?,?,?,?,1,0,?)""",
            (file, title, desc, category, shot_at, width, height, int(_t.time())))
        pid = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": pid}


def update_photo(pid: int, **kw) -> bool:
    """改标题/描述/分类/拍摄日期/显隐/排序"""
    fields, vals = [], []
    if "title" in kw:
        fields.append("title"); vals.append(_as_text(kw["title"]).strip()[:PHOTO_MAX_TITLE])
    if "desc" in kw:
        fields.append("desc"); vals.append(_as_text(kw["desc"]).strip()[:PHOTO_MAX_DESC])
    if "category" in kw:
        fields.append("category"); vals.append(_as_text(kw["category"]).strip()[:PHOTO_MAX_CATEGORY])
    if "shot_at" in kw:
        fields.append("shot_at"); vals.append(_as_text(kw["shot_at"]).strip()[:10])
    if "shown" in kw:
        fields.append("shown"); vals.append(1 if kw["shown"] else 0)
    if "sort" in kw:
        try:
            fields.append("sort"); vals.append(max(-100000, min(100000, int(kw["sort"]))))
        except (TypeError, ValueError):
            pass
    if not fields:
        return False
    with get_db() as c:
        sets = ",".join(f"{f}=?" for f in fields)
        cur = c.execute(f"UPDATE photos SET {sets} WHERE id=?", vals + [pid])
        return cur.rowcount > 0


def del_photo(pid: int) -> dict:
    """从相册移除(可选是否连文件一起删,由调用方决定)"""
    with get_db() as c:
        row = c.execute("SELECT file FROM photos WHERE id=?", (pid,)).fetchone()
        if not row:
            return {"ok": False, "error": "照片不存在"}
        c.execute("DELETE FROM photos WHERE id=?", (pid,))
    return {"ok": True, "file": row["file"]}


def photo_in_album(file: str) -> bool:
    """某文件是否已被相册引用(删文件前检查用)"""
    with get_db() as c:
        return bool(c.execute("SELECT 1 FROM photos WHERE file=?", (file,)).fetchone())


# ============================================================
# 站点公告(后台发,前台横幅)
# ============================================================

def get_active_notice() -> dict | None:
    """前台:当前生效的公告(active=1 的最新一条)"""
    with get_db() as c:
        r = c.execute(
            "SELECT id,body,ts FROM notices WHERE active=1 "
            "ORDER BY ts DESC LIMIT 1").fetchone()
    return dict(r) if r else None


def list_notices() -> list:
    with get_db() as c:
        rows = c.execute(
            "SELECT id,body,ts,active FROM notices ORDER BY ts DESC LIMIT 50").fetchall()
    return [dict(r) for r in rows]


def add_notice(body: str) -> dict:
    body = (body or "").strip()[:100]
    if not body:
        return {"ok": False, "error": "内容不能为空"}
    with get_db() as c:
        c.execute("INSERT INTO notices(body,ts,active) VALUES(?,?,1)",
                  (body, int(time.time())))
        mid = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": mid}


def set_notice_active(nid: int, active: int) -> bool:
    if active not in (0, 1):
        return False
    with get_db() as c:
        cur = c.execute("UPDATE notices SET active=? WHERE id=?", (active, nid))
        return cur.rowcount > 0


def del_notice(nid: int) -> bool:
    with get_db() as c:
        cur = c.execute("DELETE FROM notices WHERE id=?", (nid,))
        return cur.rowcount > 0


# ============================================================
# 倒计时(后台配,前台角标)
# ============================================================

def get_active_countdown() -> dict | None:
    """前台:active=1 的倒计时,取 target 最近的一个"""
    with get_db() as c:
        r = c.execute(
            "SELECT id,title,target,emoji FROM countdowns WHERE active=1 "
            "ORDER BY target ASC LIMIT 1").fetchone()
    return dict(r) if r else None


def list_countdowns() -> list:
    with get_db() as c:
        rows = c.execute(
            "SELECT id,title,target,emoji,active FROM countdowns "
            "ORDER BY target ASC").fetchall()
    return [dict(r) for r in rows]


def upsert_countdown(cid, title: str, target: str, emoji: str, active: int) -> dict:
    """cid 为空则新增,否则更新"""
    title = (title or "").strip()[:20]
    emoji = (emoji or "⏳").strip()[:4]
    import re as _re
    if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", target or ""):
        return {"ok": False, "error": "日期格式应为 YYYY-MM-DD"}
    if not title:
        return {"ok": False, "error": "标题不能为空"}
    active = 1 if active else 0
    with get_db() as c:
        if cid:
            cur = c.execute(
                "UPDATE countdowns SET title=?,target=?,emoji=?,active=? WHERE id=?",
                (title, target, emoji, active, cid))
            if cur.rowcount == 0:
                return {"ok": False, "error": "倒计时不存在"}
        else:
            c.execute(
                "INSERT INTO countdowns(title,target,emoji,active) VALUES(?,?,?,?)",
                (title, target, emoji, active))
    return {"ok": True}


def del_countdown(cid: int) -> bool:
    with get_db() as c:
        cur = c.execute("DELETE FROM countdowns WHERE id=?", (cid,))
        return cur.rowcount > 0


# ============================================================
# 访客深度:新老访客 + 停留时长
# ============================================================
# 新老访客:visits 表加两列(幂等 ALTER,已存在的库自动补)
def _ensure_visit_cols():
    try:
        with get_db() as c:
            cols = [r["name"] for r in c.execute("PRAGMA table_info(visits)")]
            if "is_new" not in cols:
                c.execute("ALTER TABLE visits ADD COLUMN is_new INTEGER DEFAULT 1")
            if "dur_s" not in cols:
                c.execute("ALTER TABLE visits ADD COLUMN dur_s INTEGER DEFAULT 0")
    except Exception:
        pass


def visitor_breakdown(days: int = 30) -> dict:
    """看板卡片:新访客 / 回访 / 平均停留秒数"""
    _ensure_visit_cols()
    since = int(time.time()) - days * 86400
    with get_db() as c:
        total = c.execute(
            "SELECT COUNT(*) n FROM visits WHERE is_bot=0 AND ts>=?",
            (since,)).fetchone()["n"]
        new = c.execute(
            "SELECT COUNT(*) n FROM visits WHERE is_bot=0 AND ts>=? AND is_new=1",
            (since,)).fetchone()["n"]
        back = total - new
        avg = c.execute(
            "SELECT AVG(dur_s) v FROM visits WHERE is_bot=0 AND ts>=? AND dur_s>0",
            (since,)).fetchone()["v"] or 0
    return {"total": total, "new": new, "back": max(back, 0),
            "avg_dur": int(avg)}
