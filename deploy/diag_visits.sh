#!/bin/bash
DB=/var/www/mysite/admin/data/mysite.db
echo "=== visits 表结构 ==="
sqlite3 "$DB" ".schema visits"
echo
echo "=== 总行数 ==="
sqlite3 "$DB" "SELECT COUNT(*) FROM visits;"
echo
echo "=== 按 path 分组 ==="
sqlite3 "$DB" "SELECT path, COUNT(*) FROM visits GROUP BY path ORDER BY 2 DESC;"
echo
echo "=== 按 city 分组(空显示为 空) ==="
sqlite3 "$DB" "SELECT CASE WHEN city IS NULL OR city='' THEN '(空)' ELSE city END AS c, COUNT(*) FROM visits GROUP BY c ORDER BY 2 DESC;"
echo
echo "=== is_bot 分布 ==="
sqlite3 "$DB" "SELECT is_bot, COUNT(*) FROM visits GROUP BY is_bot;"
echo
echo "=== 最近 15 条 ==="
sqlite3 -header "$DB" "SELECT id,path,city,is_bot,day,ts FROM visits ORDER BY id DESC LIMIT 15;"
echo
echo "=== day 分布(最近10天) ==="
sqlite3 "$DB" "SELECT day, COUNT(*) FROM visits GROUP BY day ORDER BY day DESC LIMIT 10;"
