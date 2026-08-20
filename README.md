# AI Meeting Intelligence & Summarization Platform

A production-grade GenAI application that converts recorded meeting audio into structured, reliable meeting intelligence:
- **Comprehensive Meeting Transcript**: Speech-to-text via Groq Whisper (`whisper-large-v3`).
- **Executive Summary**: Concise overview of meeting purpose and key outcomes.
- **Key Discussion Points**: Essential topics, context, and takeaways.
- **Explicit Decisions**: Agreed-upon choices extracted without hallucination.
- **Verified Action Items**: Structured tasks with assignees and deadlines strictly supported by transcript evidence.

---

## Live Cloud Architecture

- **Backend API**: Render (FastAPI)
- **Database & Object Storage**: Supabase PostgreSQL & Supabase Storage

---

## Architecture Overview

![AI Meeting Intelligence Architecture](docs/architecture_diagram.png)

```text
React (Vite + Tailwind CSS)
  ↓
FastAPI Backend (Render)
  ↓
File Validation & Bounded Chunked Streaming
  ↓
Supabase Storage (Audio Bucket)
  ↓
Meeting Persistence Record (Supabase PostgreSQL)
  ↓
Stage 1: Groq Whisper (whisper-large-v3) → Raw Transcript
  ↓
Transcript Normalization (Whitespace & Formatting Cleanup)
  ↓
Stage 2: Google Gemini Flash (Versioned Prompt) → Structured Intelligence
  ↓
Pydantic Schema Validation Gate (Strict Non-Hallucination Constraints)
  ↓
Supabase PostgreSQL Persistence & Telemetry
  ↓
FastAPI Results API
  ↓
React Dashboard UI
```

---

## Technology Stack

- **Frontend**: React, Vite, Tailwind CSS, JavaScript (JSX), Lucide Icons
- **Backend**: Python 3.11+, FastAPI, Pydantic v2
- **Database & Cloud Storage**: Supabase PostgreSQL, Supabase Storage
- **Speech-to-Text (ASR)**: Groq API (`whisper-large-v3`)
- **Generative AI (LLM)**: Google Gemini (`gemini-flash-lite-latest` / `gemini-3.6-flash`)
- **Testing**: pytest (unit, schema, route, and integration tests)
- **Deployment**: Render (Backend), Netlify/Vercel (Frontend), Supabase (DB & Storage)

---

## Core API Contract

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check and operational status |
| `POST` | `/api/meetings/upload` | Upload audio file, validate format/size, store in cloud, and create meeting record |
| `POST` | `/api/meetings/{id}/transcribe` | Download audio, transcribe with Groq Whisper, normalize, and persist transcript |
| `POST` | `/api/meetings/{id}/summarize` | Structured intelligence extraction with Gemini Flash and Pydantic validation gate |

---

## LLMOps & Production Engineering Practices

1. **Prompt Injection Defense**:
   - Transcripts are isolated as untrusted data.
   - System prompt instructs the model to ignore commands inside transcripts and strictly preserve output schemas.
2. **Deterministic Output Guarantee**:
   - Native structured JSON output (`response_schema=MeetingSummaryOutput`).
   - Pydantic schema acts as the definitive validation gate before persisting to the database.
3. **Zero-Hallucination Action Items**:
   - Assignees (`owner`) and deadlines (`deadline`) are set to `null` unless explicitly stated in the transcript.
4. **LLMOps Telemetry**:
   - Records `model_name`, `prompt_version`, `transcription_time`, and `summarization_time` for full pipeline observability.

---

## Project Structure

```text
meeting-summarizer/
├── frontend/                  # React + Vite application
│   ├── src/
│   │   ├── components/        # AudioUpload, status badges, and UI elements
│   │   ├── pages/             # Home and meeting dashboard pages
│   │   ├── services/          # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI backend application
│   ├── app/
│   │   ├── routes/            # Meeting API routers
│   │   ├── services/          # Storage, Transcription, Summarization, Database
│   │   ├── schemas/           # Pydantic validation schemas
│   │   ├── prompts/           # Versioned Gemini prompt templates (v1)
│   │   ├── config.py          # Centralized configuration & environment settings
│   │   └── main.py            # FastAPI entry point & CORS configuration
│   ├── tests/                 # Automated pytest test suites
│   ├── requirements.txt
│   └── README.md
│
├── docs/                      # Architecture, evaluation, and design specifications
├── .gitignore
├── README.md
└── LICENSE
```

---

## Local Development Setup

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, and GEMINI_API_KEY in .env

uvicorn app.main:app --reload --port 8000
```
Backend health check: `http://localhost:8000/health`

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Frontend development server: `http://localhost:5173`

### 3. Running Automated Tests
```bash
cd backend
.venv\Scripts\pytest -v
```
All 64 backend tests execute with 100% pass rate.
