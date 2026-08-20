import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  ArrowLeft, 
  Copy, 
  Check, 
  Clock, 
  Cpu, 
  Layers, 
  Sparkles, 
  FileText, 
  CheckSquare, 
  Activity, 
  RefreshCw,
  Award,
  Zap
} from 'lucide-react';
import { getMeetingStatus, getMeetingResult } from '../services/api';
import ProcessingStatus from '../components/ProcessingStatus';
import MeetingSummary from '../components/MeetingSummary';
import ActionItems from '../components/ActionItems';
import Transcript from '../components/Transcript';

export default function Meeting({ meetingId, onBackToUpload }) {
  const [status, setStatus] = useState('PENDING');
  const [failureStage, setFailureStage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [meetingData, setMeetingData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [copiedId, setCopiedId] = useState(false);
  const [isFetchingResult, setIsFetchingResult] = useState(false);
  const pollTimerRef = useRef(null);

  const fetchFinalResult = useCallback(async () => {
    try {
      setIsFetchingResult(true);
      const result = await getMeetingResult(meetingId);
      setMeetingData(result);
    } catch (err) {
      console.error('Failed to fetch meeting results:', err);
      setErrorMessage(err.message || 'Failed to fetch final meeting intelligence.');
    } finally {
      setIsFetchingResult(false);
    }
  }, [meetingId]);

  // Status Polling Loop
  useEffect(() => {
    if (!meetingId) return;

    let isMounted = true;

    const pollStatus = async () => {
      try {
        const statusResponse = await getMeetingStatus(meetingId);
        if (!isMounted) return;

        const currentStatus = statusResponse.status;
        setStatus(currentStatus);
        setFailureStage(statusResponse.failure_stage);
        setErrorMessage(statusResponse.error_message);

        if (currentStatus === 'COMPLETED') {
          fetchFinalResult();
        } else if (currentStatus === 'FAILED') {
          // Terminal failure state reached
        } else {
          // Keep polling every 1.5s
          pollTimerRef.current = setTimeout(pollStatus, 1500);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('Polling error:', err);
        // Retry polling on temporary network glitch
        pollTimerRef.current = setTimeout(pollStatus, 2500);
      }
    };

    pollStatus();

    return () => {
      isMounted = false;
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
      }
    };
  }, [meetingId, fetchFinalResult]);

  const handleCopyId = async () => {
    if (!meetingId) return;
    try {
      await navigator.clipboard.writeText(meetingId);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    } catch (err) {
      console.error('Failed to copy ID:', err);
    }
  };

  const isCompleted = status === 'COMPLETED' && meetingData !== null;

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Top Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 md:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToUpload}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all cursor-pointer"
            title="Back to Upload"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-white truncate max-w-xs md:max-w-md">
                {meetingData?.original_filename || 'Meeting Recording'}
              </h2>
              <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full border ${
                status === 'COMPLETED'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : status === 'FAILED'
                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  : 'bg-sky-500/10 text-sky-400 border-sky-500/20'
              }`}>
                {status}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mt-0.5">
              <span>ID: {meetingId}</span>
              <button
                onClick={handleCopyId}
                className="text-slate-400 hover:text-sky-400 transition-colors"
                title="Copy Meeting ID"
              >
                {copiedId ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onBackToUpload}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs font-semibold transition-all cursor-pointer"
          >
            Upload Another Recording
          </button>
        </div>
      </div>

      {/* Processing State View (if not completed) */}
      {!isCompleted ? (
        <ProcessingStatus
          status={status}
          failureStage={failureStage}
          errorMessage={errorMessage}
          meetingId={meetingId}
          onReset={onBackToUpload}
        />
      ) : (
        /* Completed Results Dashboard */
        <div className="space-y-6">
          {/* Telemetry & Observability Bar */}
          <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                <span>Total Pipeline</span>
              </div>
              <p className="text-base font-bold text-slate-100 font-mono">
                {meetingData?.processing_time ? `${meetingData.processing_time}s` : '—'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <Zap className="w-3.5 h-3.5 text-indigo-400" />
                <span>Whisper ASR</span>
              </div>
              <p className="text-base font-bold text-slate-100 font-mono">
                {meetingData?.transcription_time ? `${meetingData.transcription_time}s` : '—'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>Gemini LLM</span>
              </div>
              <p className="text-base font-bold text-slate-100 font-mono">
                {meetingData?.summarization_time ? `${meetingData.summarization_time}s` : '—'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <Cpu className="w-3.5 h-3.5 text-purple-400" />
                <span>Model Engine</span>
              </div>
              <p className="text-xs font-semibold text-slate-200 font-mono truncate">
                {meetingData?.model_name || 'gemini-flash-lite-latest'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 col-span-2 sm:col-span-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <Activity className="w-3.5 h-3.5 text-amber-400" />
                <span>Prompt Version</span>
              </div>
              <p className="text-base font-bold text-slate-100 font-mono uppercase">
                {meetingData?.prompt_version || 'v1'}
              </p>
            </div>
          </section>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 p-1.5 rounded-xl bg-slate-900/80 border border-slate-800 max-w-md">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'overview'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Summary & Points
            </button>
            <button
              onClick={() => setActiveTab('actions')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'actions'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Decisions & Actions
            </button>
            <button
              onClick={() => setActiveTab('transcript')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'transcript'
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Transcript
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="pt-2">
            {activeTab === 'overview' && (
              <MeetingSummary
                summary={meetingData.summary}
                keyPoints={meetingData.key_points}
              />
            )}

            {activeTab === 'actions' && (
              <ActionItems
                decisions={meetingData.decisions}
                actionItems={meetingData.action_items}
              />
            )}

            {activeTab === 'transcript' && (
              <Transcript transcript={meetingData.transcript} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
