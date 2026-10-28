"""部署一致性检查:本地代码 vs 线上实际运行的文件。

比对关键文件的 sha256,发现「本地改了但没部署」的漂移。
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REMOTE = "root@8.152.200.132"
SITE = "/var/www/mysite"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def local_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    # 本地:后端源码 + 前端产物
    files = []
    for p in Path("app").rglob("*.py"):
        files.append(("backend/" + p.as_posix(), p))
    files.append(("backend/seed.py", Path("seed.py")))
    files.append(("backend/requirements.txt", Path("requirements.txt")))

    dist = Path("../frontend/dist")
    if dist.is_dir():
        for p in dist.rglob("*"):
            if p.is_file():
                rel = p.relative_to(dist).as_posix()
                files.append(("dist/" + rel, p))

    # 线上哈希
    remote_paths = " ".join(f"{SITE}/{rp}" for rp, _ in files)
    cmd = (
        "for f in " + remote_paths + "; do "
        "if [ -f \"$f\" ]; then sha256sum \"$f\"; else echo \"MISSING $f\"; fi; done"
    )
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", REMOTE, cmd],
        capture_output=True, text=True, encoding="utf-8",
    )
    remote: dict[str, str] = {}
    for line in r.stdout.splitlines():
        if line.startswith("MISSING "):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and len(parts[0]) == 64:
            remote[parts[1].strip()] = parts[0]

    print(f"比对文件数: {len(files)}  |  线上返回: {len(remote)}")
    print()

    drift = []
    missing = []
    for rp, lp in files:
        full = f"{SITE}/{rp}"
        lh = local_hash(lp)
        rh = remote.get(full)
        if rh is None:
            missing.append(rp)
        elif rh != lh:
            drift.append(rp)

    if missing:
        print("!! 线上缺失:")
        for m in missing:
            print("   ", m)
    if drift:
        print("!! 内容不一致(本地改了没部署):")
        for d in drift:
            print("   ", d)

    ck("线上文件齐全", not missing, f"{len(missing)} 个缺失")
    ck("内容与本地一致", not drift, f"{len(drift)} 个漂移")

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
