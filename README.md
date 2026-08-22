# AI Meeting Intelligence & Summarization Platform

[![CI / Automated Testing & Build](https://github.com/Souptik-Hazra/meeting-summarizer/actions/workflows/ci.yml/badge.svg)](https://github.com/Souptik-Hazra/meeting-summarizer/actions/workflows/ci.yml)

> **Live Application**: [https://meeting-summarizer-app.netlify.app](https://meeting-summarizer-app.netlify.app)

An end-to-end AI application that converts meeting audio into structured, reliable meeting intelligence using **Groq Whisper**, **Google Gemini Flash**, **FastAPI**, and **React**.

---

## 🚀 Live Demo

- **Frontend App**: [https://meeting-summarizer-app.netlify.app](https://meeting-summarizer-app.netlify.app)
- **Backend API**: Hosted on Render
- **Database & Object Storage**: Supabase (PostgreSQL & Storage)

---

## ✨ Features

- **Audio File Upload & Live Microphone Recording**: Upload recordings (`.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.webm`) or record directly from your microphone in the browser.
- **Fast Speech-to-Text (ASR)**: Groq Whisper (`whisper-large-v3`) produces full transcripts with sub-3s latency.
- **Structured Meeting Intelligence**: Google Gemini Flash extracts:
  - **Executive Summary**: Concise meeting overview.
  - **Key Discussion Points**: Core topics and context.
  - **Explicit Decisions**: Confirmed choices without hallucination.
  - **Verified Action Items**: Specific tasks with assignees and deadlines strictly grounded in transcript evidence.
- **Pydantic Validation Gate**: Schema-enforced JSON guarantees 100% deterministic output before database persistence.
- **Interactive Results Dashboard**: Searchable/copyable transcript, action items checklist, Markdown export, and live pipeline latency telemetry.

---

## 🏗️ Architecture

![Architecture Diagram](docs/architecture_diagram.png)

```text
Audio File / Live Mic
        │
        ▼
 FastAPI Backend
        │
   ┌────┴──────────────────────────┐
   ▼                               ▼
Supabase Storage (Audio)     Supabase DB (Record)
   │
   ▼
Stage 1: Groq Whisper (whisper-large-v3) ──► Transcript
                                                   │
                                                   ▼
Stage 2: Gemini Flash + Pydantic Gate ────► Structured Summary
                                                   │
                                                   ▼
                                         Interactive React Dashboard
```

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React, Vite, Tailwind CSS, Lucide Icons |
| **Backend** | Python 3.11, FastAPI, Pydantic v2 |
| **Speech-to-Text** | Groq API (`whisper-large-v3`) |
| **LLM Intelligence**| Google Gemini (`gemini-flash-lite-latest` / `gemini-2.5-flash`) |
| **Database & Storage** | Supabase PostgreSQL & Supabase Storage |
| **Testing** | pytest (79 unit and integration test cases) |
| **Deployments** | Netlify (Frontend) + Render (Backend) |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check |
| `POST` | `/api/meetings/upload` | Upload audio and initialize meeting record |
| `GET` | `/api/meetings/{id}/status` | Get real-time processing status (`PENDING` → `TRANSCRIBING` → `SUMMARIZING` → `COMPLETED`) |
| `GET` | `/api/meetings/{id}` | Get complete meeting transcript, summary, decisions, and action items |

---

## 💻 Local Setup

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# Activate Virtual Environment:
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, and GEMINI_API_KEY in .env

uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000 in frontend/.env

npm run dev
```

### 3. Run Automated Tests
```bash
cd backend
pytest -v
```
*(All 79 test cases passing)*

---

## 📄 License
MIT License
