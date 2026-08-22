import { useState, useRef, useEffect } from 'react';
import { 
  Mic, 
  Square, 
  Play, 
  Pause, 
  RotateCcw, 
  UploadCloud, 
  Loader2, 
  AlertCircle,
  CheckCircle2,
  Radio
} from 'lucide-react';
import { formatFileSize, formatTime } from '../utils/formatters';

export default function AudioRecorder({ 
  onRecorded, 
  isUploading = false,
  disabled = false 
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [micError, setMicError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Timer while recording
  useEffect(() => {
    if (isRecording && !isPaused) {
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording, isPaused]);

  // Clean up object URL
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const startRecording = async () => {
    setMicError(null);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const mime = recorder.mimeType || 'audio/webm';
        const blob = new Blob(audioChunksRef.current, { type: mime });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);

        stream.getTracks().forEach((track) => track.stop());

        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
        const file = new File([blob], `live-recording-${timestamp}.wav`, { type: mime });
        setAudioFile(file);
      };

      recorder.start(250);
      setIsRecording(true);
      setIsPaused(false);
      setRecordingSeconds(0);
    } catch (err) {
      console.error('Microphone error:', err);
      setMicError(
        err.name === 'NotAllowedError'
          ? 'Microphone permission was denied. Please allow microphone access in your browser settings.'
          : 'Could not connect to microphone audio device.'
      );
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }
  };

  const handleReset = () => {
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioFile(null);
    setIsRecording(false);
    setIsPaused(false);
    setRecordingSeconds(0);
    setMicError(null);
  };

  const handleUploadRecorded = () => {
    if (audioFile && onRecorded && !isUploading) {
      onRecorded(audioFile);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 md:p-8 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl text-center space-y-6">
      {!isRecording && !audioBlob ? (
        /* 1. Idle State */
        <div className="space-y-4">
          <button
            type="button"
            onClick={startRecording}
            disabled={disabled || isUploading}
            className="w-16 h-16 rounded-full bg-gradient-to-tr from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 border-4 border-rose-500/30 flex items-center justify-center text-white mx-auto shadow-lg shadow-rose-600/30 hover:scale-105 transition-all cursor-pointer disabled:opacity-50"
            title="Start Recording"
          >
            <Mic className="w-7 h-7" />
          </button>

          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-100">Live Microphone Recording</h3>
            <p className="text-xs text-slate-400">
              Click to capture a live conversation directly through your microphone.
            </p>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-[11px] text-slate-400 font-mono">
            <Radio className="w-3 h-3 text-rose-400" />
            <span>High-fidelity browser audio capture</span>
          </div>
        </div>
      ) : isRecording ? (
        /* 2. Active Recording State */
        <div className="space-y-5 py-2">
          <div className="w-16 h-16 rounded-full bg-rose-500/20 border-2 border-rose-500/40 flex items-center justify-center text-rose-400 mx-auto animate-pulse">
            <Mic className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <div className="text-3xl font-bold font-mono text-white tracking-wider">
              {formatTime(recordingSeconds)}
            </div>
            <p className="text-xs text-rose-400 font-medium flex items-center justify-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span>{isPaused ? 'Recording Paused' : 'Recording in progress...'}</span>
            </p>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-3">
            {isPaused ? (
              <button
                type="button"
                onClick={resumeRecording}
                className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 transition-all cursor-pointer"
                title="Resume Recording"
              >
                <Play className="w-4 h-4 fill-emerald-400" />
              </button>
            ) : (
              <button
                type="button"
                onClick={pauseRecording}
                className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 transition-all cursor-pointer"
                title="Pause Recording"
              >
                <Pause className="w-4 h-4" />
              </button>
            )}

            <button
              type="button"
              onClick={stopRecording}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/30 transition-all cursor-pointer"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              <span>Stop Recording</span>
            </button>
          </div>
        </div>
      ) : (
        /* 3. Finished Recording Preview State */
        <div className="space-y-5">
          <div className="w-14 h-14 rounded-full bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
            <CheckCircle2 className="w-7 h-7" />
          </div>

          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-white">Recording Captured</h3>
            <p className="text-xs text-slate-400 font-mono">
              Duration: {formatTime(recordingSeconds)} • Size: {formatFileSize(audioFile?.size)}
            </p>
          </div>

          {/* Audio Player */}
          {audioUrl && (
            <div className="max-w-md mx-auto p-2 rounded-xl bg-slate-950/80 border border-slate-800">
              <audio controls src={audioUrl} className="w-full h-8" />
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={handleReset}
              disabled={isUploading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-all cursor-pointer disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Discard & Re-record</span>
            </button>

            <button
              type="button"
              onClick={handleUploadRecorded}
              disabled={isUploading || !audioFile}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-sky-500/20 transition-all cursor-pointer disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Audio...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>Upload & Analyze Meeting</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Mic Permission Alert */}
      {micError && (
        <div
          role="alert"
          aria-live="polite"
          className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-start space-x-3 text-rose-300 text-xs text-left"
        >
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <span>{micError}</span>
        </div>
      )}
    </div>
  );
}
