import sqlite3
from typing import List, Dict, Any, Optional
import logging
import time

DB_PATH = '/data/moviedb.sqlite'

logger = logging.getLogger("db_tool")

class DBTool:
    """
    A utility class for interacting with the SQLite database.

    Attributes:
        db_path (str): The path to the SQLite database file.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _connect(self, retries: int = 3, delay: int = 2):
        """
        Establish a connection to the database with retries.

        Args:
            retries (int): Number of retry attempts for connection.
            delay (int): Delay (in seconds) between retries.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.

        Raises:
            sqlite3.OperationalError: If the connection fails after retries.
        """
        for attempt in range(retries):
            try:
                return sqlite3.connect(self.db_path)
            except sqlite3.OperationalError as e:
                logger.error(f"Database connection failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise

    def introspect_schema(self) -> Dict[str, List[str]]:
        """
        Get the database schema to help the LLM generate SQL queries.

        Returns:
            Dict[str, List[str]]: A mapping of table names to their column names.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        schema = {}
        for t in tables:
            try:
                cur.execute(f"PRAGMA table_info({t})")
                cols = [row[1] for row in cur.fetchall()]
                schema[t] = cols
            except Exception:
                schema[t] = []
        conn.close()
        return schema

    def execute_select(self, sql: str, max_rows: int = 20) -> Dict[str, Any]:
        """
        Execute a SELECT SQL statement safely and return rows and columns.

        Args:
            sql (str): The SQL query to execute.
            max_rows (int): The maximum number of rows to fetch.

        Returns:
            Dict[str, Any]: A dictionary containing columns and rows, or an error message.
        """
        sql_strip = sql.strip()
        sql_strip = sql_strip.rstrip(";")
        if not sql_strip.lower().startswith('select'):
            return {'error': 'Only SELECT queries are allowed.'}

        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(sql_strip)
            rows = cur.fetchmany(max_rows)
            cols = rows[0].keys() if rows else [c[0] for c in cur.description] if cur.description else []
            results = [dict(r) for r in rows]
            conn.close()
            return {'columns': list(cols), 'rows': results}
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            conn.close()
            return {'error': str(e)}
