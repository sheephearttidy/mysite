# ============================================================
# 数据库层:SQLite + 初始数据
# 所有函数线程安全(每次调用独立连接)
# ============================================================

import os
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
