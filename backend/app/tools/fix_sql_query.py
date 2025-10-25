"""
fix_sql_query.py
Tool for fixing invalid SQL queries using LLM.
"""
from langchain.tools import tool
from app.db_tool import DBTool
import os
from langchain_ollama import ChatOllama

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

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
