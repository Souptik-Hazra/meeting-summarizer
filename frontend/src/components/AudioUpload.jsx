import { useState, useRef } from 'react';
import { UploadCloud, FileAudio, AlertCircle, CheckCircle2, Trash2, ArrowRight } from 'lucide-react';

const ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg'];
const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB limit

export default function AudioUpload({ onFileSelect, isUploading = false }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    setValidationError(null);

    if (!file) return false;

    // Check extension
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => fileName.endsWith(ext));
    if (!hasValidExtension && !file.type.startsWith('audio/')) {
      setValidationError(
        `Invalid audio format. Allowed extensions: ${ALLOWED_EXTENSIONS.join(', ')}`
      );
      return false;
    }

    // Check size limit
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError(
        `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum limit is 25 MB.`
      );
      return false;
    }

    return true;
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (validateFile(file)) {
        setSelectedFile(file);
        if (onFileSelect) onFileSelect(file);
      } else {
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (validateFile(file)) {
        setSelectedFile(file);
        if (onFileSelect) onFileSelect(file);
      } else {
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setValidationError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (onFileSelect) onFileSelect(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Drag and drop card */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative rounded-2xl border-2 border-dashed transition-all duration-200 p-8 text-center bg-slate-900/50 backdrop-blur-sm focus-within:ring-2 focus-within:ring-sky-500 focus-within:border-sky-500 ${
          dragActive
            ? 'border-sky-500 bg-sky-950/20 shadow-lg shadow-sky-500/10'
            : 'border-slate-700 hover:border-slate-600'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={handleFileChange}
          className="sr-only"
          id="audio-upload-input"
          disabled={isUploading}
          aria-label="Upload meeting audio recording"
        />

        {!selectedFile ? (
          <label
            htmlFor="audio-upload-input"
            className="flex flex-col items-center justify-center cursor-pointer space-y-4"
          >
            <div className="w-16 h-16 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-sky-400 group-hover:scale-105 transition-transform shadow-inner">
              <UploadCloud className="w-8 h-8" />
            </div>

            <div>
              <p className="text-lg font-semibold text-slate-100">
                Click to upload <span className="text-slate-400 font-normal">or drag and drop</span>
              </p>
              <p className="text-sm text-slate-400 mt-1">
                Supported: MP3, WAV, M4A, AAC, FLAC, OGG (Max 25 MB)
              </p>
            </div>

            <div className="inline-flex items-center px-4 py-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-300 text-xs font-medium">
              Stage 0: Pre-Upload File Validation
            </div>
          </label>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <FileAudio className="w-8 h-8" />
            </div>

            <div className="w-full bg-slate-800/80 rounded-xl p-4 border border-slate-700/80 flex items-center justify-between text-left">
              <div className="flex items-center space-x-3 overflow-hidden pr-2">
                <div className="p-2 rounded-lg bg-slate-700/60 text-sky-400 shrink-0">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                </div>
                <div className="truncate min-w-0" title={selectedFile.name}>
                  <p className="text-sm font-medium text-slate-200 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {formatFileSize(selectedFile.size)} • {selectedFile.name.split('.').pop()?.toUpperCase() || 'AUDIO'}
                  </p>
                </div>
              </div>

              {!isUploading && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-700/50 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 shrink-0"
                  title="Remove file"
                  aria-label="Remove selected audio file"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Validation Error Alert */}
      {validationError && (
        <div
          role="alert"
          aria-live="polite"
          className="mt-4 p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-start space-x-3 text-rose-300 text-sm"
        >
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Upload Action Trigger Container */}
      {selectedFile && (
        <div className="mt-6 flex items-center justify-end space-x-4">
          <button
            type="button"
            onClick={handleClear}
            disabled={isUploading}
            className="px-4 py-2.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors text-sm font-medium disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!selectedFile || isUploading}
            className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium text-sm shadow-lg shadow-sky-500/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
          >
            <span>Ready for Processing</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
