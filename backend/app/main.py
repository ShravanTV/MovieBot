from .db_tool import DBTool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from langchain_community.vectorstores import FAISS
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain.tools import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title='MovieBot Backend')

SYSTEM_PROMPT = """You are MovieBot, an AI assistant that helps users with movie-related questions by querying a movie database.
Use available tools to answer user queries."""

# class QueryRequest(BaseModel):
#     q: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: Optional[str]
    chat_history: List[ChatMessage]

class ChatResponse(BaseModel):
    ai_message: str


# shared components
db = DBTool()


@tool
def generate_sql(query: str):
    """Generate a single SELECT SQL statement from the user's question using the LLM and fetch records from Database."""
    question = query
    schema = db.introspect_schema()
    prompt = (
        f"You are an assistant that converts natural language questions into a single SQLite SELECT statement.\n"
        f"Only output SQL, no explanation.\n"
        f"Database schema: {schema}\n"
        f"User question: {question}\n"
        f"Limit results to 200 rows."
    )
    # sql = llm.invoke(prompt)
    # return sql.strip()
    return prompt


@tool
def fetch_query_from_db(sql: str):
    """Fetch records from Database using the provided SQL."""
    if not sql:
        return "I couldn't generate a valid SQL query for your question."
    
    # only allow select statements to proceed
    if not sql.lower().strip().startswith('select'):
        return "I can only execute SELECT queries for security reasons."
    
    result = db.execute_select(sql, max_rows=200)
    
    if 'error' in result:
        return f"Sorry, there was an error executing the query: {result['error']}"
    
    data = result
    cols = data.get('columns', [])
    rows = data.get('rows', [])
    
    prompt = (
        f"You are a helpful assistant. Below are the database query results:\n"
        f"Columns: {cols}\n"
        f"Rows (preview): {rows[:10] if rows else []}\n"
        f"Provide a concise, conversational answer based on these results."
    )
    
    # response = llm.invoke(prompt)
    # return response
    return prompt
    # return {'sql': sql}


# def _cond_after_generate_sql(ctx: dict) -> Optional[str]:
#     sql = (ctx.get('sql') or '').strip()
#     if not sql:
#         return None
#     # only allow select statements to proceed
#     if sql.lower().startswith('select'):
#         return 'execute_sql'
#     return None


# def _node_execute_sql(ctx: dict):
#     sql = ctx.get('sql', '')
#     result = db.execute_select(sql, max_rows=200)
#     # store result under data
#     return {'data': result}


# def _cond_after_execute(ctx: dict) -> Optional[str]:
#     data = ctx.get('data', {})
#     if isinstance(data, dict) and 'error' in data:
#         return None
#     return 'generate_reply'


# def _node_generate_reply(ctx: dict):
#     question = ctx.get('question', '')
#     data = ctx.get('data', {})
#     cols = data.get('columns') if isinstance(data, dict) else None
#     rows = data.get('rows') if isinstance(data, dict) else None
#     prompt = (
#         f"You are a helpful assistant. The user asked: {question}\n"
#         f"The SQL query results are columns={cols} and rows (preview)={rows[:10] if rows else []}.\n"
#         f"Provide a concise, conversational answer that summarizes the results and answers the user's question."
#     )
#     reply = llm.generate(prompt, max_tokens=300)
#     return {'reply': reply}



tools = [generate_sql, fetch_query_from_db]

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
llm = ChatOllama(model="qwen3:0.6b", base_url=OLLAMA_BASE_URL)
llm_with_tools = llm.bind_tools(tools=tools)


def tool_calling_llm(state):
    # Pass system prompt explicitly if present in state
    messages = state["messages"]
    system_prompt = state.get("system_prompt")
    if system_prompt:
        # Ensure system prompt is the first message
        if not (messages and isinstance(messages[0], SystemMessage) and messages[0].content == system_prompt):
            messages = [SystemMessage(content=system_prompt)] + messages
    return {"messages": [llm_with_tools.invoke(messages)]}

# builder = StateGraph()
# builder.add_node('generate_sql', _node_generate_sql)
# builder.add_node('execute_sql', _node_execute_sql)
# builder.add_node('generate_reply', _node_generate_reply)
# builder.add_edge(START, 'generate_sql')
# builder.add_conditional_edges('generate_sql', _cond_after_generate_sql)
# builder.add_conditional_edges('execute_sql', _cond_after_execute)
# builder.add_edge('generate_reply', None)

# graph = builder.compile()


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    system_prompt: Optional[str]

builder = StateGraph(State)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges("tool_calling_llm", tools_condition)
builder.add_edge("tools", "tool_calling_llm")
graph = builder.compile()



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


    # Do not insert SystemMessage here, pass as system_prompt in context
    context = {"messages": history, "system_prompt": sys_prompt}
    response = graph.invoke(context)

    # Send response back to frontend
    ai_msgs = [m for m in response["messages"] if hasattr(m, "content")]
    last_ai_msg = ai_msgs[-1].content if ai_msgs else ""
    return ChatResponse(ai_message=last_ai_msg)

