#!/usr/bin/env python
"""数据库初始化 / 重置脚本。

用途:
1. 新环境首次建库(没有表时自动建表 + 灌示例内容)
2. 重置后台密码(默认 admin,并强制下次登录改密)
3. 迁移旧键名(admin_password -> pass_hash 等,兼容历史库)

用法:
    python seed.py                      # 建表 + 灌示例数据(幂等)
    python seed.py --reset-password     # 把密码重置为 admin 并强制改密
    python seed.py --password 新密码    # 设为指定密码(仍强制改密)
    python seed.py --db 路径            # 指定数据库文件

设计说明:
- 幂等:重复执行不会重复插入内容
- 不覆盖已有密码:除非显式 --reset-password / --password
- 键名与线上历史库保持一致(pass_hash / must_change_pass / sec_captcha)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core import keys as K  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import models as m  # noqa: E402

# ---------------- 默认设置 ----------------

# 键名必须与线上历史库一致,否则老库读不到
DEFAULT_SETTINGS = {
    # 站点信息
    "site_owner": "至尊杰",
    "site_name": "至尊杰的小窝",
    "site_school": "燕京理工学院",
    "site_major": "计算机科学与技术",
    "site_grade": "2026 级",
    "site_focus": "智能车 AI",
    "site_slogan": "learning and building",
    "site_credit": "纯手搓 + AI 协作",
    "site_start_year": "2026",
    # 前台特效
    "fx_holiday_mode": "auto",
    "fx_holiday_key": "",
    "fx_effects": "1",
    "pet_mode": "on",
    # 安全
    "sec_captcha": "1",
    "sec_captcha_len": "4",
    "sec_fail_threshold": "5",
    "sec_block_minutes": "15",
    "sec_session_hours": "168",
    "sec_idle_minutes": "60",
    "sec_audit_keep": "500",
    "sec_pass_minlen": "8",
    "sec_pass_classes": "2",
    "sec_login_delay": "1",
    "sec_bind_ip": "0",
}

# ---------------- 示例内容 ----------------

SEED = {
    "skills": [
        ("🏎️ 智能车 / 嵌入式", 78, "主线任务,小车就是我的另一半", "serious", "teal", 1),
        ("🐍 Python", 75, "调车、调 AI、调 DeepSeek 都靠它", "serious", "blue", 2),
        ("⚙️ C / C++", 72, "写底层的感觉,又痛又上头", "serious", "pink", 3),
        ("🌐 全栈开发", 65, "React / FastAPI / 前端三件套", "serious", "purple", 4),
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
        ("💬", 1000, " 条", "调教 AI 的 prompt", 3),
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
         "React + FastAPI 练手,从接口到页面一手包办,顺便练部署。",
         "练手作", "https://github.com/sheephearttidy", 3),
        ("💻", "purple", "GitHub 仓库",
         "所有公开代码都在 @sheephearttidy,欢迎来逛,点个 star 就是最大的鼓励。",
         "持续更新", "https://github.com/sheephearttidy", 4),
        ("📄", "orange", "这个网页本身",
         "React SPA + FastAPI 重构版,贴纸风视觉,支持暗色模式。",
         "你现在看着呢", "https://github.com/sheephearttidy", 5),
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
        ("🛠️", "今天给小车换了新的循迹算法,弯道终于不画龙了!", "teal", 1),
        ("🌙", "凌晨的实验室和泡面更配,代码跑通那一刻什么都值了。", "purple", 2),
        ("📚", "期末周生存指南:把「临时抱佛脚」拆成每天抱一点点。", "yellow", 3),
    ],
    "friendlinks": [
        ("GitHub", "https://github.com/sheephearttidy", "🐙", "我的全部公开代码都在这里", 1),
        ("DeepSeek", "https://chat.deepseek.com", "🐋", "写代码与改 bug 的最佳搭子", 2),
    ],
    "songs": [
        ("晴天", "周杰伦", "🌧️", "97773", "写代码循环曲第一名", 1),
    ],
}


def seed_content(db) -> None:
    """灌入示例内容。只在该表为空时插入,避免重复。"""
    inserted = {}

    def add_if_empty(table, model, rows, build):
        exists = db.scalar(select(model).limit(1))
        if exists is not None:
            return 0
        for row in rows:
            db.add(build(row))
        return len(rows)

    inserted["skills"] = add_if_empty(
        "skills", m.Skill, SEED["skills"],
        lambda r: m.Skill(name=r[0], percent=r[1], note=r[2], category=r[3], color=r[4], sort=r[5]),
    )
    inserted["timeline"] = add_if_empty(
        "timeline", m.TimelineItem, SEED["timeline"],
        lambda r: m.TimelineItem(emoji=r[0], time_label=r[1], title=r[2], content=r[3], sort=r[4]),
    )
    inserted["stats"] = add_if_empty(
        "stats", m.Stat, SEED["stats"],
        lambda r: m.Stat(emoji=r[0], number=r[1], unit=r[2], label=r[3], sort=r[4]),
    )
    inserted["works"] = add_if_empty(
        "works", m.Work, SEED["works"],
        lambda r: m.Work(emoji=r[0], cover=r[1], title=r[2], desc=r[3], pill=r[4], link=r[5], sort=r[6]),
    )
    inserted["profile"] = add_if_empty(
        "profile", m.ProfileItem, SEED["profile"],
        lambda r: m.ProfileItem(kind=r[0], emoji=r[1], label=r[2], value=r[3], sort=r[4]),
    )
    inserted["honors"] = add_if_empty(
        "honors", m.Honor, SEED["honors"],
        lambda r: m.Honor(emoji=r[0], year=r[1], title=r[2], desc=r[3], level=r[4], sort=r[5]),
    )

    if db.scalar(select(m.Note).limit(1)) is None:
        now = int(time.time())
        for i, (emoji, text, mood, sort) in enumerate(SEED["notes"]):
            db.add(m.Note(emoji=emoji, text=text, mood=mood, ts=now - i * 86400, sort=sort))
        inserted["notes"] = len(SEED["notes"])

    inserted["friendlinks"] = add_if_empty(
        "friendlinks", m.FriendLink, SEED["friendlinks"],
        lambda r: m.FriendLink(name=r[0], url=r[1], emoji=r[2], desc=r[3], sort=r[4]),
    )
    inserted["songs"] = add_if_empty(
        "songs", m.Song, SEED["songs"],
        lambda r: m.Song(title=r[0], artist=r[1], emoji=r[2], song_id=r[3], note=r[4], sort=r[5]),
    )

    db.commit()
    total = sum(v for v in inserted.values() if v)
    if total:
        detail = ", ".join(f"{k}+{v}" for k, v in inserted.items() if v)
        print(f"✓ 示例内容已灌入({detail})")
    else:
        print("✓ 内容已存在,跳过灌入")


def seed_settings(db) -> None:
    """补齐缺失的默认设置,不覆盖已有值。"""
    existing = {r.key for r in db.scalars(select(m.Setting)).all()}
    added = []
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            db.add(m.Setting(key=key, value=value))
            added.append(key)
    db.commit()
    if added:
        print(f"✓ 补充默认设置 {len(added)} 项")
    else:
        print("✓ 设置已完整")


# ---------------- 密码 ----------------


def set_admin_password(db, password: str, *, force_change: bool = True) -> None:
    """设置后台密码。

    键名用 pass_hash / must_change_pass,与线上历史库保持一致。
    """
    row = db.get(m.Setting, "pass_hash")
    if row is None:
        db.add(m.Setting(key="pass_hash", value=hash_password(password)))
    else:
        row.value = hash_password(password)

    mc = db.get(m.Setting, "must_change_pass")
    flag = "1" if force_change else "0"
    if mc is None:
        db.add(m.Setting(key="must_change_pass", value=flag))
    else:
        mc.value = flag

    db.commit()
    state = "下次登录必须改密" if force_change else "无需改密"
    print(f"✓ 后台密码已设置({state})")


def migrate_legacy_keys(db) -> None:
    """把新代码曾误用的键名迁回历史键名(修历史库兼容问题)。"""
    mapping = {
        "admin_password": "pass_hash",
        "must_change_pwd": "must_change_pass",
    }
    moved = []
    for old, new in mapping.items():
        old_row = db.get(m.Setting, old)
        if old_row is None:
            continue
        new_row = db.get(m.Setting, new)
        if new_row is None:
            db.add(m.Setting(key=new, value=old_row.value))
            moved.append(f"{old} -> {new}")
        db.delete(old_row)
    if moved:
        db.commit()
        print(f"✓ 迁移旧键名:{', '.join(moved)}")


# ---------------- 入口 ----------------


def main() -> int:
    ap = argparse.ArgumentParser(description="数据库初始化与密码重置")
    ap.add_argument("--db", help="SQLite 文件路径(默认取 MYSITE_DB_PATH 或 admin/data/mysite.db)")
    ap.add_argument("--reset-password", action="store_true", help="重置密码为 admin 并强制改密")
    ap.add_argument("--password", help="设置指定密码(仍强制下次改密)")
    ap.add_argument("--no-seed", action="store_true", help="只建表与设置,不灌示例内容")
    args = ap.parse_args()

    # 用独立 engine,不复用全局单例 —— 否则 --db 指定别的库时不生效
    db_path = args.db or os.environ.get("MYSITE_DB_PATH") or str(settings.db_file)
    db_file = Path(db_path).expanduser().resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"数据库:{db_file}")

    # Windows 路径含反斜杠,直接拼进 SQLite URL 会被当转义序列,必须转 POSIX 形式
    local_engine = create_engine(
        "sqlite:///" + db_file.as_posix(),
        connect_args={"check_same_thread": False, "timeout": 15},
        future=True,
    )
    local_session = sessionmaker(
        bind=local_engine, autoflush=False, expire_on_commit=False, future=True
    )

    # 建表
    m.Base.metadata.create_all(local_engine)
    print(f"✓ 表结构就绪({len(m.Base.metadata.tables)} 张)")

    db = local_session()
    try:
        migrate_legacy_keys(db)
        seed_settings(db)
        if not args.no_seed:
            seed_content(db)

        # 密码:仅在显式要求或从未设置时初始化
        has_pwd = db.get(m.Setting, K.KEY_PASS_HASH) is not None
        if args.password:
            set_admin_password(db, args.password, force_change=True)
        elif args.reset_password:
            set_admin_password(db, "admin", force_change=True)
        elif not has_pwd:
            set_admin_password(db, "admin", force_change=True)
            print("  (首次初始化,初始密码 admin)")
        else:
            print("✓ 已有密码,保持不动(要重置用 --reset-password)")
    finally:
        db.close()

    print("\n完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
