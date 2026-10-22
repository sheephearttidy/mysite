#!/bin/bash
# 测试环境完整回归基线
python3 /tmp/reset_testpwd.py >/dev/null 2>&1
cd /tmp/testapp || exit 1
echo -n "pages: "; python3 pages_test.py 2>&1 | tail -1
echo -n "split: "; python3 split_check.py 2>&1 | tail -1
echo -n "sec:   "; python3 sec_test.py 2>&1 | tail -1
echo -n "v220:  "; python3 /tmp/test_v220.py 2>&1 | tail -1
echo -n "v230:  "; python3 /tmp/test_v230.py 2>&1 | tail -1
# v240 必须在 /root 下跑:/tmp/testapp 作为 cwd 时 sys.path[0] 会指向它,
# 影响登录后的 session 复用(实测 401),换目录即可
python3 /tmp/reset_testpwd.py >/dev/null 2>&1
cd /root || exit 1
echo -n "v240:  "; python3 /tmp/test_v240.py 2>&1 | grep '结果:'
