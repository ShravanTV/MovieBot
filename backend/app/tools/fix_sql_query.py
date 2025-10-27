"""
fix_sql_query.py
Tool for fixing invalid SQL queries using LLM.
"""
from langchain.tools import tool
from app.db_tool import DBTool
import os
from langchain_groq import ChatGroq

GROQ_MODEL = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
llm = ChatGroq(model=GROQ_MODEL)

@tool
def fix_sql_query(error_message: str, original_sql: str):
    """Fix invalid SQL queries for SQLite."""
    prompt = (
        "You are an SQL expert. Fix the SQL query to be valid SQLite syntax.\n"
        "Only output corrected SQL, nothing else.\n"
        f"Original SQL: {original_sql}\n"
        f"Error: {error_message}"
    )
    fixed = llm.invoke(prompt)
    return {"fixed_sql_query": fixed.content.strip()}
