import React from 'react';
import { Sparkles, Layers, Award, FileText } from 'lucide-react';

export default function MeetingSkeleton() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-pulse">
      {/* Telemetry Bar Skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="h-3 w-16 bg-slate-800 rounded" />
            <div className="h-5 w-24 bg-slate-700/60 rounded" />
          </div>
        ))}
      </div>

      {/* Tabs Skeleton */}
      <div className="h-10 w-72 bg-slate-900/80 border border-slate-800 rounded-xl" />

      {/* Main Content Skeleton Cards */}
      <div className="space-y-6">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-800" />
            <div className="h-4 w-40 bg-slate-800 rounded" />
          </div>
          <div className="space-y-2.5 pt-2">
            <div className="h-3.5 w-full bg-slate-800/80 rounded" />
            <div className="h-3.5 w-11/12 bg-slate-800/80 rounded" />
            <div className="h-3.5 w-4/5 bg-slate-800/80 rounded" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-800" />
              <div className="h-4 w-48 bg-slate-800 rounded" />
            </div>
            <div className="h-4 w-12 bg-slate-800 rounded-full" />
          </div>
          <div className="space-y-3 pt-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 w-full bg-slate-950/60 border border-slate-800/60 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
