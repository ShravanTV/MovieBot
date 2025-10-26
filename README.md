# MovieBot

A conversational AI chatbot that helps users discover and learn about movies using the MovieLens dataset. The bot uses LangChain, Langgraph, Ollama, and SQLite to provide intelligent responses to movie-related queries.

## Features

- Natural language interaction for movie queries
- Powered by Ollama's Qwen 2.5 7B model
- Automatic SQL query generation and execution
- User-friendly Streamlit web interface
- Docker containerized architecture
- Conversation history tracking
- LangSmith integration for request tracing

## Architecture

The project consists of four main components:

### 1. Ollama Service
- Runs the Qwen 2.5 7B model
- Handles natural language processing
- Exposed on port 11434

### 2. DB Manager
- Processes MovieLens CSV data
- Creates and manages SQLite database
- Handles data initialization
- Pulls required Ollama model

### 3. Backend Service
- FastAPI-based REST API
- Implements LangChain tools for:
  - SQL query generation
  - Query execution
  - Query error fixing
- Database schema introspection
- LangSmith integration for tracing

### 4. Web Frontend
- Streamlit-based user interface
- Real-time chat interaction
- Maintains conversation history
- Displays last 5 exchanges

## Getting Started

### Prerequisites
- Docker and Docker Compose
- MovieLens dataset (included in ml-latest-small/)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ShravanTV/MovieBot.git
cd MovieBot
```

2. Start the services:
(Include necessary API_KEYS for langsmith)
```bash
docker compose up -d
```

This will:
- Start the Ollama service
- Initialize the database with MovieLens data
- Launch the backend API
- Start the web interface

### Accessing the Application

- Web Interface: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Environment Variables

### Backend Service
- `OLLAMA_URL`: Ollama service URL
- `OLLAMA_MODEL`: Model name (default: qwen2.5:7b)
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
