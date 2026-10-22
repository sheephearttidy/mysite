#!/usr/bin/env python3
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
h = urllib.request.urlopen("https://imyxj.xyz/", timeout=20).read().decode()
for s in re.findall(r'src="([^"]+)"', h):
    if "js/" in s:
        print(s)
