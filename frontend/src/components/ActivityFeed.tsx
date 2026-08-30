import React from 'react';
import { Activity, Wrench, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { ActivityItem } from '../types';

interface ActivityFeedProps {
  activities: ActivityItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities }) => {
  return (
    <div className="glass-panel p-6 h-full min-h-[380px] flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase">System Activity</h3>
          </div>
          <span className="text-xs text-slate-400">{activities.length} Events</span>
        </div>

        {/* Activity Timeline List */}
        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
          {activities.map((act) => (
            <div 
              key={act.id} 
              className="flex items-start space-x-3 text-xs bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/50 transition-all hover:border-slate-700/60"
            >
              <div className="mt-0.5 shrink-0">
                {act.type === 'tool_start' ? (
                  <Wrench className="w-3.5 h-3.5 text-purple-400 animate-spin" />
                ) : act.type === 'tool_result' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : act.type === 'interruption' ? (
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                ) : (
                  <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-slate-300 font-medium truncate">{act.details}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">{act.timestamp}</p>
              </div>
            </div>
          ))}

          {activities.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              <p className="text-sm">No activity recorded yet.</p>
              <p className="text-xs mt-1 text-slate-600">Tool execution events will appear here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
