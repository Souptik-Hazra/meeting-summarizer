import React, { useState, useEffect } from 'react';
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Mic, 
  Sparkles, 
  Database, 
  Check, 
  ArrowLeft,
  Clock
} from 'lucide-react';

const PIPELINE_STEPS = [
  {
    id: 'PENDING',
    label: 'Upload & Validation',
    desc: 'Audio validated and stored in cloud storage',
    icon: Database,
  },
  {
    id: 'TRANSCRIBING',
    label: 'Groq Whisper ASR',
    desc: 'Converting speech to text via whisper-large-v3',
    icon: Mic,
  },
  {
    id: 'SUMMARIZING',
    label: 'Gemini Flash Intelligence',
    desc: 'Extracting structured summary, decisions, and action items',
    icon: Sparkles,
  },
  {
    id: 'COMPLETED',
    label: 'Intelligence Ready',
    desc: 'Pydantic validated and persisted to database',
    icon: CheckCircle2,
  },
];

const STEP_ORDER = ['PENDING', 'TRANSCRIBING', 'SUMMARIZING', 'COMPLETED'];

export default function ProcessingStatus({ 
  status, 
  failureStage, 
  errorMessage, 
  meetingId,
  onReset 
}) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (status === 'COMPLETED' || status === 'FAILED') return;

    const timer = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [status]);

  const currentIndex = STEP_ORDER.indexOf(status) !== -1 ? STEP_ORDER.indexOf(status) : 0;
  const isFailed = status === 'FAILED';

  return (
    <div className="w-full max-w-3xl mx-auto space-y-8 animate-fadeIn">
      {/* Header Status Card */}
      <div className="p-6 md:p-8 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-wider text-sky-400 font-semibold">
                Meeting Processing Pipeline
              </span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              {isFailed ? 'Processing Encountered an Issue' : 'Analyzing Meeting Recording'}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            {!isFailed && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono text-slate-300">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                <span>Elapsed: {elapsedSeconds}s</span>
              </div>
            )}
            <div className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono uppercase tracking-wider border ${
              isFailed 
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' 
                : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20'
            }`}>
              {status}
            </div>
          </div>
        </div>

        {/* Visual Progress Stepper */}
        {!isFailed ? (
          <div className="space-y-4 py-2">
            {PIPELINE_STEPS.map((step, idx) => {
              const StepIcon = step.icon;
              const isPast = idx < currentIndex;
              const isCurrent = idx === currentIndex;

              return (
                <div 
                  key={step.id} 
                  className={`flex items-start gap-4 p-4 rounded-xl transition-all duration-300 border ${
                    isCurrent 
                      ? 'bg-sky-950/30 border-sky-500/30 shadow-lg shadow-sky-950/50' 
                      : isPast 
                      ? 'bg-slate-900/40 border-slate-800/60 opacity-90' 
                      : 'bg-slate-950/20 border-slate-900/40 opacity-40'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border transition-all ${
                    isPast 
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                      : isCurrent 
                      ? 'bg-sky-500/20 border-sky-400 text-sky-300 shadow-md shadow-sky-500/20' 
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-500'
                  }`}>
                    {isPast ? (
                      <Check className="w-5 h-5" />
                    ) : isCurrent ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <StepIcon className="w-5 h-5" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0 space-y-0.5">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className={`text-sm font-semibold ${
                        isCurrent ? 'text-sky-200' : isPast ? 'text-slate-200' : 'text-slate-500'
                      }`}>
                        {step.label}
                      </h4>
                      {isCurrent && (
                        <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                          In Progress
                        </span>
                      )}
                      {isPast && (
                        <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Complete
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Error State Card */
          <div className="p-5 rounded-xl bg-rose-500/10 border border-rose-500/20 space-y-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-rose-300">
                  Processing Failed {failureStage ? `at ${failureStage} stage` : ''}
                </h4>
                <p className="text-xs text-rose-200/80 leading-relaxed">
                  {errorMessage || "An unexpected error occurred while processing the meeting audio."}
                </p>
              </div>
            </div>

            <div className="pt-2 flex gap-3">
              {onReset && (
                <button
                  onClick={onReset}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/30 transition-all cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Try Another Recording
                </button>
              )}
            </div>
          </div>
        )}

        {/* Meeting ID Reference Footer */}
        {meetingId && (
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>Meeting Reference:</span>
            <span className="text-slate-300 bg-slate-800/80 px-2 py-1 rounded border border-slate-700 select-all">
              {meetingId}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
