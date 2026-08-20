import { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Mic, 
  UploadCloud, 
  FileText, 
  CheckSquare, 
  ShieldCheck, 
  Activity, 
  Search, 
  ArrowRight 
} from 'lucide-react';
import AudioUpload from '../components/AudioUpload';
import AudioRecorder from '../components/AudioRecorder';
import { checkHealth, uploadMeetingAudio } from '../services/api';

export default function Home({ onNavigateToMeeting }) {
  const [inputMode, setInputMode] = useState('upload'); // 'upload' | 'record'
  const [apiHealth, setApiHealth] = useState({ status: 'checking', service: '' });
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [lookupId, setLookupId] = useState('');

  useEffect(() => {
    let isMounted = true;
    checkHealth()
      .then((data) => {
        if (isMounted) setApiHealth({ status: 'online', service: data.service });
      })
      .catch(() => {
        if (isMounted) setApiHealth({ status: 'offline', service: '' });
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleUpload = async (file) => {
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const response = await uploadMeetingAudio(file);
      setUploadSuccess(response);
      // Automatically transition to the meeting dashboard
      if (response && response.meeting_id && onNavigateToMeeting) {
        setTimeout(() => {
          onNavigateToMeeting(response.meeting_id);
        }, 600);
      }
    } catch (err) {
      setUploadError(err.message || 'Failed to upload and store audio file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setUploadSuccess(null);
    setUploadError(null);
  };

  const handleLookupSubmit = (e) => {
    e.preventDefault();
    if (lookupId.trim() && onNavigateToMeeting) {
      onNavigateToMeeting(lookupId.trim());
    }
  };

  return (
    <div className="space-y-12 py-6">
      {/* Hero Section */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-sky-950/60 border border-sky-500/30 text-sky-300 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Groq Whisper & Gemini Flash Pipeline</span>
        </div>

        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          AI Meeting Intelligence & Summarization
        </h1>

        <p className="text-base md:text-lg text-slate-400">
          Transform raw meeting recordings into structured intelligence: comprehensive transcripts,
          concise summaries, key points, explicit decisions, and verified action items.
        </p>

        {/* Backend API Health Badge */}
        <div className="pt-1 flex items-center justify-center space-x-2 text-xs">
          <span className="flex items-center space-x-1.5 text-slate-400">
            <Activity className="w-3.5 h-3.5" />
            <span>Backend API:</span>
          </span>
          {apiHealth.status === 'checking' && (
            <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Connecting...
            </span>
          )}
          {apiHealth.status === 'online' && (
            <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              Online ({apiHealth.service})
            </span>
          )}
          {apiHealth.status === 'offline' && (
            <span className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Offline
            </span>
          )}
        </div>
      </div>

      {/* Input Mode Selector */}
      <div className="flex items-center justify-center gap-2 max-w-xs mx-auto p-1 rounded-xl bg-slate-900/80 border border-slate-800">
        <button
          type="button"
          onClick={() => {
            setInputMode('upload');
            handleReset();
          }}
          disabled={isUploading}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            inputMode === 'upload'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <UploadCloud className="w-3.5 h-3.5" />
          <span>Upload File</span>
        </button>
        <button
          type="button"
          onClick={() => {
            setInputMode('record');
            handleReset();
          }}
          disabled={isUploading}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            inputMode === 'record'
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Mic className="w-3.5 h-3.5" />
          <span>Record Live</span>
        </button>
      </div>

      {/* Main Audio Ingestion Section */}
      <section className="relative">
        {inputMode === 'upload' ? (
          <AudioUpload 
            onUpload={handleUpload} 
            isUploading={isUploading}
            uploadSuccess={uploadSuccess}
            uploadError={uploadError}
            onReset={handleReset}
          />
        ) : (
          <AudioRecorder
            onRecorded={handleUpload}
            isUploading={isUploading}
          />
        )}
      </section>

      {/* Lookup Existing Meeting ID */}
      <section className="max-w-xl mx-auto p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-semibold text-slate-300">View Existing Meeting Intelligence</span>
          <span className="font-mono">Enter Meeting UUID</span>
        </div>
        <form onSubmit={handleLookupSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="e.g. eec61ac1-7784-40b7-8b49-c7b867f3fb8f"
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              className="w-full pl-8 pr-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500/50 font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={!lookupId.trim()}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold border border-slate-700 transition-all cursor-pointer"
          >
            <span>View</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </form>
      </section>

      {/* Pipeline Architecture Cards */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-6 max-w-5xl mx-auto">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <Mic className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Groq Whisper ASR</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            High-speed, accurate speech-to-text transcription powered by whisper-large-v3.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Gemini Flash</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Structured analysis extracting discussion topics, core takeaways, and takeaways.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <CheckSquare className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Decisions & Actions</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Explicit decisions and verified action items with strict owner/deadline support.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Pydantic Validation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Schema-enforced JSON guarantees deterministic, production-safe meeting outputs.
          </p>
        </div>
      </section>
    </div>
  );
}
