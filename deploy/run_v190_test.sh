#!/bin/bash
# v1.9.0 测试环境:更新代码 + 建表 + 重启 + 跑测试
set -e
cd /tmp/testapp

python3 - <<'PY'
import sys
sys.path.insert(0, "/tmp/testapp")
import db
db.init_db("/tmp/testapp/data/test.db")
print("建表 OK (messages + likes)")
PY

bash restart_test.sh > /dev/null 2>&1
sleep 1
TEST_PWD=admin python3 test_v190_api.py
