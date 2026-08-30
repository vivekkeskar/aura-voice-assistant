import React from 'react';
import { Clock, CheckCircle2, Trash2 } from 'lucide-react';
import { Reminder } from '../types';

interface RemindersWidgetProps {
  reminders: Reminder[];
  onRefresh: () => void;
}

export const RemindersWidget: React.FC<RemindersWidgetProps> = ({ reminders, onRefresh }) => {
  const handleCompleteReminder = async (id: number) => {
    try {
      const res = await fetch(`/api/reminders/${id}/complete`, { method: 'POST' });
      if (res.ok) {
        onRefresh();
      }
    } catch (e) {
      console.error("Failed to complete reminder", e);
    }
  };

  const handleDeleteReminder = async (id: number) => {
    try {
      const res = await fetch(`/api/reminders/${id}`, { method: 'DELETE' });
      if (res.ok) {
        onRefresh();
      }
    } catch (e) {
      console.error("Failed to delete reminder", e);
    }
  };

  return (
    <div className="glass-panel p-6 h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Reminders ({reminders.length})</h3>
          </div>
        </div>

        {/* Reminders List */}
        <div className="space-y-2.5 max-h-[260px] overflow-y-auto pr-1">
          {reminders.map((rem) => (
            <div 
              key={rem.id} 
              className={`group flex items-center justify-between p-3 rounded-xl border transition-all ${
                rem.status === 'completed'
                  ? 'bg-slate-950/30 border-slate-900 opacity-60'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0 flex-1 pr-2">
                <button
                  onClick={() => handleCompleteReminder(rem.id)}
                  className={`p-1 rounded-lg transition-colors ${
                    rem.status === 'completed' 
                      ? 'text-emerald-400 bg-emerald-950/40 border border-emerald-800/50' 
                      : 'text-slate-600 hover:text-emerald-400 bg-slate-900'
                  }`}
                  title={rem.status === 'completed' ? 'Completed' : 'Mark as complete'}
                >
                  <CheckCircle2 className="w-4 h-4" />
                </button>
                <div className="min-w-0 flex-1">
                  <p className={`text-xs font-medium truncate ${rem.status === 'completed' ? 'line-through text-slate-500' : 'text-slate-200'}`}>
                    {rem.title}
                  </p>
                  <p className="text-[10px] text-amber-400/80 mt-0.5 font-sans">
                    ⏰ {new Date(rem.scheduled_datetime).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>

              <button
                onClick={() => handleDeleteReminder(rem.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                title="Delete reminder"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}

          {reminders.length === 0 && (
            <div className="text-center py-10 text-slate-500">
              <p className="text-xs">No upcoming reminders.</p>
              <p className="text-[11px] mt-1 text-slate-600">Try saying: "Remind me to study tomorrow at 8 PM"</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
