"""文档一致性检查:README 里提到的命令/文件/路径是否真实存在。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("..").resolve()
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
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    deploy = (ROOT / "DEPLOY.md").read_text(encoding="utf-8")

    print("=" * 60)
    print("README 提到的路径是否存在")
    print("=" * 60)
    # 提取反引号里的文件/目录路径
    candidates = set()
    for m in re.finditer(r"`([a-zA-Z0-9_./-]+\.(?:py|ts|tsx|json|md|txt|conf|service|css|html))`", readme):
        candidates.add(m.group(1))
    for m in re.finditer(r"`(backend/[\w/.-]+|frontend/[\w/.-]+|deploy/[\w/.-]+)`", readme):
        candidates.add(m.group(1))

    for c in sorted(candidates):
        p = ROOT / c
        if p.exists():
            ck(f"{c}", True)
            continue
        # README 目录树里会写 app/ 内部的相对路径(如 api/content.py),
        # 这些相对 backend/app/ 解析
        if (ROOT / "backend" / "app" / c).exists():
            ck(f"{c} (= backend/app/{c})", True)
            continue
        if (ROOT / "backend" / c).exists():
            ck(f"{c} (= backend/{c})", True)
            continue
        ck(f"{c}", False, "不存在")

    print()
    print("=" * 60)
    print("README 提到的脚本命令")
    print("=" * 60)
    for m in re.finditer(r"python (backend/scripts/[\w.]+\.py|backend/seed\.py)", readme):
        script = m.group(1)
        ck(script, (ROOT / script).exists(), "文件不存在")

    print()
    print("=" * 60)
    print("DEPLOY.md 提到的路径")
    print("=" * 60)
    for m in re.finditer(r"`(backend/[\w/.-]+|frontend/[\w/.-]+|deploy/[\w/.-]+)`", deploy):
        c = m.group(1)
        ck(c, (ROOT / c).exists(), "不存在")

    print()
    print("=" * 60)
    print("文档里是否残留已删除的旧路径")
    print("=" * 60)
    stale = [
        "admin/app.py",
        "admin/db.py",
        "templates/front",
        "deploy/archive",
        "deploy/add_asset_ver.py",
        "deploy/ci_front_check.py",
        "deploy/check_panel_map.py",
        "tests/test_db.py",
        "admin/static",
    ]
    for s in stale:
        hit_readme = s in readme
        hit_deploy = s in deploy
        ck(f"README/DEPLOY 不含 {s}", not (hit_readme or hit_deploy),
           f"readme={hit_readme} deploy={hit_deploy}")

    print()
    print("=" * 60)
    print("版本号一致性")
    print("=" * 60)
    # package.json 版本 vs README 版本表
    import json

    pkg = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    ck("package.json 有 version", "version" in pkg, str(pkg.get("version")))
    main_py = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    m = re.search(r'version="([\d.]+)"', main_py)
    ck("main.py 有 version", bool(m), "")
    if m and "version" in pkg:
        ck("前后端版本号一致", pkg["version"] == m.group(1),
           f"pkg={pkg['version']} api={m.group(1)}")

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
