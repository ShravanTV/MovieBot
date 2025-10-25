"""
generate_sql.py
Tool for generating SQL queries from user questions using the provided LLM and DBTool.
"""
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from typing_extensions import TypedDict, Annotated
from app.db_tool import DBTool
import os
from langchain_ollama import ChatOllama

db = DBTool()
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

class QueryOutput(TypedDict):
    query: Annotated[str, ..., "Syntactically valid SQL query."]

@tool
def generate_sql(user_question: str):
    """Generate a single SELECT SQL statement from the user's question."""
    schema = db.introspect_schema()
    prompt = (
        f"You are an assistant that converts natural language questions into a single SQLite SELECT statement.\n"
        f"Only output SQL, no explanation.\n"
        f"Database schema: {schema}\n"
        f"User question: {user_question}\n"
        f"Limit results to 200 rows."
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    sql_query = structured_llm.invoke(prompt)
    return {"sql_query": sql_query["query"].rstrip(";")}
