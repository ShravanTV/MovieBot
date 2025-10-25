FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db_manager.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

VOLUME /data

ENTRYPOINT ["/app/entrypoint.sh"]
