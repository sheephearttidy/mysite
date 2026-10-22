#!/usr/bin/env python3
import datetime
import os
import time

print("TZ 环境变量:", os.environ.get("TZ"))
print("系统本地时间:", datetime.datetime.now())
print("北京时间    :", datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))))
print("time.strftime 今天:", time.strftime("%Y-%m-%d"))
print()
print("=> 如果系统时区是 UTC,time.strftime 的日期在北京时间 0-8 点会差一天")
print("   服务器当前时区:", time.tzname, "偏移:", time.timezone / -3600, "小时")
