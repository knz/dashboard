#! /bin/sh
cd ~/src/dashboard
mkdir -p dashboard
../issue/issue -json ""|python3 json2sql.py|sqlite3 issues.db
python3 report.py
