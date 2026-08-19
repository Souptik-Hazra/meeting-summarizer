# Meeting Summarizer Backend API

FastAPI backend service for the AI Meeting Intelligence & Summarization Platform.

## Requirements

- Python 3.11+

## Local Setup

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Endpoints

- `GET /health` - Health check status
- `GET /docs` - Swagger interactive API documentation
