# ============================================================
# 数据库层:SQLite + 初始数据
# 所有函数线程安全(每次调用独立连接)
# ============================================================

import sqlite3
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
}


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
