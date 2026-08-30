import React from 'react';
import { Cpu, Zap, Clock, Wrench } from 'lucide-react';
import { LatencyMetrics } from '../types';

interface DevMetricsPanelProps {
  metrics: LatencyMetrics | null;
}

export const DevMetricsPanel: React.FC<DevMetricsPanelProps> = ({ metrics }) => {
  if (!metrics) return null;

  return (
    <div className="glass-panel p-4 mb-6 bg-slate-900/90 border-purple-900/40">
      <div className="flex items-center justify-between pb-2 mb-3 border-b border-purple-900/30">
        <div className="flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-semibold text-purple-200 uppercase tracking-wider">Observed Runtime Latency Metrics</h3>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">Empirical Measurement</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-center space-x-1 text-slate-400 text-[11px] mb-1">
            <Zap className="w-3 h-3 text-amber-400" />
            <span>LLM Time-to-First-Token</span>
          </div>
          <p className="text-sm font-bold text-slate-100 font-mono">
            {metrics.llm_ttft !== undefined ? `${metrics.llm_ttft}s` : 'N/A'}
          </p>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-center space-x-1 text-slate-400 text-[11px] mb-1">
            <Wrench className="w-3 h-3 text-purple-400" />
            <span>Tool Execution Time</span>
          </div>
          <p className="text-sm font-bold text-slate-100 font-mono">
            {metrics.tool_execution_time !== undefined ? `${metrics.tool_execution_time}s` : '0s'}
          </p>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-center space-x-1 text-slate-400 text-[11px] mb-1">
            <Clock className="w-3 h-3 text-emerald-400" />
            <span>TTS First Audio Byte</span>
          </div>
          <p className="text-sm font-bold text-slate-100 font-mono">
            {metrics.tts_first_audio !== undefined ? `${metrics.tts_first_audio}s` : 'N/A'}
          </p>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-center space-x-1 text-slate-400 text-[11px] mb-1">
            <Clock className="w-3 h-3 text-brand-400" />
            <span>Total Pipeline Latency</span>
          </div>
          <p className="text-sm font-bold text-brand-400 font-mono">
            {metrics.total_latency !== undefined ? `${metrics.total_latency}s` : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  );
};
