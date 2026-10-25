#!/usr/bin/env python3
"""生产验证:统计修复效果"""
import json
import sys

sys.path.insert(0, "/var/www/mysite/admin")
import db

db.DB_PATH = "/var/www/mysite/admin/data/mysite.db"

P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


print("=== by_day 补零(7/30/90 天) ===")
for days in (7, 30, 90):
    d = db.get_visit_stats(days)
    bd = d["by_day"]
    ck(f"{days} 天返回 {days} 个点", len(bd) == days, f"实际 {len(bd)}")
    ck(f"{days} 天总和 = 真实访问", sum(x["n"] for x in bd) == d["total_real"],
       f'{sum(x["n"] for x in bd)} vs {d["total_real"]}')

print()
print("=== 7 天趋势(补零后) ===")
for x in db.get_visit_stats(7)["by_day"]:
    bar = "█" * min(x["n"], 30)
    print(f"  {x['day']}  {x['n']:3d} {bar}")

print()
print("=== 24 小时分布 ===")
d = db.get_visit_stats(30)
print("  非零:", {h: n for h, n in enumerate(d["by_hour"]) if n})
ck("24 个小时桶", len(d["by_hour"]) == 24, str(len(d["by_hour"])))

print()
print("=== 城市统计 ===")
print("  cities:", d["cities"])
ck("城市接口有数据或为空数组", isinstance(d["cities"], list))

print()
print("=== geo 新逻辑(真实 IP) ===")
import geo
for ip in ["223.104.101.73", "114.114.114.114", "59.82.83.223", "8.8.8.8"]:
    r = geo.locate(ip)
    print(f"  {ip:18s} -> {r!r}")
    ck(f"geo 解析 {ip}", bool(r), repr(r))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
