#!/usr/bin/env python3
import time

print("服务器当前时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
print("当前 ts:", int(time.time()))
for t in (1792627461, 1792602177, 1792596618):
    print(f"ts {t} -> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))}")
print()
print("时区:", time.tzname)
