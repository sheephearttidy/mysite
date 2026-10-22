#!/usr/bin/env python3
"""v2.0:TOTP 两步验证(RFC 6238,纯标准库)
- 密钥生成(base32, 20 字节)
- otpauth:// URI(手机验证器扫码用)
- 6 位码校验(±1 个时间窗容错)
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time


def generate_secret() -> str:
    """生成新密钥(存储格式:base32 无填充)"""
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _code_at(secret_b32: str, counter: int) -> str:
    pad = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32 + pad)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def verify(secret_b32: str, code: str, window: int = 1) -> bool:
    """校验 6 位码;允许前后 window 个 30 秒窗(防手机/服务器时钟漂移)"""
    if not code or not secret_b32:
        return False
    code = str(code).strip().replace(" ", "")
    if not code.isdigit() or len(code) != 6:
        return False
    counter = int(time.time()) // 30
    return any(hmac.compare_digest(_code_at(secret_b32, counter + i), code)
               for i in range(-window, window + 1))


def otpauth_uri(secret_b32: str, account: str, issuer: str = "imyxj.xyz") -> str:
    from urllib.parse import quote
    return (f"otpauth://totp/{quote(issuer)}:{quote(account)}"
            f"?secret={secret_b32}&issuer={quote(issuer)}&algorithm=SHA1"
            f"&digits=6&period=30")


if __name__ == "__main__":
    s = generate_secret()
    print("secret:", s)
    print("uri   :", otpauth_uri(s, "zhishengjie", "imyxj.xyz"))
    print("self  :", verify(s, _code_at(s, int(time.time()) // 30)))
