# ============================================================
# 图形验证码:纯标准库生成 SVG,零第三方依赖
# 不依赖 Pillow / 字体文件,服务器上直接能跑
# ============================================================

import os
import hmac
import time
import base64
import hashlib

# 去掉容易看错的字符:0/O、1/l/I、2/Z、5/S、8/B
ALPHABET = "ACDEFGHJKLMNPQRTUVWXY34679"

# 验证码有效期(秒)
CAPTCHA_TTL = 180


def _rand_text(n: int) -> str:
    # secrets 级随机
    return "".join(ALPHABET[os.urandom(1)[0] % len(ALPHABET)] for _ in range(n))


def _rand_int(a: int, b: int) -> int:
    return a + os.urandom(2)[0] % max(1, (b - a))


def make_captcha(length: int = 4) -> dict:
    """生成验证码

    返回 {token, svg}:token 是签名后的凭据,cookie 里另存答案哈希。
    """
    text = _rand_text(length)
    token = base64.urlsafe_b64encode(os.urandom(18)).decode().rstrip("=")
    return {"text": text, "token": token, "svg": _render_svg(text)}


def _render_svg(text: str) -> str:
    """把文字画成带干扰线的 SVG"""
    w, h = 130, 46
    n = len(text)
    slot = w / n

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="验证码">',
        f'<rect width="{w}" height="{h}" fill="#fff8ee" rx="8"/>',
    ]

    # 干扰线
    for _ in range(4):
        x1, y1 = _rand_int(0, w), _rand_int(0, h)
        x2, y2 = _rand_int(0, w), _rand_int(0, h)
        cx, cy = _rand_int(0, w), _rand_int(0, h)
        color = ["#ffd93d", "#2ec4b6", "#ff6b9d", "#a78bfa"][_rand_int(0, 4)]
        parts.append(
            f'<path d="M{x1},{y1} Q{cx},{cy} {x2},{y2}" fill="none" '
            f'stroke="{color}" stroke-width="1.4" opacity="0.55"/>')

    # 噪点
    for _ in range(26):
        parts.append(
            f'<circle cx="{_rand_int(0, w)}" cy="{_rand_int(0, h)}" r="1.1" '
            f'fill="#2d2a32" opacity="0.28"/>')

    # 字符:每个随机旋转、上下偏移、粗细变化
    palette = ["#2d2a32", "#1f6f66", "#8c2f5c", "#5b4a9e"]
    for i, ch in enumerate(text):
        cx = slot * i + slot / 2
        rot = _rand_int(-22, 23)
        dy = _rand_int(-4, 5)
        size = _rand_int(25, 31)
        weight = [600, 700, 800][_rand_int(0, 3)]
        parts.append(
            f'<text x="{cx:.1f}" y="{h/2 + dy:.1f}" font-size="{size}" '
            f'font-weight="{weight}" font-family="Baloo 2,Verdana,DejaVu Sans,sans-serif" '
            f'fill="{palette[_rand_int(0, len(palette))]}" text-anchor="middle" '
            f'dominant-baseline="central" '
            f'transform="rotate({rot} {cx:.1f} {h/2 + dy:.1f})">{ch}</text>')

    parts.append("</svg>")
    return "".join(parts)


def answer_digest(text: str) -> str:
    """验证码答案的摘要。不存明文,防数据库泄露后被直接读走。"""
    return hashlib.sha256(("cap:" + text.upper()).encode()).hexdigest()


def verify_captcha(given: str, expected_digest: str, issued_at) -> tuple[bool, str]:
    """校验验证码。返回 (是否通过, 失败原因)"""
    if not expected_digest:
        return False, "验证码已过期,请刷新"
    try:
        age = time.time() - float(issued_at or 0)
    except (TypeError, ValueError):
        return False, "验证码已过期,请刷新"
    if age > CAPTCHA_TTL:
        return False, "验证码已过期,请刷新"
    if not given:
        return False, "请填写验证码"
    got = answer_digest((given or "").strip())
    if not hmac.compare_digest(got, expected_digest):
        return False, "验证码不对,再看看?"
    return True, ""
