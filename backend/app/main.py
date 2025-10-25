from .db_tool import DBTool
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from langchain_ollama import ChatOllama
# from langgraph.graph import StateGraph, START, END
# from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage
from typing_extensions import TypedDict
from typing import Annotated
# from langgraph.graph.message import add_messages
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")


app = FastAPI(title='MovieBot Backend')

# LangSmith environment setup to trace requests
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_PROJECT"] = "MovieChatbot"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")


# Create an instance of DBTool
db = DBTool()


# LLM setup
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)



# ---------------------------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------------------------

class QueryOutput(TypedDict):
    query: Annotated[str, ..., "Syntactically valid SQL query."]
    
@tool
def generate_sql(user_question: str):
    """Generate a single SELECT SQL statement from the user's question"""
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
    
    # Return ONLY the SQL query, don't execute it here
    return {"sql_query": sql_query["query"].rstrip(";")}

@tool
def execute_sql_query(sql_query: str):
    """Execute SQL query and return rows/columns."""
    if not sql_query:
        return {"error": "No SQL query was provided."}

    result = db.execute_select(sql_query)
    return result  # This will contain 'error' key if there's an issue

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



tools = [generate_sql, execute_sql_query, fix_sql_query]


# Enhanced system message
SYSTEM_PROMPT = """
You are MovieBot, an AI assistant that helps users with movie-related questions by querying a movie database.

Your workflow should be:
1. First, use generate_sql to create a SQL query from the user's question
2. Then, use execute_sql_query to run the generated SQL
3. If there's an error in execution, use fix_sql_query to correct the SQL and then execute again
4. Finally, analyze the results and provide a friendly answer to the user

Always limit queries to reasonable results unless specified otherwise.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

Respond in a conversational and friendly tone.
"""


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: Optional[str]
    chat_history: List[ChatMessage]

class ChatResponse(BaseModel):
    ai_message: str


@app.post('/query')
def query(request: ChatRequest):
    logger.info(f"Received chat request: session_id={request.session_id}")

    # Prepare chat history for LangGraph
    history = []
    for m in request.chat_history:
        if m.role == "user":
            history.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            history.append(AIMessage(content=m.content))

    # Add System prompt
    sys_prompt = SYSTEM_PROMPT
    
    agent_executor = create_react_agent(llm, tools, prompt=sys_prompt)

    # Do not insert SystemMessage here, pass as system_prompt in context
    context = {"messages": history}
    
    response = agent_executor.invoke(context)

    # Send response back to frontend
    ai_msgs = [m for m in response["messages"] if hasattr(m, "content")]
    last_ai_msg = ai_msgs[-1].content if ai_msgs else ""
    return ChatResponse(ai_message=last_ai_msg)

