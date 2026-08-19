-- ==============================================================================
-- AI Meeting Intelligence & Summarization Platform
-- PostgreSQL Database Schema (Supabase)
-- ==============================================================================

-- Create meetings table
CREATE TABLE IF NOT EXISTS public.meetings (
    meeting_id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'TRANSCRIBING', 'SUMMARIZING', 'COMPLETED', 'FAILED')),
    transcript TEXT,
    summary TEXT,
    key_points JSONB,
    decisions JSONB,
    action_items JSONB,
    model_name TEXT,
    prompt_version TEXT,
    transcription_time DOUBLE PRECISION,
    summarization_time DOUBLE PRECISION,
    processing_time DOUBLE PRECISION,
    failure_stage TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for status queries and list ordering
CREATE INDEX IF NOT EXISTS idx_meetings_status ON public.meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON public.meetings(created_at DESC);

-- Trigger function to automatically maintain updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_meetings_updated_at ON public.meetings;
CREATE TRIGGER set_meetings_updated_at
    BEFORE UPDATE ON public.meetings
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
