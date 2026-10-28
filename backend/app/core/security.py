"""安全原语:密码哈希、会话令牌、限流与审计。

刻意保留与原实现相同的 PBKDF2 格式(`pbkdf2:iters:salt:hash`),
这样线上已有的密码哈希可以直接沿用,站主不用重置密码。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Final

PBKDF2_ITERS: Final = 120_000


# ---------------- 密码 ----------------


def hash_password(pwd: str, iters: int = PBKDF2_ITERS, salt: bytes | None = None) -> str:
    """返回 `pbkdf2:iters:salt_hex:hash_hex`,与原 db.py 格式一致。"""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, iters)
    return f"pbkdf2:{iters}:{salt.hex()}:{digest.hex()}"


def verify_password(pwd: str, stored: str) -> bool:
    """常量时间比较,防时序侧信道。"""
    if not stored:
        return False
    parts = stored.split(":")
    if len(parts) != 4 or parts[0] != "pbkdf2":
        return False
    _, iters, salt_hex, hash_hex = parts
    try:
        calc = hashlib.pbkdf2_hmac("sha256", pwd.encode(), bytes.fromhex(salt_hex), int(iters))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calc.hex(), hash_hex)


def password_strength_error(pwd: str) -> str | None:
    """返回错误文案,None 表示通过。规则与原版一致。"""
    if len(pwd) < 6:
        return "密码至少 6 位"
    if pwd.lower() == "admin":
        return "不能继续用初始密码 admin"
    if pwd.isdigit():
        return "密码不能全是数字"
    return None


# ---------------- 会话 ----------------


def new_session_id() -> str:
    """会话指纹:随机 32 字节,库里只存它,cookie 里存同一个值。"""
    return secrets.token_urlsafe(32)


def new_guest_token() -> str:
    """留言人凭证:凭它才能继续追问自己的留言。"""
    return secrets.token_urlsafe(18)


# ---------------- 图形验证码 ----------------


CAPTCHA_ALPHABET: Final = "ACDEFGHJKLMNPQRTUVWXY34679"


def captcha_code(length: int = 4) -> str:
    """去掉易混字符(0O1lI2Z5S8B)的随机码。"""
    return "".join(secrets.choice(CAPTCHA_ALPHABET) for _ in range(length))


def captcha_digest(code: str) -> str:
    """答案不存明文:sha256('cap:' + 大写答案)。"""
    return hashlib.sha256(f"cap:{code.upper()}".encode()).hexdigest()


# ---------------- 限流 ----------------


class RateLimiter:
    """进程内滑动窗口限流。

    单机 2 worker 场景够用;原实现也是进程内 + 落库混合。
    需要多机时换 Redis,接口不变。
    """

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str, limit: int, window_s: int) -> bool:
        now = time.time()
        cutoff = now - window_s
        bucket = [t for t in self._hits.get(key, []) if t > cutoff]
        if len(bucket) >= limit:
            self._hits[key] = bucket
            return False
        bucket.append(now)
        self._hits[key] = bucket
        return True

    def sweep(self, max_keys: int = 5000) -> None:
        """防止字典无限增长。"""
        if len(self._hits) <= max_keys:
            return
        now = time.time()
        self._hits = {
            k: [t for t in v if t > now - 3600]
            for k, v in self._hits.items()
        }
        self._hits = {k: v for k, v in self._hits.items() if v}


limiter = RateLimiter()
