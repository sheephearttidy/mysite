"""模型与真实数据库结构一致性校验。

比对 ORM 模型声明的列 vs SQLite 实际列,任何漂移都会在运行时炸掉。
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.models.models import Base  # noqa: E402

DB = sys.argv[1] if len(sys.argv) > 1 else "admin/data/mysite.db"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def main() -> int:
    path = Path(DB)
    print(f"数据库: {path.resolve()}")
    if not path.exists():
        print("!! 数据库不存在")
        return 1

    con = sqlite3.connect(str(path))
    actual: dict[str, dict[str, str]] = {}
    for (t,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ):
        cols = {}
        for row in con.execute(f"PRAGMA table_info({t})"):
            cols[row[1]] = row[2]
        actual[t] = cols
    con.close()

    print(f"实际表数: {len(actual)}  |  模型表数: {len(Base.metadata.tables)}")
    print()

    for name, table in sorted(Base.metadata.tables.items()):
        if name not in actual:
            ck(f"表 {name} 存在", False, "数据库中缺失")
            continue
        model_cols = {c.name for c in table.columns}
        db_cols = set(actual[name])
        if model_cols == db_cols:
            ck(f"表 {name} 列一致({len(model_cols)} 列)", True)
        else:
            only_model = sorted(model_cols - db_cols)
            only_db = sorted(db_cols - model_cols)
            ck(
                f"表 {name} 列一致",
                False,
                f"模型多出={only_model} 库多出={only_db}",
            )

    # 反向:库里有表但模型没映射
    unmapped = sorted(set(actual) - set(Base.metadata.tables))
    if unmapped:
        print()
        print("!! 库中未映射的表(可能有数据但接口读不到):")
        for t in unmapped:
            print("   ", t)

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
