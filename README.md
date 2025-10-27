# MovieBot

A conversational AI chatbot that helps users discover and learn about movies using the MovieLens dataset. The bot uses LangChain, Langgraph, GROQ, and SQLite to provide intelligent responses to movie-related queries.

# Branches
- GroqApproach - Utilises Groq, a fast and low cost inference API. As part of this project utilised free tier version.
- Approach 1 - Builds ollama image locally and pulls required model. As part of this project utilised "Qwen 2.5 7B" model (because of system limitations used a model trained on lower parameters)

## Features

- Natural language interaction for movie queries
- Powered by Groq's "openai/gpt-oss-120b" model
- Automatic SQL query generation and execution
- User-friendly Streamlit web interface
- Docker containerized architecture
- Conversation history tracking
- LangSmith integration for request tracing

## Architecture

The project consists of three main components:


### 1. DB Manager
- Processes MovieLens CSV data
- Creates and manages SQLite database
- Handles data initialization

### 2. Backend Service
- FastAPI-based REST API
- Implements LangChain tools for:
  - SQL query generation
  - Query execution
  - Query error fixing
- Database schema introspection
- LangSmith integration for tracing

### 3. Web Frontend
- Streamlit-based user interface
- Real-time chat interaction
- Maintains conversation history
- Displays last 5 exchanges

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.10+
- MovieLens dataset (included in ml-latest-small/)
- langsmith api key (If not required comment out langsmith keys in backend-->apps-->main.py)
- GROQ API KEY (https://console.groq.com/) : To make LLM inference calls

### Installation

1. Clone the repository:
```bash
git clone https://github.com/<random-repo-name>.git
cd MovieBot
```

2. Start the services:
(Include necessary API_KEYS for langsmith in docker compose file)
```bash
docker compose up -d
```

This will:
- Initialize the database with MovieLens data
- Launch the backend API
- Start the web interface

### Accessing the Application

- Web Interface: http://localhost:8501
- Backend API: http://localhost:8000

## API Documentation

### Endpoints

#### 1. `/query`
- **Method**: POST
- **Description**: Accepts a natural language query and returns a response combining structured data and LLM-generated insights.
- **Request Body**:
```json
{
    "session_id": "session1",
    "chat_history": {"messages": [{"role": "user", "content": "Hello"}]}
}
```
- **Response**:
```json
{
  "ai_message": "Hello"
}
```

#### 2. `/health`
- **Method**: GET
- **Description**: Returns the health status of the backend service.
- **Response**:
```json
{
  "status": "ok"
}
```

## Approach to Combining Structured Data with LLM Responses

1. **Structured Data Retrieval**:
   - The MovieLens dataset is stored in an SQLite database.
   - SQL queries are dynamically generated using LangChain tools to retrieve relevant data.

2. **LLM Integration**:
  - The GROQ-hosted "openai/gpt-oss-120b" model is used for natural language understanding and tool orchestration.
    - Trained on 120b parameters and has strong tool-calling, Reasoning,  instruction-following and multilingual capabilities, which improves reliability when invoking LangChain tools to generate SQL and other structured outputs.
    - Its relatively predictable outputs reduce post-processing and error-handling overhead, helping the backend more reliably execute and validate generated queries.

3. **Combining Results**:
   - The backend merges the structured data from the database with the LLM-generated response to provide a comprehensive answer.

## Environment Variables

### Backend Service
- `GROQ_API_KEY`: Ollama service URL
- `GROQ_MODEL`: Model name 
- `LANGSMITH_ENDPOINT`: LangSmith API endpoint
- `LANGSMITH_PROJECT`: Project name for tracing
- `LANGSMITH_API_KEY`: API key for LangSmith

### Web Frontend
- `API_URL`: Backend API endpoint

## Project Structure

```
MovieBot/
├── docker-compose.yml        # Docker services configuration
├── ml-latest-small/         # MovieLens dataset
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── main.py         # Main API implementation
│   │   ├── db_tool.py      # Database utilities
│   │   └── tools/          # LangChain tools
├── dbmanager/              # Database initialization service
│   └── db_manager.py       # Data processing and DB setup
└── webapp/                 # Streamlit frontend
    └── app.py             # Web interface implementation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Dataset

This project uses the MovieLens dataset (ml-latest-small.zip) provided by GroupLens Research. For more information, please visit [MovieLens](https://grouplens.org/datasets/movielens/).
