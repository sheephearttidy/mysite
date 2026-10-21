# ============================================================
# IP 定位模块:淘宝 IP API(免费、国内快、无 key)
# - 纯标准库 urllib,零第三方依赖
# - 内存缓存(同 IP 只查一次,上限 1000)
# - 查询失败静默返回 ""(绝不阻塞访问统计)
# - 隐私:只取 省/市,不落 IP 原文(仅用于查询)
# ============================================================

import ipaddress
import json
import threading
import time
import urllib.request

_API_URL = "https://ip.taobao.com/outGetIpInfo?ip={ip}&accessKey=alibaba-inc"
_TIMEOUT = 2.0  # 单次查询超时,别让统计等太久
_MAX_CACHE = 1000

_lock = threading.Lock()
_cache = {}          # ip -> (city, ts)  简单 LRU 靠顺序
_ordered = []        # 最近使用顺序(维护插入序)


def _public_ipv4(ip: str) -> bool:
    """只解析公网 IPv4;内网/本机/保留地址一律跳过"""
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False
    return addr.version == 4 and addr.is_global


def _fetch_city(ip: str) -> str:
    """调淘宝 API 拿 '省 市'(如 '江苏 南京');失败/查不到返回 ''"""
    try:
        req = urllib.request.Request(_API_URL.format(ip=ip), headers={
            "User-Agent": "Mozilla/5.0 (compatible; mysite-geo)"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        d = data.get("data") or {}
        region, city = d.get("region", ""), d.get("city", "")
        # 淘宝对查不到的 IP 返回 XX 占位,视为无效
        if region in ("", "XX") and city in ("", "XX"):
            return ""
        # 城市可能带 "市" 后缀(南京/南京市),裁掉;直辖市(北京/上海/重庆)只留城市名
        if city in ("北京市", "上海市", "天津市", "重庆市"):
            return city[:2] if city == "北京市" else city[:2]
        city = city.replace("市", "").replace("地区", "").replace("盟", "")
        if city == "XX":
            city = ""
        if region and region != city:
            # 省名有时带 "省"(江苏/江苏省)
            region = region.replace("省", "")
            if region == "XX":
                region = ""
            if city:
                return f"{region} {city}"
            return region
        return city or region
    except Exception:
        return ""


def _cache_get(ip: str):
    """命中返回城市串;未命中返回 None(注意:空城市也是有效命中)"""
    now = time.time()
    hit = _cache.get(ip)
    if hit:
        city, ts = hit
        if now - ts < 86400 * 30:   # 缓存 30 天
            _touch(ip)
            return city
        _cache.pop(ip, None)
    return None


def _touch(ip: str):
    """把 ip 挪到有序列表末尾(近似 LRU)"""
    try:
        _ordered.remove(ip)
    except ValueError:
        pass
    _ordered.append(ip)
    while len(_ordered) > _MAX_CACHE:
        old = _ordered.pop(0)
        _cache.pop(old, None)


def _cache_put(ip: str, city: str):
    _cache[ip] = (city, time.time())
    _touch(ip)


def locate(ip: str) -> str:
    """对外主入口:给定 IP 返回 '省 市' 或 ''(不可查/失败)"""
    ip = (ip or "").strip()
    if not _public_ipv4(ip):
        return ""
    with _lock:
        city = _cache_get(ip)
        if city is not None:
            return city
    # 缓存未命中,网络查询(锁外,避免阻塞其他线程)
    city = _fetch_city(ip)
    with _lock:
        _cache_put(ip, city)
    return city
