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

# Wait for Ollama to be up
until curl -s http://ollama:11434 > /dev/null; do
  echo "Waiting for Ollama to be available..."
  sleep 2
done

OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5:7b}
echo "Ollama is up. Pulling model: $OLLAMA_MODEL ..."
curl -X POST http://ollama:11434/api/pull -d "{\"name\": \"$OLLAMA_MODEL\"}" -H 'Content-Type: application/json'


# By default exit after import. Set KEEP_ALIVE=1 to keep container alive for inspection.
if [ "$KEEP_ALIVE" = "1" ]; then
  echo "KEEP_ALIVE=1, keeping container running"
  tail -f /dev/null
fi
