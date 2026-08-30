import React from 'react';
import { Mic, Activity, CheckCircle2, AlertCircle, Wifi, WifiOff, Trash2, Cpu } from 'lucide-react';
import { AssistantState } from '../types';

interface HeaderProps {
  currentState: AssistantState;
  isConnected: boolean;
  showDevMode: boolean;
  onToggleDevMode: () => void;
  onClearConversation: () => void;
}

const STATE_CONFIG: Record<AssistantState, { label: string; color: string; icon: React.ReactNode }> = {
  IDLE: { label: 'Ready', color: 'bg-slate-800 text-slate-300 border-slate-700', icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> },
  LISTENING: { label: 'Listening', color: 'bg-blue-950 text-blue-300 border-blue-800 animate-pulse', icon: <Mic className="w-3.5 h-3.5 text-blue-400" /> },
  THINKING: { label: 'Processing', color: 'bg-amber-950 text-amber-300 border-amber-800', icon: <Activity className="w-3.5 h-3.5 text-amber-400 animate-spin" /> },
  USING_TOOL: { label: 'Executing tool', color: 'bg-purple-950 text-purple-300 border-purple-800', icon: <Activity className="w-3.5 h-3.5 text-purple-400 animate-bounce" /> },
  SPEAKING: { label: 'Speaking', color: 'bg-emerald-950 text-emerald-300 border-emerald-800', icon: <Activity className="w-3.5 h-3.5 text-emerald-400" /> },
  ERROR: { label: 'Connection Error', color: 'bg-rose-950 text-rose-300 border-rose-800', icon: <AlertCircle className="w-3.5 h-3.5 text-rose-400" /> }
};

export const Header: React.FC<HeaderProps> = ({
  currentState,
  isConnected,
  showDevMode,
  onToggleDevMode,
  onClearConversation
}) => {
  const currentConfig = STATE_CONFIG[currentState] || STATE_CONFIG.IDLE;

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md sticky top-0 z-50 py-3.5 px-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand & Tagline */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Mic className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-sans">AURA</h1>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">Productivity Assistant</span>
            </div>
            <p className="text-xs text-slate-400">Speak naturally. Get things done.</p>
          </div>
        </div>

        {/* Action Controls & Indicators */}
        <div className="flex items-center space-x-3">
          
          {/* Active State Badge */}
          <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border ${currentConfig.color}`}>
            {currentConfig.icon}
            <span>{currentConfig.label}</span>
          </div>

          {/* Dev Mode Toggle */}
          <button
            onClick={onToggleDevMode}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              showDevMode 
                ? 'bg-purple-950/80 text-purple-300 border-purple-800' 
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
            title="Toggle Developer Performance Metrics"
          >
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden sm:inline">Metrics</span>
          </button>

          {/* Clear Conversation */}
          <button
            onClick={onClearConversation}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:text-rose-400 hover:border-rose-900 transition-colors"
            title="Clear current transcript & conversation history"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>

          {/* Connection Status */}
          <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${
            isConnected ? 'bg-slate-900 text-slate-300 border-slate-800' : 'bg-rose-950 text-rose-300 border-rose-800'
          }`}>
            {isConnected ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden md:inline">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-rose-400" />
                <span>Offline</span>
              </>
            )}
          </div>
        </div>

      </div>
    </header>
  );
};
