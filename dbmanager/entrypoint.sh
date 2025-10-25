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
tail -f /dev/null

# Wait for Ollama to be up
until curl -s http://ollama:11434 > /dev/null; do
  echo "Waiting for Ollama to be available..."
  sleep 2
done


echo "Ollama is up. Pulling llama2 model..."
# curl -X POST http://ollama:11434/api/pull -d '{"name": "nomic-embed-text"}' -H 'Content-Type: application/json'
curl -X POST http://ollama:11434/api/pull -d '{"name": "qwen3:0.6b"}' -H 'Content-Type: application/json'


# By default exit after import. Set KEEP_ALIVE=1 to keep container alive for inspection.
if [ "$KEEP_ALIVE" = "1" ]; then
  echo "KEEP_ALIVE=1, keeping container running"
  tail -f /dev/null
fi
