# Phase 8 — Results Dashboard Prompt

Phases 1 through 7 are complete, verified, and pushed to GitHub.
The backend API exposes:
- `POST /api/meetings/upload` (returns meeting_id and status: PENDING)
- `GET  /api/meetings/{id}/status` (returns live processing status)
- `GET  /api/meetings/{id}` (returns complete meeting intelligence record)

Now implement ONLY Phase 8 according to AGENTS.md.

==================================================
IMPORTANT SCOPE RULES
==================================================

- Do NOT implement Phase 9 (Advanced UX / Polish), Phase 10, or Phase 11 early.
- Do NOT add external UI frameworks (no MUI, Chakra, Ant Design); use existing Tailwind CSS + Lucide Icons.
- React must communicate ONLY with the FastAPI backend via api.js (never call Groq, Gemini, or Supabase directly).
- Do NOT commit or push until explicitly instructed.
- Keep all Phase 8 changes uncommitted in the working tree.

==================================================
1. USER EXPERIENCE & FLOW
==================================================

1. User uploads a recording on Home page (or enters an existing meeting ID).
2. UI transitions smoothly to the Meeting Dashboard view (`/meeting/:id` or view state).
3. Live Processing State:
   - Polling `GET /api/meetings/:id/status` every 1.5–2 seconds.
   - Displays animated visual stepper:
     * PENDING (Queued)
     * TRANSCRIBING (Groq Whisper large-v3)
     * SUMMARIZING (Gemini Flash Intelligence)
     * COMPLETED / FAILED
   - Polling stops immediately once status reaches COMPLETED or FAILED.
4. Once COMPLETED:
   - Fetches full record via `GET /api/meetings/:id`.
   - Displays rich, clean dashboard cards.
   - Shows telemetry bar (transcription_time, summarization_time, processing_time, model_name, prompt_version).
5. If FAILED:
   - Displays clear, safe error card with failure stage and a "Try Another Recording" button.

==================================================
2. FRONTEND COMPONENTS TO BUILD / FINALIZE
==================================================

Inside `frontend/src/`:

1. `components/ProcessingStatus.jsx`
   - Active status indicator with glowing status badges and visual pipeline progress steps.
   - Real-time elapsed timer while waiting.
   - Clean failure card with sanitized error message if processing fails.

2. `components/MeetingSummary.jsx`
   - **Executive Summary Card**: Formatted overview paragraph of the meeting.
   - **Key Discussion Points**: Structured bulleted list of essential discussion topics and context.

3. `components/ActionItems.jsx`
   - **Explicit Decisions Section**: Verified decisions explicitly made during the meeting.
   - **Action Items Table / Grid**:
     * Task description
     * Owner badge (shows name or clean fallback badge like "Unassigned" if null)
     * Deadline badge (shows deadline or "No deadline" if null)

4. `components/Transcript.jsx`
   - Formatted transcript viewer with scrollable content box.
   - "Copy Transcript" button with visual copy confirmation.
   - Search/filter input to quickly highlight or find spoken text in the transcript.

5. `pages/Meeting.jsx`
   - Main results page coordinating `ProcessingStatus`, `MeetingSummary`, `ActionItems`, and `Transcript`.
   - Header with original filename, meeting ID copy button, and "Upload Another Meeting" back navigation.
   - Observability / Telemetry Bar displaying:
     * ASR Duration (Groq Whisper)
     * LLM Duration (Gemini Flash)
     * Total Processing Time
     * Model & Prompt Version

6. `App.jsx` & Navigation
   - Seamless routing or state-based switching between `Home.jsx` and `Meeting.jsx`.
   - When an upload finishes on `Home.jsx`, automatically navigate to `Meeting.jsx` with the returned `meeting_id`.
   - Add a "View Existing Meeting ID" lookup input on `Home.jsx` for easy sharing/review.

==================================================
3. TESTING & VERIFICATION REQUIREMENTS
==================================================

1. Run frontend build: `npm run build` (must pass with 0 errors and 0 warnings).
2. Verify all backend tests still pass: `.venv\Scripts\pytest -v` (79/79 passing).
3. Test end-to-end user experience in browser:
   - Upload audio recording → watch stepper progress → view final dashboard with Summary, Key Points, Decisions, Action Items, and Transcript.
4. Verify empty states:
   - Handles empty key points, decisions, or action items gracefully without breaking the layout.
5. Verify null safety:
   - Action items with `owner: null` or `deadline: null` render fallback badges cleanly.

==================================================
4. SCOPE AUDIT & GIT
==================================================

- Do NOT commit.
- Do NOT push.
- Keep Phase 8 uncommitted in the working tree.

Report completion and STOP.
