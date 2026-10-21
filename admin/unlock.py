#!/usr/bin/env python3
"""
安全应急工具:在 SSH 里用,当把自己锁在门外时救命

用法:
  venv/bin/python unlock.py                    # 列出当前封锁的 IP
  venv/bin/python unlock.py 1.2.3.4            # 解除某个 IP
  venv/bin/python unlock.py --all              # 解除全部
  venv/bin/python unlock.py --sessions         # 列出登录会话
  venv/bin/python unlock.py --kill-all         # 踢掉所有会话
  venv/bin/python unlock.py --captcha off      # 临时关掉验证码
  venv/bin/python unlock.py --audit 30         # 看最近 30 条审计
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mysite.db")
db.init_db(DB_PATH)


def fmt_ts(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def show_blocked():
    rows = db.list_blocked()
    if not rows:
        print("当前没有封锁的 IP")
        return
    now = time.time()
    print(f"{'IP':<18} {'剩余':>10} {'失败次数':>10} {'最后尝试':<20}")
    print("-" * 62)
    for r in rows:
        left = int(r["blocked_until"] - now)
        print(f"{r['ip']:<18} {left//60:>7} 分 {r['count']:>10} "
              f"{fmt_ts(r['last_ts']):<20}")


def show_sessions():
    rows = db.list_sessions()
    if not rows:
        print("当前没有活跃会话")
        return
    print(f"{'会话 ID':<34} {'IP':<16} {'最后活动':<20} 设备")
    print("-" * 100)
    for r in rows:
        print(f"{r['sid'][:32]:<34} {r['ip']:<16} {fmt_ts(r['last_seen']):<20} "
              f"{(r['ua'] or '')[:30]}")


def show_audit(n=30):
    rows = db.list_audit(n)
    if not rows:
        print("没有审计记录")
        return
    print(f"{'时间':<20} {'操作':<16} {'IP':<16} 详情")
    print("-" * 90)
    for r in rows:
        print(f"{fmt_ts(r['ts']):<20} {r['action']:<16} {(r['ip'] or '-'):<16} "
              f"{r['detail'][:40]}")


def main():
    args = sys.argv[1:]
    if not args:
        show_blocked()
        return

    if args[0] == "--all":
        n = 0
        for r in db.list_blocked():
            db.unblock(r["ip"])
            n += 1
        print(f"已解除 {n} 个 IP 的封锁")
    elif args[0] == "--sessions":
        show_sessions()
    elif args[0] == "--kill-all":
        n = db.revoke_all_sessions()
        db.add_audit("cli_revoke_all", "cli", f"命令行踢掉全部会话({n} 个)", "unlock.py")
        print(f"已踢掉 {n} 个会话,所有设备都需要重新登录")
    elif args[0] == "--captcha":
        if len(args) < 2 or args[1] not in ("on", "off"):
            print("用法: --captcha on|off")
            return
        db.set_sec("sec_captcha", "1" if args[1] == "on" else "0")
        db.add_audit("cli_captcha", "cli", f"命令行把验证码设为 {args[1]}", "unlock.py")
        print(f"验证码已{'开启' if args[1] == 'on' else '关闭'}")
    elif args[0] == "--audit":
        n = int(args[1]) if len(args) > 1 else 30
        show_audit(n)
    elif args[0] in ("-h", "--help"):
        print(__doc__)
    else:
        ip = args[0]
        if db.unblock(ip):
            db.add_audit("cli_unblock", "cli", f"命令行解除封锁 {ip}", "unlock.py")
            print(f"已解除 {ip} 的封锁")
        else:
            print(f"{ip} 不在封锁列表中")


if __name__ == "__main__":
    main()
