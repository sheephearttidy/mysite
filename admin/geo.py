# ============================================================
# IP 定位模块:多源解析,失败短缓存,绝不阻塞访问统计
# - 主源:淘宝 IP API(免费、国内快、无 key)
# - 备源:ip-api.com(国外,支持 HTTPS 免费,境内也能通)
# - 成功缓存 30 天;失败只缓存 5 分钟(避免限流期间永久记空)
# - 纯标准库 urllib,零第三方依赖
# - 隐私:只取 省/市,不落 IP 原文(仅用于查询)
# ============================================================

import ipaddress
import json
import threading
import time
import urllib.request

# 主源:淘宝(国内准确度高)
_TAOBAO = "https://ip.taobao.com/outGetIpInfo?ip={ip}&accessKey=alibaba-inc"
# 备源:ip-api.com(字段干净,免费额度 45 次/分钟)
_IPAPI = "http://ip-api.com/json/{ip}?lang=zh-CN&fields=status,country,regionName,city,message"

_TIMEOUT = 3.0
_MAX_CACHE = 1000
_OK_TTL = 86400 * 30      # 解析成功:缓存 30 天
_FAIL_TTL = 300           # 解析失败:只缓存 5 分钟,稍后自动重试

_lock = threading.Lock()
_cache = {}          # ip -> (city, ts)
_ordered = []        # 最近使用顺序(近似 LRU)


def _public_ipv4(ip: str) -> bool:
    """只解析公网 IPv4;内网/本机/保留地址一律跳过"""
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False
    return addr.version == 4 and addr.is_global


def _clean_region(region: str) -> str:
    """省名清洗:去行政后缀,XX 视为空"""
    region = (region or "").strip()
    if region in ("", "XX"):
        return ""
    # 长的先裁(自治区 > 特别行政区 > 省),避免「广西壮族自治区」只裁掉「区」
    for suf in ("维吾尔自治区", "壮族自治区", "回族自治区", "自治区",
                "特别行政区", "省"):
        if region.endswith(suf) and len(region) > len(suf):
            region = region[: -len(suf)]
            break
    return region


def _clean_city(city: str) -> str:
    """市名清洗:去 '市/地区/盟' 后缀,XX 视为空,直辖市保留原名"""
    city = (city or "").strip()
    if city in ("", "XX"):
        return ""
    if city in ("北京市", "上海市", "天津市", "重庆市"):
        return city[:2]
    # 注意:只裁明确的行政后缀,不能裁「州」——否则杭州变杭、广州变广
    for suf in ("市", "地区", "盟"):
        if city.endswith(suf) and len(city) > len(suf) + 1:
            city = city[: -len(suf)]
            break
    return "" if city == "XX" else city


def _join(region: str, city: str) -> str:
    """拼成 '省 市';省市相同时只留一个"""
    region, city = _clean_region(region), _clean_city(city)
    if region and city and region != city:
        return f"{region} {city}"
    return city or region


def _fetch_taobao(ip: str) -> str:
    req = urllib.request.Request(_TAOBAO.format(ip=ip), headers={
        "User-Agent": "Mozilla/5.0 (compatible; mysite-geo)"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    if data.get("code") != 0:
        return ""
    d = data.get("data") or {}
    country = (d.get("country") or "").strip()
    region, city = d.get("region", ""), d.get("city", "")

    # 港澳台:直接返回地区名
    if country in ("香港", "澳门", "台湾"):
        return country

    # 国外:淘宝常不给 country(如 region=佛罗里达 city=迈阿密),
    # 这种情况交给备源(ip-api 有 country 字段),返回空让它接手
    if country and country != "中国":
        c = _clean_city(city)
        if c and c != country:
            return f"{country} {c}"
        r2 = _clean_city(region)
        return f"{country} {r2}" if r2 and r2 != country else country

    if not country:
        # 没国家名:大概率是国外(国内 IP 淘宝一般给 country=中国),
        # 直接返回空,让备源用 country 字段补全
        return ""

    # 国内
    return _join(region, city)


def _fetch_ipapi(ip: str) -> str:
    req = urllib.request.Request(_IPAPI.format(ip=ip), headers={
        "User-Agent": "Mozilla/5.0 (compatible; mysite-geo)"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    if data.get("status") != "success":
        return ""
    country = (data.get("country") or "").strip()
    region = data.get("regionName") or ""
    city = data.get("city") or ""

    if not country:
        return _join(region, city)

    # 港澳台:国家名本身够用,不再拼区名(避免「香港 Sheung Wan」)
    if country in ("香港", "澳门", "台湾"):
        return country

    # 国外:国家 + 城市(城市名可能是片区,保留但用国家前缀)
    if country != "中国":
        c = _clean_city(city)
        if c and c != country:
            return f"{country} {c}"
        r2 = _clean_city(region)
        return f"{country} {r2}" if r2 and r2 != country else country

    # 国内:省 市
    return _join(region, city)


def _fetch_city(ip: str) -> str:
    """主源失败自动切备源;全失败返回 ''"""
    for fn in (_fetch_taobao, _fetch_ipapi):
        try:
            city = fn(ip)
            if city:
                return city
        except Exception:
            continue
    return ""


def _cache_get(ip: str):
    """命中返回城市串;未命中返回 None(空城市也按 TTL 区分)"""
    now = time.time()
    hit = _cache.get(ip)
    if hit:
        city, ts = hit
        ttl = _OK_TTL if city else _FAIL_TTL   # 失败短缓存,5 分钟后重试
        if now - ts < ttl:
            _touch(ip)
            return city
        _cache.pop(ip, None)
    return None


def _touch(ip: str):
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
    city = _fetch_city(ip)   # 锁外查询,避免阻塞其他线程
    with _lock:
        _cache_put(ip, city)
    return city


def stats() -> dict:
    """给后台/诊断用:缓存里有几个成功、几个失败"""
    with _lock:
        ok = sum(1 for c, _ in _cache.values() if c)
        fail = len(_cache) - ok
    return {"cached_ok": ok, "cached_fail": fail, "total": len(_cache)}
