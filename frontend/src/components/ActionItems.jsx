import React from 'react';
import { 
  CheckSquare, 
  User, 
  Calendar, 
  Award, 
  CheckCircle2, 
  Clock, 
  HelpCircle 
} from 'lucide-react';

export default function ActionItems({ decisions = [], actionItems = [] }) {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Explicit Decisions Section */}
      <section className="p-6 md:p-8 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Explicit Decisions</h3>
              <p className="text-xs text-slate-400">Agreements finalized during the meeting</p>
            </div>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {decisions.length} {decisions.length === 1 ? 'Decision' : 'Decisions'}
          </span>
        </div>

        {decisions && decisions.length > 0 ? (
          <div className="grid grid-cols-1 gap-3 pt-1">
            {decisions.map((decision, index) => (
              <div 
                key={index}
                className="flex items-start gap-3.5 p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 hover:border-emerald-500/30 transition-colors"
              >
                <div className="w-6 h-6 rounded-md bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-300 shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <span className="text-sm font-medium text-emerald-100 leading-relaxed">
                  {decision}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-slate-950/20 border border-dashed border-slate-800 text-center text-slate-500 text-xs italic">
            No explicit decisions were identified in this meeting.
          </div>
        )}
      </section>

      {/* Verified Action Items Section */}
      <section className="p-6 md:p-8 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <CheckSquare className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Verified Action Items</h3>
              <p className="text-xs text-slate-400">Tasks with assignees and deadlines grounded in transcript context</p>
            </div>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
            {actionItems.length} {actionItems.length === 1 ? 'Action' : 'Actions'}
          </span>
        </div>

        {actionItems && actionItems.length > 0 ? (
          <div className="grid grid-cols-1 gap-3 pt-1">
            {actionItems.map((item, index) => {
              const hasOwner = item.owner && item.owner.trim().length > 0 && item.owner.toLowerCase() !== 'null';
              const hasDeadline = item.deadline && item.deadline.trim().length > 0 && item.deadline.toLowerCase() !== 'null';

              return (
                <div 
                  key={index}
                  className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60 hover:border-slate-700/80 transition-all space-y-3"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-md bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 text-xs font-mono font-bold shrink-0 mt-0.5">
                      {index + 1}
                    </div>
                    <p className="text-sm font-medium text-slate-200 leading-relaxed flex-1">
                      {item.task}
                    </p>
                  </div>

                  {/* Metadata Badges (Owner & Deadline) */}
                  <div className="flex flex-wrap items-center gap-2 pl-9">
                    {/* Owner Badge */}
                    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${
                      hasOwner 
                        ? 'bg-sky-500/10 text-sky-300 border-sky-500/20' 
                        : 'bg-slate-800/60 text-slate-400 border-slate-700/50'
                    }`}>
                      <User className="w-3 h-3 text-sky-400" />
                      <span>{hasOwner ? item.owner : 'Unassigned'}</span>
                    </div>

                    {/* Deadline Badge */}
                    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${
                      hasDeadline 
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/20' 
                        : 'bg-slate-800/60 text-slate-400 border-slate-700/50'
                    }`}>
                      <Clock className="w-3 h-3 text-amber-400" />
                      <span>{hasDeadline ? item.deadline : 'No deadline'}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-slate-950/20 border border-dashed border-slate-800 text-center text-slate-500 text-xs italic">
            No specific action items were assigned during this meeting.
          </div>
        )}
      </section>
    </div>
  );
}
