#!/bin/bash
set -eu

python3 /submissionscript/db-upgrade.py $SCRIPT_PATH $MYSQL_USER $MYSQL_HOST $MYSQL_DATABASE $MYSQL_PASSWORD
sleep infinity