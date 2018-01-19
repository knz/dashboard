#! /bin/sh
ISSUE=${1:-issue}
mkdir -p dashboard
$ISSUE -json "" >data.json
python3 json2sql.py <data.json |sqlite3 issues.db
python3 report.py
cp sorttable.js dashboard/
