import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  ArrowLeft, 
  Copy, 
  Check, 
  Clock, 
  Cpu, 
  Sparkles, 
  Share2, 
  SearchX, 
  Zap, 
  AlertCircle 
} from 'lucide-react';
import { getMeetingStatus, getMeetingResult } from '../services/api';
import ProcessingStatus from '../components/ProcessingStatus';
import MeetingSummary from '../components/MeetingSummary';
import ActionItems from '../components/ActionItems';
import Transcript from '../components/Transcript';
import MeetingSkeleton from '../components/MeetingSkeleton';

const NAVIGATION_TABS = [
  { id: 'overview', label: 'Summary & Points', activeStyle: 'bg-sky-500/20 text-sky-300 border-sky-500/30 shadow-sm' },
  { id: 'actions', label: 'Decisions & Actions', activeStyle: 'bg-purple-500/20 text-purple-300 border-purple-500/30 shadow-sm' },
  { id: 'transcript', label: 'Transcript', activeStyle: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30 shadow-sm' },
];

export default function Meeting({ meetingId, onBackToUpload }) {
  const [status, setStatus] = useState('PENDING');
  const [failureStage, setFailureStage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [meetingData, setMeetingData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [copiedId, setCopiedId] = useState(false);
  const [copiedShareLink, setCopiedShareLink] = useState(false);
  const [isFetchingResult, setIsFetchingResult] = useState(false);
  const [isNotFound, setIsNotFound] = useState(false);
  const [networkRetryCount, setNetworkRetryCount] = useState(0);
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

  // Status Polling Loop with network resilience
  useEffect(() => {
    if (!meetingId) return;

    let isMounted = true;
    setIsNotFound(false);

    const pollStatus = async () => {
      try {
        const statusResponse = await getMeetingStatus(meetingId);
        if (!isMounted) return;

        setNetworkRetryCount(0);
        const currentStatus = statusResponse.status;
        setStatus(currentStatus);
        setFailureStage(statusResponse.failure_stage);
        setErrorMessage(statusResponse.error_message);

        if (currentStatus === 'COMPLETED') {
          fetchFinalResult();
        } else if (currentStatus !== 'FAILED') {
          pollTimerRef.current = setTimeout(pollStatus, 1500);
        }
      } catch (err) {
        if (!isMounted) return;
        const errStr = String(err?.message || '');
        if (errStr.includes('404') || errStr.toLowerCase().includes('not found')) {
          setIsNotFound(true);
          return;
        }

        console.warn('Temporary network/server response during polling, retrying...', err);
        setNetworkRetryCount((prev) => prev + 1);
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

  const handleCopyShareLink = async () => {
    try {
      const shareUrl = `${window.location.origin}${window.location.pathname}#meeting/${meetingId}`;
      await navigator.clipboard.writeText(shareUrl);
      setCopiedShareLink(true);
      setTimeout(() => setCopiedShareLink(false), 2500);
    } catch (err) {
      console.error('Failed to copy share link:', err);
    }
  };

  // 404 State Card
  if (isNotFound) {
    return (
      <div className="max-w-2xl mx-auto p-8 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-5 animate-fadeIn">
        <div className="w-16 h-16 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mx-auto">
          <SearchX className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-white">Meeting Record Not Found</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            No meeting record exists with ID <span className="font-mono text-slate-200">{meetingId}</span>. The recording may have expired or the ID was entered incorrectly.
          </p>
        </div>
        <button
          onClick={onBackToUpload}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-lg shadow-sky-600/30 transition-all cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Upload a New Meeting</span>
        </button>
      </div>
    );
  }

  const isCompleted = status === 'COMPLETED' && meetingData !== null;

  const telemetryItems = meetingData ? [
    { label: 'Total Pipeline', value: meetingData.processing_time ? `${meetingData.processing_time}s` : '—', icon: Clock, iconColor: 'text-sky-400' },
    { label: 'Whisper ASR', value: meetingData.transcription_time ? `${meetingData.transcription_time}s` : '—', icon: Zap, iconColor: 'text-indigo-400' },
    { label: 'Gemini LLM', value: meetingData.summarization_time ? `${meetingData.summarization_time}s` : '—', icon: Sparkles, iconColor: 'text-emerald-400' },
    { label: 'Model Engine', value: meetingData.model_name || 'gemini-flash-lite-latest', icon: Cpu, iconColor: 'text-purple-400', isTruncate: true },
  ] : [];

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Top Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 md:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={onBackToUpload}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all cursor-pointer shrink-0"
            title="Back to Upload"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-white truncate max-w-xs md:max-w-md">
                {meetingData?.original_filename || 'Meeting Recording'}
              </h2>
              <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full border shrink-0 ${
                status === 'COMPLETED'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : status === 'FAILED'
                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  : 'bg-sky-500/10 text-sky-400 border-sky-500/20'
              }`}>
                {status}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mt-0.5 truncate">
              <span className="truncate">ID: {meetingId}</span>
              <button
                onClick={handleCopyId}
                className="text-slate-400 hover:text-sky-400 transition-colors shrink-0"
                title="Copy Meeting ID"
              >
                {copiedId ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleCopyShareLink}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all cursor-pointer"
            title="Copy direct shareable link"
          >
            {copiedShareLink ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-300">Link Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5 text-slate-400" />
                <span>Share</span>
              </>
            )}
          </button>

          <button
            onClick={onBackToUpload}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs font-semibold transition-all cursor-pointer"
          >
            Upload New
          </button>
        </div>
      </div>

      {/* Network Warning Badge if reconnecting */}
      {networkRetryCount > 1 && status !== 'COMPLETED' && status !== 'FAILED' && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center gap-2 text-amber-300 text-xs font-mono animate-pulse">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Backend service connecting / warming up (attempt {networkRetryCount})...</span>
        </div>
      )}

      {/* Processing State or Results */}
      {isFetchingResult ? (
        <MeetingSkeleton />
      ) : !isCompleted ? (
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
          <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {telemetryItems.map((item) => {
              const Icon = item.icon;
              return (
                <div 
                  key={item.label} 
                  className={`p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 ${item.colSpan || ''}`}
                >
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                    <Icon className={`w-3.5 h-3.5 ${item.iconColor}`} />
                    <span>{item.label}</span>
                  </div>
                  <p className={`font-bold text-slate-100 font-mono ${item.isTruncate ? 'text-xs font-semibold truncate' : 'text-base'}`}>
                    {item.value}
                  </p>
                </div>
              );
            })}
          </section>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 p-1.5 rounded-xl bg-slate-900/80 border border-slate-800 max-w-md">
            {NAVIGATION_TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeTab === t.id ? t.activeStyle : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t.label}
              </button>
            ))}
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
              <Transcript 
                transcript={meetingData.transcript} 
                originalFilename={meetingData.original_filename}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
