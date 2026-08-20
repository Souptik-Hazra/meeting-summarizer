# Phase 9 — Integration & UX Polish Prompt

Phases 1 through 8 are complete, tested, and pushed to GitHub.
The core pipeline (Upload → Storage → Whisper → Gemini → Validation → PostgreSQL → Dashboard) is fully operational.

Now implement ONLY Phase 9 according to AGENTS.md.

==================================================
IMPORTANT SCOPE RULES
==================================================

- Do NOT implement Phase 10 (LLMOps Evaluation & Benchmark Audio Dataset) or Phase 11 (Final Deployment & Docs) early.
- Do NOT introduce external UI frameworks (no MUI, Chakra, Ant Design); use existing Tailwind CSS + Lucide Icons.
- Keep the UI clean, dark-themed, and professional (no excessive animations).
- Do NOT commit or push until explicitly approved by the user.
- Keep all Phase 9 changes uncommitted in the working tree.

==================================================
1. OBJECTIVES FOR PHASE 9
==================================================

Improve the end-to-end meeting workflow across four core areas:

### A. Upload & Validation UX (`AudioUpload.jsx` & `Home.jsx`)
1. **Interactive Drag-and-Drop Feedback**:
   - Distinct visual state when dragging a file over the drop zone.
   - File details preview card (filename, formatted size in MB, format badge).
2. **Clear Validation Banners**:
   - Clear warning for invalid extensions (allowed: `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`).
   - Clear warning for oversized files (> 25MB).
   - "Clear / Remove File" button to reset the dropzone without refreshing.

### B. Network & Cold-Start Resilience (`Meeting.jsx` & `api.js`)
1. **Backend Cold-Start & Network Retry**:
   - If the backend on Render is waking up from sleep (cold start) or experiencing a temporary network blip, polling must automatically retry with exponential backoff (1.5s → 3s) up to 5 times without throwing an instant failure screen.
   - Friendly guidance banner if the browser ad-blocker or CORS blocks requests.
2. **Skeleton Shimmer Loading**:
   - When transitioning from `COMPLETED` status to rendering full intelligence, display a smooth skeleton card placeholder instead of an abrupt layout shift.

### C. Enhanced Productivity & Export Actions (`Meeting.jsx` & `Transcript.jsx`)
1. **Export Intelligence as Markdown (`.md`)**:
   - "Export Markdown" button that generates and downloads a clean formatted `meeting-intelligence-[ID].md` file containing Executive Summary, Key Points, Decisions, Action Items, and Transcript.
2. **Shareable Deep Link**:
   - "Copy Share Link" button with instant visual toast/badge feedback that copies the full direct URL (`http://.../#meeting/[ID]`).
3. **Meeting Not Found (404) Handling**:
   - Clean 404 card when an invalid meeting UUID is looked up, with a direct button back to Home.

### D. Refined Empty & Null States (`MeetingSummary.jsx` & `ActionItems.jsx`)
1. **Pristine Empty States**:
   - Clean placeholder graphics and guidance text when a meeting legitimately has no explicit decisions or no assigned action items.
2. **Full Null Safety**:
   - Verify zero layout shift or crash when owner/deadline fields are null.

==================================================
2. TESTING & VERIFICATION REQUIREMENTS
==================================================

1. Run frontend build: `npm run build` (must pass with 0 errors and 0 warnings).
2. Verify all backend regression tests: `.venv\Scripts\pytest -v` (79/79 passing).
3. Test edge cases manually in browser:
   - Drag & drop invalid file → check error message.
   - Upload audio → verify automatic navigation and live polling.
   - Click "Export Markdown" → verify downloaded `.md` formatting.
   - Click "Copy Share Link" → test opening link in a new tab.
   - Enter invalid meeting ID in lookup → verify clean 404 card.

==================================================
3. SCOPE AUDIT & GIT
==================================================

- Do NOT commit.
- Do NOT push.
- Keep Phase 9 uncommitted in the working tree.

Report completion and STOP.
