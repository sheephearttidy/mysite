#!/bin/bash
# v2.0 自动备份:SQLite 在线备份(WAL 安全) + 保留最近 14 份
# crontab: 17 3 * * * /var/www/mysite/admin/backup_daily.sh >> /var/log/mysite_backup.log 2>&1
set -e
DB=/var/www/mysite/admin/data/mysite.db
OUTDIR=/var/www/mysite/admin/backups
KEEP=14
mkdir -p "$OUTDIR"
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="$OUTDIR/mysite-$STAMP.db"

python3 - "$DB" "$OUT" <<'PY'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
s = sqlite3.connect(src)
d = sqlite3.connect(dst)
s.backup(d)          # 在线备份 API,对 WAL 模式安全,不用停服务
d.close(); s.close()
print("backup ok ->", dst)
PY

gzip -f "$OUT"                       # 变成 .gz
ls -t "$OUTDIR"/mysite-*.db.gz | tail -n +$((KEEP+1)) | xargs -r rm -f
echo "$(date '+%F %T') 备份完成 $(du -h "$OUT.gz" | cut -f1), 保留 $(ls "$OUTDIR"/mysite-*.db.gz | wc -l) 份"
