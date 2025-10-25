#!/usr/bin/env python3
"""Create SQLite schema and import CSV files from ml-latest-small into the DB.

Tables: movies, ratings, tags, links

Usage: python db_manager.py --db /data/moviedb.sqlite [--force]
"""
import os
import sqlite3
import csv
import re
import argparse

CSV_DIR = "./ml-latest-small"

SCHEMA = {
    "movies": """
        CREATE TABLE IF NOT EXISTS movies (
            movieId INTEGER PRIMARY KEY,
            title TEXT,
            year INTEGER,
            genres TEXT
        )
    """,
    "ratings": """
        CREATE TABLE IF NOT EXISTS ratings (
            userId INTEGER,
            movieId INTEGER,
            rating REAL,
            timestamp INTEGER,
            PRIMARY KEY (userId, movieId),
            FOREIGN KEY (movieId) REFERENCES movies(movieId)
        )
    """,
    "tags": """
        CREATE TABLE IF NOT EXISTS tags (
            userId INTEGER,
            movieId INTEGER,
            tag TEXT,
            timestamp INTEGER,
            PRIMARY KEY (userId, movieId, tag),
            FOREIGN KEY (movieId) REFERENCES movies(movieId)
        )
    """,
    "links": """
        CREATE TABLE IF NOT EXISTS links (
            movieId INTEGER PRIMARY KEY,
            imdbId INTEGER,
            tmdbId INTEGER,
            FOREIGN KEY (movieId) REFERENCES movies(movieId)
        )
    """
}

CSV_TO_TABLE = {
    'movies.csv': ('movies', ['movieId','title','genres']),
    'ratings.csv': ('ratings', ['userId','movieId','rating','timestamp']),
    'tags.csv': ('tags', ['userId','movieId','tag','timestamp']),
    'links.csv': ('links', ['movieId','imdbId','tmdbId'])
}


def create_tables(conn: sqlite3.Connection, force: bool = False):
    cur = conn.cursor()
    if force:
        for t in SCHEMA.keys():
            cur.execute(f"DROP TABLE IF EXISTS {t}")
    for t, sql in SCHEMA.items():
        cur.execute(sql)
    conn.commit()


def split_title_year(title_str):
    match = re.match(r"^(.*)\s\((\d{4})\)$", title_str.strip())
    if match:
        title, year = match.groups()
        return title.strip(), int(year)
    else:
        return title_str.strip(), None

def import_csv_to_table(conn: sqlite3.Connection, csv_path: str, table: str, cols: list):
    print(f"Importing {csv_path} -> {table}")
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if table == "movies":
            for row in reader:
                movieId = int(row["movieId"])
                title, year = split_title_year(row["title"])
                genres = row["genres"]
                rows.append((movieId, title, year, genres))
            sql = "INSERT INTO movies VALUES (?, ?, ?, ?)"
        elif table == "ratings":
            for row in reader:
                rows.append((int(row["userId"]), int(row["movieId"]), float(row["rating"]), int(row["timestamp"])))
            sql = "INSERT INTO ratings VALUES (?, ?, ?, ?)"
        elif table == "tags":
            for row in reader:
                rows.append((int(row["userId"]), int(row["movieId"]), row["tag"], int(row["timestamp"])))
            sql = "INSERT INTO tags VALUES (?, ?, ?, ?)"
        elif table == "links":
            for row in reader:
                imdbId = int(row["imdbId"]) if row["imdbId"] else None
                tmdbId = int(row["tmdbId"]) if row["tmdbId"] else None
                rows.append((int(row["movieId"]), imdbId, tmdbId))
            sql = "INSERT INTO links VALUES (?, ?, ?)"
        else:
            raise ValueError(f"Unknown table: {table}")
    cur = conn.cursor()
    cur.executemany(sql, rows)
    conn.commit()
    print(f"Inserted {len(rows)} rows into `{table}`.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True, help='Path to sqlite DB file')
    parser.add_argument('--force', action='store_true', help='Drop and recreate tables')
    args = parser.parse_args()

    db_path = args.db
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    need_create = not os.path.exists(db_path) or args.force
    conn = sqlite3.connect(db_path)
    try:
        create_tables(conn, force=args.force)

        # import each CSV
        for csv_name, (table, cols) in CSV_TO_TABLE.items():
            csv_path = os.path.join(CSV_DIR, csv_name)
            if not os.path.exists(csv_path):
                print(f"Warning: {csv_path} not found, skipping {table}")
                continue
            import_csv_to_table(conn, csv_path, table, cols)

        print('\nAll tables created with primary/foreign keys and data inserted successfully!')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
