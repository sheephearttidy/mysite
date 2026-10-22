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
    city TEXT DEFAULT ''            -- 访客城市(如 "江苏 南京"),隐私起见不存 IP
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
    reply TEXT DEFAULT ''                  -- 站长回复(可空)
);
CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);

-- 点赞(按页面计数,无 cookie 无 IP,纯计数)
CREATE TABLE IF NOT EXISTS likes (
    page TEXT PRIMARY KEY,
    n INTEGER NOT NULL DEFAULT 0
);
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
}

# 前台特效设置(与安全设置分开,后台独立面板)
FX_DEFAULTS = {
    "fx_holiday_mode": "auto",   # auto=按日期自动 / manual=手动指定 / off=全关
    "fx_holiday_key": "",        # manual 模式下生效:节日 key
    "fx_effects": "1",           # 前台动效总开关(1 开 / 0 关)
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
        # 初始密码 admin,标记必须修改
        if c.execute("SELECT COUNT(*) FROM settings WHERE key='pass_hash'").fetchone()[0] == 0:
            c.execute("INSERT INTO settings(key,value) VALUES('pass_hash',?)",
                      (hash_password(DEFAULT_ADMIN_PASS),))
            c.execute("INSERT INTO settings(key,value) VALUES('must_change_pass','1')")


# ---------------- skills ----------------

def get_skills():
    with get_db() as c:
        rows = c.execute("SELECT * FROM skills ORDER BY category, sort, id").fetchall()
        return [dict(r) for r in rows]


def insert_skill(item):
    with get_db() as c:
        cur = c.execute(
            "INSERT INTO skills(name,percent,note,category,color,sort) VALUES(?,?,?,?,?,?)",
            (item.get("name", ""), int(item.get("percent", 50)), item.get("note", ""),
             item.get("category", "serious"), item.get("color", "teal"),
             int(item.get("sort", 99))))
        row = c.execute("SELECT * FROM skills WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_skill(sid, item):
    with get_db() as c:
        row = c.execute("SELECT * FROM skills WHERE id=?", (sid,)).fetchone()
        if not row:
            return None
        merged = dict(row)
        merged.update({k: item[k] for k in
                       ("name", "note", "category", "color") if k in item})
        if "percent" in item:
            merged["percent"] = int(item["percent"])
        if "sort" in item:
            merged["sort"] = int(item["sort"])
        c.execute(
            "UPDATE skills SET name=?,percent=?,note=?,category=?,color=?,sort=? WHERE id=?",
            (merged["name"], merged["percent"], merged["note"], merged["category"],
             merged["color"], merged["sort"], sid))
        return merged


def delete_skill(sid):
    with get_db() as c:
        cur = c.execute("DELETE FROM skills WHERE id=?", (sid,))
        return cur.rowcount > 0


# ---------------- timeline ----------------

def get_timeline():
    with get_db() as c:
        rows = c.execute("SELECT * FROM timeline ORDER BY sort, id").fetchall()
        return [dict(r) for r in rows]


def insert_timeline(item):
    with get_db() as c:
        cur = c.execute(
            "INSERT INTO timeline(emoji,time_label,title,content,sort) VALUES(?,?,?,?,?)",
            (item.get("emoji", "🚀"), item.get("time_label", ""), item.get("title", ""),
             item.get("content", ""), int(item.get("sort", 99))))
        row = c.execute("SELECT * FROM timeline WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_timeline(eid, item):
    with get_db() as c:
        row = c.execute("SELECT * FROM timeline WHERE id=?", (eid,)).fetchone()
        if not row:
            return None
        merged = dict(row)
        merged.update({k: item[k] for k in
                       ("emoji", "time_label", "title", "content") if k in item})
        if "sort" in item:
            merged["sort"] = int(item["sort"])
        c.execute(
            "UPDATE timeline SET emoji=?,time_label=?,title=?,content=?,sort=? WHERE id=?",
            (merged["emoji"], merged["time_label"], merged["title"], merged["content"],
             merged["sort"], eid))
        return merged


def delete_timeline(eid):
    with get_db() as c:
        cur = c.execute("DELETE FROM timeline WHERE id=?", (eid,))
        return cur.rowcount > 0


# ---------------- stats ----------------

def get_stats():
    with get_db() as c:
        rows = c.execute("SELECT * FROM stats ORDER BY sort, id").fetchall()
        return [dict(r) for r in rows]


def insert_stat(item):
    with get_db() as c:
        cur = c.execute(
            "INSERT INTO stats(emoji,number,unit,label,sort) VALUES(?,?,?,?,?)",
            (item.get("emoji", "😄"), int(item.get("number", 0)), item.get("unit", ""),
             item.get("label", ""), int(item.get("sort", 99))))
        row = c.execute("SELECT * FROM stats WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_stat(sid, item):
    with get_db() as c:
        row = c.execute("SELECT * FROM stats WHERE id=?", (sid,)).fetchone()
        if not row:
            return None
        merged = dict(row)
        merged.update({k: item[k] for k in ("emoji", "unit", "label") if k in item})
        if "number" in item:
            merged["number"] = int(item["number"])
        if "sort" in item:
            merged["sort"] = int(item["sort"])
        c.execute("UPDATE stats SET emoji=?,number=?,unit=?,label=?,sort=? WHERE id=?",
                  (merged["emoji"], merged["number"], merged["unit"], merged["label"],
                   merged["sort"], sid))
        return merged


def delete_stat(sid):
    with get_db() as c:
        cur = c.execute("DELETE FROM stats WHERE id=?", (sid,))
        return cur.rowcount > 0


# ---------------- works(项目墙) ----------------

def get_works():
    with get_db() as c:
        rows = c.execute("SELECT * FROM works ORDER BY sort, id").fetchall()
        return [dict(r) for r in rows]


def insert_work(item):
    with get_db() as c:
        cur = c.execute(
            "INSERT INTO works(emoji,cover,title,desc,pill,link,sort) VALUES(?,?,?,?,?,?,?)",
            (item.get("emoji", "🛠️"), item.get("cover", "pink"), item.get("title", ""),
             item.get("desc", ""), item.get("pill", "进行中"), item.get("link", ""),
             int(item.get("sort", 99))))
        row = c.execute("SELECT * FROM works WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_work(wid, item):
    with get_db() as c:
        row = c.execute("SELECT * FROM works WHERE id=?", (wid,)).fetchone()
        if not row:
            return None
        merged = dict(row)
        merged.update({k: item[k] for k in
                       ("emoji", "cover", "title", "desc", "pill", "link") if k in item})
        if "sort" in item:
            merged["sort"] = int(item["sort"])
        c.execute(
            "UPDATE works SET emoji=?,cover=?,title=?,desc=?,pill=?,link=?,sort=? WHERE id=?",
            (merged["emoji"], merged["cover"], merged["title"], merged["desc"],
             merged["pill"], merged["link"], merged["sort"], wid))
        return merged


def delete_work(wid):
    with get_db() as c:
        cur = c.execute("DELETE FROM works WHERE id=?", (wid,))
        return cur.rowcount > 0


# ---------------- profile(关于我 / 信息卡片) ----------------

def get_profile():
    with get_db() as c:
        rows = c.execute("SELECT * FROM profile ORDER BY kind, sort, id").fetchall()
        return [dict(r) for r in rows]


def insert_profile(item):
    with get_db() as c:
        cur = c.execute(
            "INSERT INTO profile(kind,emoji,label,value,sort) VALUES(?,?,?,?,?)",
            (item.get("kind", "info"), item.get("emoji", ""), item.get("label", ""),
             item.get("value", ""), int(item.get("sort", 99))))
        row = c.execute("SELECT * FROM profile WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_profile(pid, item):
    with get_db() as c:
        row = c.execute("SELECT * FROM profile WHERE id=?", (pid,)).fetchone()
        if not row:
            return None
        merged = dict(row)
        merged.update({k: item[k] for k in ("kind", "emoji", "label", "value") if k in item})
        if "sort" in item:
            merged["sort"] = int(item["sort"])
        c.execute("UPDATE profile SET kind=?,emoji=?,label=?,value=?,sort=? WHERE id=?",
                  (merged["kind"], merged["emoji"], merged["label"], merged["value"],
                   merged["sort"], pid))
        return merged


def delete_profile(pid):
    with get_db() as c:
        cur = c.execute("DELETE FROM profile WHERE id=?", (pid,))
        return cur.rowcount > 0


# ---------------- 备份导入 ----------------

IMPORT_FIELDS = {
    "skills": ("name", "percent", "note", "category", "color", "sort"),
    "timeline": ("emoji", "time_label", "title", "content", "sort"),
    "stats": ("emoji", "number", "unit", "label", "sort"),
    "works": ("emoji", "cover", "title", "desc", "pill", "link", "sort"),
    "profile": ("kind", "emoji", "label", "value", "sort"),
}


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
                vals = tuple(row.get(f) for f in fields)
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


def record_visit(path: str, referer: str, ua: str, day: str, ts: int, city: str = ""):
    """记录一次访问。调用方负责把 referer 裁成域名,city 可为空(查不到就留空)。"""
    label, is_bot = _classify_ua(ua)
    with get_db() as c:
        c.execute(
            "INSERT INTO visits(day,ts,path,referer,ua,is_bot,city) VALUES(?,?,?,?,?,?,?)",
            (day, ts, path[:200], referer[:200], label[:60], is_bot, city[:40]))


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


def add_message(name: str, body: str, color: str = "", ip: str = "") -> dict:
    """公开写留言:默认进待审核池,返回脱敏后的记录"""
    import time as _t
    name = (name or "匿名").strip()[:MESSAGE_MAX_NAME] or "匿名"
    body = (body or "").strip()[:MESSAGE_MAX_BODY]
    if not body:
        return {"ok": False, "error": "内容不能为空"}
    if color not in MSG_COLORS:
        import random
        color = random.choice(MSG_COLORS)
    with get_db() as c:
        c.execute(
            "INSERT INTO messages(name,body,color,ts,ip,shown) VALUES(?,?,?,?,?,0)",
            (name, body, color, int(_t.time()), (ip or "")[:64]))
        mid = c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
    return {"ok": True, "id": mid, "name": name, "body": body, "color": color}


def list_messages_public(limit: int = 30) -> list:
    """前台:只给展示中的,新的在前"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,name,body,color,ts,reply FROM messages
               WHERE shown=1 ORDER BY ts DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


def list_messages_admin() -> list:
    """后台:全部状态,旧的待审核排前面方便处理"""
    with get_db() as c:
        rows = c.execute(
            """SELECT id,name,body,color,ts,ip,shown,reply FROM messages
               ORDER BY shown ASC, ts DESC LIMIT 500""").fetchall()
    return [dict(r) for r in rows]


def message_counts() -> dict:
    """后台卡片:待审 / 展示中 / 总数"""
    with get_db() as c:
        pending = c.execute(
            "SELECT COUNT(*) n FROM messages WHERE shown=0").fetchone()["n"]
        shown = c.execute(
            "SELECT COUNT(*) n FROM messages WHERE shown=1").fetchone()["n"]
        total = c.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
    return {"pending": pending, "shown": shown, "total": total}


def set_message_shown(mid: int, shown: int) -> bool:
    """审核:0 待审 / 1 展示 / 2 隐藏"""
    if shown not in (0, 1, 2):
        return False
    with get_db() as c:
        cur = c.execute("UPDATE messages SET shown=? WHERE id=?", (shown, mid))
        return cur.rowcount > 0


def reply_message(mid: int, reply: str) -> bool:
    reply = (reply or "").strip()[:140]
    with get_db() as c:
        cur = c.execute("UPDATE messages SET reply=? WHERE id=?", (reply, mid))
        return cur.rowcount > 0


def del_message(mid: int) -> bool:
    with get_db() as c:
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
