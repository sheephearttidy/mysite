"""前后端接口契约检查:前端调用的每个路径,后端是否真的存在。

扫前端源码里的 api.get/post/put/del 与 fetch 调用,和 OpenAPI schema 比对。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.main import app  # noqa: E402

FRONTEND = Path("../frontend/src")

# 从 OpenAPI 拿到所有已注册路径
paths = set(app.openapi().get("paths", {}).keys())


def normalize(p: str) -> str:
    """把 /api/content/${kind} 这类模板替换成 {x} 形式,并剥掉查询串。"""
    p = p.split("?")[0]  # 去掉 ?action=xxx 这类查询参数
    p = re.sub(r"\$\{[^}]+\}", "{x}", p)
    p = re.sub(r"\{[^}]+\}", "{x}", p)
    return p


def match_front(path: str) -> bool:
    """前端路径是否能在后端找到对应(允许路径参数)。"""
    f = normalize(path)
    for bp in paths:
        if normalize(bp) == f:
            return True
    # 前缀匹配:/api/content/xxx/1 -> /api/content/{kind}/{item_id}
    fparts = f.strip("/").split("/")
    for bp in paths:
        bparts = bp.strip("/").split("/")
        if len(bparts) != len(fparts):
            continue
        if all(b == "{x}" or b == "{kind}" or b == "{item_id}" or b == "{name}"
               or b == "{mid}" or b == "{qid}" or b == "{nid}" or b == "{cid}"
               or b == "{pid}" or b == "{did}" or b == "{sid}" or b == "{full_path:path}"
               or b == fp
               for b, fp in zip(bparts, fparts)):
            return True
    return False


def main() -> int:
    calls: list[tuple[str, str, str]] = []  # (file, method, path)

    pat = re.compile(
        r"""api\.(get|post|put|del)\s*(?:<[^>]*>)?\s*\(\s*[`'"]([^`'"]+)[`'"]"""
    )
    fetch_pat = re.compile(r"""fetch\s*\(\s*[`'"](/api/[^`'"]+)[`'"]""")

    for f in FRONTEND.rglob("*.ts*"):
        src = f.read_text(encoding="utf-8", errors="replace")
        for m in pat.finditer(src):
            method = m.group(1).upper().replace("DEL", "DELETE")
            path = m.group(2)
            if path.startswith("/api"):
                calls.append((str(f.relative_to(FRONTEND)), method, path))
        for m in fetch_pat.finditer(src):
            calls.append((str(f.relative_to(FRONTEND)), "FETCH", m.group(1)))

    print(f"后端注册路径: {len(paths)}")
    print(f"前端调用点: {len(calls)}")
    print()

    missing = []
    seen = set()
    for file, method, path in sorted(set(calls)):
        key = (method, path)
        if key in seen:
            continue
        seen.add(key)
        ok = match_front(path)
        flag = "OK  " if ok else "MISS"
        print(f"{flag} {method:7s} {path:46s} ({file})")
        if not ok:
            missing.append((method, path, file))

    print()
    if missing:
        print(f"!! {len(missing)} 个前端调用在后端找不到:")
        for m, p, f in missing:
            print(f"   {m} {p}  <- {f}")
        return 1
    print("前后端接口契约一致 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
