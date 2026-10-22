#!/usr/bin/env python3
"""geo 清洗规则单测(不联网,直接测函数)"""
import sys

sys.path.insert(0, "/tmp/geotest")
import geo

P = F = 0


def ck(n, got, want):
    global P, F
    if got == want:
        print(f"PASS  {n}: {got!r}")
        P += 1
    else:
        print(f"FAIL  {n}: got {got!r} want {want!r}")
        F += 1


print("=== _clean_city ===")
ck("杭州不裁州", geo._clean_city("杭州"), "杭州")
ck("广州不裁州", geo._clean_city("广州"), "广州")
ck("南京市裁市", geo._clean_city("南京市"), "南京")
ck("北京市直辖", geo._clean_city("北京市"), "北京")
ck("XX 视为空", geo._clean_city("XX"), "")
ck("空串", geo._clean_city(""), "")
ck("阿坝藏族羌族自治州", geo._clean_city("阿坝藏族羌族自治州"), "阿坝藏族羌族自治州")
ck("苏州不裁", geo._clean_city("苏州"), "苏州")
ck("通辽市", geo._clean_city("通辽市"), "通辽")

print("\n=== _clean_region ===")
ck("江苏省", geo._clean_region("江苏省"), "江苏")
ck("广西壮族自治区", geo._clean_region("广西壮族自治区"), "广西")
ck("香港特别行政区", geo._clean_region("香港特别行政区"), "香港")
ck("XX", geo._clean_region("XX"), "")

print("\n=== _join ===")
ck("省+市", geo._join("江苏省", "南京市"), "江苏 南京")
ck("只有市", geo._join("", "杭州"), "杭州")
ck("省市相同", geo._join("北京", "北京"), "北京")
ck("都是XX", geo._join("XX", "XX"), "")

print("\n=== _public_ipv4 ===")
ck("公网", geo._public_ipv4("114.114.114.114"), True)
ck("内网", geo._public_ipv4("192.168.1.1"), False)
ck("本机", geo._public_ipv4("127.0.0.1"), False)
ck("IPv6", geo._public_ipv4("2400:3200::1"), False)
ck("非法", geo._public_ipv4("not-an-ip"), False)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
