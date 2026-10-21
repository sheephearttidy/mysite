"""生成后台密码哈希:python gen_pass.py 你的密码
输出格式 pbkdf2:迭代次数:salt_hex:hash_hex,写进环境变量 MYSITE_ADMIN_PASS_HASH
"""
import hashlib
import os
import sys

pwd = sys.argv[1] if len(sys.argv) > 1 else ""
if not pwd:
    print("用法: python gen_pass.py 你的密码")
    sys.exit(1)

iters = 120_000
salt = os.urandom(16)
digest = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, iters)
print(f"pbkdf2:{iters}:{salt.hex()}:{digest.hex()}")

