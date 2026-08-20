import React, { useState, useMemo } from 'react';
import { FileText, Copy, Check, Search, X } from 'lucide-react';

export default function Transcript({ transcript = '' }) {
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleCopy = async () => {
    if (!transcript) return;
    try {
      await navigator.clipboard.writeText(transcript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy transcript:', err);
    }
  };

  const wordCount = useMemo(() => {
    if (!transcript) return 0;
    return transcript.trim().split(/\s+/).length;
  }, [transcript]);

  const matchCount = useMemo(() => {
    if (!searchQuery.trim() || !transcript) return 0;
    const regex = new RegExp(searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    const matches = transcript.match(regex);
    return matches ? matches.length : 0;
  }, [transcript, searchQuery]);

  // Highlight search matches
  const renderHighlightedTranscript = () => {
    if (!searchQuery.trim()) {
      return transcript;
    }

    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = transcript.split(regex);

    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-amber-400/30 text-amber-200 px-0.5 rounded border border-amber-400/40">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="space-y-4 animate-fadeIn">
      <section className="p-6 md:p-8 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-5">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Meeting Transcript</h3>
              <p className="text-xs text-slate-400 font-mono">
                {wordCount} words • {transcript.length} characters
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Search Box */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search transcript..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-7 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 w-44 sm:w-52 transition-all font-mono"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              disabled={!transcript}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-all cursor-pointer disabled:opacity-50"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-300">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {searchQuery.trim() && (
          <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
            <span>Search result:</span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 font-bold border border-slate-700">
              {matchCount} {matchCount === 1 ? 'match' : 'matches'} found
            </span>
          </div>
        )}

        {/* Transcript Content Box */}
        <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800/80 max-h-[500px] overflow-y-auto font-normal text-slate-300 text-sm leading-relaxed whitespace-pre-line select-text">
          {transcript ? (
            renderHighlightedTranscript()
          ) : (
            <p className="text-slate-500 text-xs italic">No transcript content available for this meeting.</p>
          )}
        </div>
      </section>
    </div>
  );
}
