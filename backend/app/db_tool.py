import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = '/data/moviedb.sqlite'

class DBTool:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def introspect_schema(self) -> Dict[str, List[str]]:
        """
        Get database schema, so that LLM understands and use it to generate SQL queries. 
        Return a mapping of table -> list of column names.
        
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

    def execute_select(self, sql: str, max_rows: int = 200) -> Dict[str, Any]:
        """Execute a SELECT SQL statement safely and return rows and columns.

        Safety rules:
        - Only allow SQL that starts with SELECT (case-insensitive)
        """
        sql_strip = sql.strip()
        sql_strip = sql_strip.rstrip(";")
        if not sql_strip.lower().startswith('select'):
            return {'error': 'Only SELECT queries are allowed.'}
#         if ';' in sql_strip:
#             return {'error': 'Semicolons are not allowed in queries.'}

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
            conn.close()
            return {'error': str(e)}
        