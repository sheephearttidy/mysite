#!/bin/bash
# v2.3 全量回归(测试环境;脚本都在 /tmp)
cd /tmp/testapp || exit 1
run() {
  local name="$1" path="$2"
  if [ -f "$path" ]; then
    echo "== $name: $(python3 "$path" 2>&1 | tail -1)"
  else
    echo "== $name: 脚本缺失($path)"
  fi
}
run pages_test    /tmp/pages_test.py
run split_check   /tmp/split_check.py
run sec_test      /tmp/sec_test.py
run test_v220     /tmp/test_v220.py
run test_v230     /tmp/test_v230.py
