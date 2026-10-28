"""settings 表键名常量。

**必须与线上历史库保持一致** —— 这些键是 Flask 版本写入的,
改名会导致读不到数据(比如密码验证永远失败)。

集中定义,避免各处散落字符串拼错。
"""

from __future__ import annotations

from typing import Final

# ---------------- 认证 ----------------
KEY_PASS_HASH: Final = "pass_hash"                 # PBKDF2 哈希
KEY_MUST_CHANGE: Final = "must_change_pass"        # "1" = 下次登录必须改密

# ---------------- 安全 ----------------
KEY_CAPTCHA_ON: Final = "sec_captcha"              # 验证码开关
KEY_CAPTCHA_LEN: Final = "sec_captcha_len"         # 验证码位数 3~6
KEY_FAIL_THRESHOLD: Final = "sec_fail_threshold"   # 失败几次封锁
KEY_BLOCK_MINUTES: Final = "sec_block_minutes"     # 封锁时长(分钟)
KEY_SESSION_HOURS: Final = "sec_session_hours"     # 会话有效期(小时)
KEY_IDLE_MINUTES: Final = "sec_idle_minutes"       # 空闲登出(分钟)
KEY_AUDIT_KEEP: Final = "sec_audit_keep"           # 审计保留条数
KEY_PASS_MINLEN: Final = "sec_pass_minlen"         # 密码最小长度
KEY_PASS_CLASSES: Final = "sec_pass_classes"       # 至少几种字符
KEY_LOGIN_DELAY: Final = "sec_login_delay"         # 失败时延(秒)
KEY_BIND_IP: Final = "sec_bind_ip"                 # 会话绑 IP

# ---------------- 特效 ----------------
KEY_FX_MODE: Final = "fx_holiday_mode"             # auto / manual / off
KEY_FX_KEY: Final = "fx_holiday_key"               # manual 模式下选中的节日
KEY_FX_EFFECTS: Final = "fx_effects"               # 动效总开关
KEY_PET_MODE: Final = "pet_mode"                   # 桌宠开关

# ---------------- 2FA ----------------
KEY_TOTP_SECRET: Final = "totp_secret"
KEY_TOTP_PENDING: Final = "totp_pending"

# 验证码临时存储前缀(按会话指纹索引)
CAPTCHA_PREFIX: Final = "cap:"

# 站点信息前缀(9 个字段)
SITE_PREFIX: Final = "site_"
