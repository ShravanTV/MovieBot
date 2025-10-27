#!/bin/sh
set -e

# Default DB file
DB_FILE=${DB_FILE:-/data/moviedb.sqlite}

# Allow passing --force via env var
if [ "$FORCE_RECREATE" = "1" ]; then
  args="--force"
else
  args=""
fi

python db_manager.py --db "$DB_FILE" $args

# By default exit after import. Set KEEP_ALIVE=1 to keep container alive for inspection.
if [ "$KEEP_ALIVE" = "1" ]; then
  echo "KEEP_ALIVE=1, keeping container running"
  tail -f /dev/null
fi
