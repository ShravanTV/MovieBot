"""
execute_sql_query.py
Tool for executing SQL queries using DBTool.
"""
from langchain.tools import tool
from app.db_tool import DBTool

db = DBTool()

@tool
def execute_sql_query(sql_query: str):
    """Execute SQL query and return rows/columns."""
    if not sql_query:
        return {"error": "No SQL query was provided."}
    result = db.execute_select(sql_query)
    return result  # Contains 'error' key if there's an issue
