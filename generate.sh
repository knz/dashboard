#! /bin/sh
ISSUE=${1:-issue}

unset $(env | grep LC_ | cut -d= -f1)
# Needed for report.py below.
export LANG=en_US.UTF-8

set -eui

mkdir -p dashboard
$ISSUE -json "" >data.json
python3 json2sql.py <data.json >data.sql
sqlite3 issues.db <data.sql
python3 report.py
cp -f sorttable.js dashboard/
