from .db_tool import DBTool
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from .tools.generate_sql import generate_sql
from .tools.execute_sql_query import execute_sql_query
from .tools.fix_sql_query import fix_sql_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title='MovieBot Backend')

# LangSmith environment setup to trace requests
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

# Create an instance of DBTool
db = DBTool()

# LLM setup
GROQ_MODEL = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
llm = ChatGroq(model=GROQ_MODEL)

# List of available tools for the agent
tools = [generate_sql, execute_sql_query, fix_sql_query]

# System message
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
    """
    Represents a single chat message in the conversation history.

    Attributes:
        role (str): The role of the message sender (e.g., "user", "assistant").
        content (str): The content of the message.
    """
    role: str
    content: str

class ChatRequest(BaseModel):
    """
    Represents a chat request payload.

    Attributes:
        session_id (Optional[str]): The session ID for the chat.
        chat_history (List[ChatMessage]): The history of messages in the chat.
    """
    session_id: Optional[str]
    chat_history: List[ChatMessage]

class ChatResponse(BaseModel):
    """
    Represents the response from the AI assistant.

    Attributes:
        ai_message (str): The AI-generated response message.
    """
    ai_message: str

@app.post('/query')
def query(request: ChatRequest):
    """
    Handle chat queries from the frontend. This endpoint receives a chat history,
    processes it using the MovieBot agent, and returns the AI's response.

    Args:
        request (ChatRequest): The chat request payload containing session ID and chat history.

    Returns:
        ChatResponse: The AI-generated response to the user's query.
    """
    logger.info(f"Received chat request: session_id={request.session_id}")
    try:
        # Prepare chat history for LangGraph agent
        history = []
        for m in request.chat_history:
            if m.role == "user":
                history.append(HumanMessage(content=m.content))
            elif m.role == "assistant":
                history.append(AIMessage(content=m.content))

        # System prompt for agent
        sys_prompt = SYSTEM_PROMPT

        # Create agent executor
        agent_executor = create_react_agent(llm, tools, prompt=sys_prompt)

        # Build context for agent
        context = {"messages": history}

        # Invoke agent and get response
        response = agent_executor.invoke(context)
        ai_msgs = [m for m in response["messages"] if hasattr(m, "content")]
        last_ai_msg = ai_msgs[-1].content if ai_msgs else ""
        return ChatResponse(ai_message=last_ai_msg)
    except Exception as e:
        logger.exception("Error handling /query request")
        # Return a friendly error message to the frontend
        return ChatResponse(ai_message="Sorry, something went wrong processing your request. Please try again later.")

