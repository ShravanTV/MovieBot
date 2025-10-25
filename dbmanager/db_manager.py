#!/usr/bin/env python3
"""Create SQLite schema and import CSV files from ml-latest-small into the DB.

Tables: movies, ratings, tags, links

Usage: python db_manager.py --db /data/moviedb.sqlite [--force]
"""
import argparse
import os
import sqlite3
import pandas as pd

CSV_DIR = "./ml-latest-small"

SCHEMA = {
    'movies': (
        "movieId INTEGER PRIMARY KEY",
        "title TEXT",
        "genres TEXT"
    ),
    'ratings': (
        "userId INTEGER",
        "movieId INTEGER",
        "rating REAL",
        "timestamp INTEGER"
    ),
    'tags': (
        "userId INTEGER",
        "movieId INTEGER",
        "tag TEXT",
        "timestamp INTEGER"
    ),
    'links': (
        "movieId INTEGER",
        "imdbId INTEGER",
        "tmdbId INTEGER"
    )
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
    for t, cols in SCHEMA.items():
        cols_sql = ', '.join(cols)
        sql = f"CREATE TABLE IF NOT EXISTS {t} ({cols_sql})"
        cur.execute(sql)
    conn.commit()


def import_csv_to_table(conn: sqlite3.Connection, csv_path: str, table: str, cols: list):
    print(f"Importing {csv_path} -> {table}")
    df = pd.read_csv(csv_path)
    # keep only expected cols
    df = df[[c for c in cols if c in df.columns]]
    # write via executemany for predictable types
    placeholders = ','.join(['?'] * len(df.columns))
    sql = f"INSERT INTO {table} ({', '.join(df.columns)}) VALUES ({placeholders})"
    cur = conn.cursor()
    cur.executemany(sql, df.fillna('').values.tolist())
    conn.commit()


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

        print('Import complete')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
