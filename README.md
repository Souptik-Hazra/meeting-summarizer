# AI Meeting Intelligence & Summarization Platform

A production-grade GenAI platform converting recorded meeting audio into structured, reliable meeting intelligence:
- Meeting transcript
- Concise meeting summary
- Key discussion points
- Explicit decisions
- Action items (with assignees and deadlines strictly supported by transcript context)

---

## Architecture Overview

```text
React (Vite + Tailwind CSS)
  ↓
FastAPI Backend
  ↓
File Validation & Storage Pathing
  ↓
Supabase Storage (Audio)
  ↓
Meeting Record (Supabase PostgreSQL)
  ↓
FastAPI Background Task
  ↓
Stage 1: Groq Whisper (whisper-large-v3) → Raw Transcript
  ↓
Transcript Normalization
  ↓
Stage 2: Gemini 2.5 Flash (Versioned Prompt) → Structured Intelligence
  ↓
Pydantic Schema Validation (with retry)
  ↓
Supabase PostgreSQL Persistence
  ↓
FastAPI Results API
  ↓
React Intelligence Dashboard
```

---

## Technology Stack

- **Frontend**: React, Vite, Tailwind CSS, JavaScript (JSX)
- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Database & Storage**: Supabase PostgreSQL, Supabase Storage
- **Speech-to-Text**: Groq API (`whisper-large-v3`)
- **Generative AI**: Google Gemini (`2.5 Flash`)
- **Testing**: pytest
- **Deployment**: Vercel (Frontend), Render (Backend)

---

## Project Structure

```text
meeting-summarizer/
├── frontend/          # React + Vite application
├── backend/           # FastAPI application
├── test-audio/        # Test audio recordings documentation
├── docs/              # Architecture and evaluation documentation
├── .gitignore
└── README.md
```

---

## Getting Started

### Backend
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Backend health check: `http://localhost:8000/health`

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Frontend development server: `http://localhost:5173`
