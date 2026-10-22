#!/bin/bash
cd /tmp/testapp || exit 1
for t in fx_test pages_test map_test sec_test theme_test front_theme_test split_check; do
  printf '%-18s ' "$t"
  python3 "$t.py" 2>&1 | grep -E '通过 [0-9]+ 项' | tail -1
done
