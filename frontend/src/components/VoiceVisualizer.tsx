import React from 'react';
import { Mic, MicOff, Square, Volume2 } from 'lucide-react';
import { AssistantState } from '../types';

interface VoiceVisualizerProps {
  currentState: AssistantState;
  audioLevel: number;
  onStartListening: () => void;
  onStopListening: () => void;
  onInterrupt: () => void;
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  currentState,
  audioLevel,
  onStartListening,
  onStopListening,
  onInterrupt,
}) => {
  const isListening = currentState === 'LISTENING';
  const isSpeaking = currentState === 'SPEAKING';

  return (
    <div className="glass-panel p-8 text-center flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background visual glow */}
      <div 
        className={`absolute inset-0 transition-opacity duration-500 pointer-events-none ${
          isListening ? 'bg-blue-600/5' : isSpeaking ? 'bg-emerald-600/5' : 'bg-transparent'
        }`}
      />

      {/* Main Microphone Button */}
      <div className="relative mb-6">
        {/* Animated outer audio pulse ring */}
        {(isListening || isSpeaking) && (
          <div 
            className={`absolute -inset-4 rounded-full opacity-75 blur-md transition-all duration-150 ${
              isSpeaking ? 'bg-emerald-500/30 animate-pulse' : 'bg-brand-500/30'
            }`}
            style={{ transform: `scale(${1 + audioLevel / 100})` }}
          />
        )}

        <button
          onClick={isListening ? onStopListening : onStartListening}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 transform active:scale-95 shadow-2xl ${
            isListening 
              ? 'bg-gradient-to-tr from-brand-600 to-blue-500 text-white shadow-brand-500/40 ring-4 ring-brand-500/20 animate-pulse-subtle'
              : isSpeaking
              ? 'bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-emerald-500/40 ring-4 ring-emerald-500/20'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 shadow-slate-900/50'
          }`}
          aria-label={isListening ? "Stop Listening" : "Start Listening"}
        >
          {isListening ? (
            <Mic className="w-10 h-10 animate-bounce" />
          ) : isSpeaking ? (
            <Volume2 className="w-10 h-10" />
          ) : (
            <MicOff className="w-10 h-10 text-slate-400" />
          )}
        </button>
      </div>

      {/* Action controls & prompt guide */}
      <div className="space-y-3 z-10">
        <h2 className="text-lg font-semibold text-white tracking-tight">
          {isListening
            ? 'Listening... Speak naturally'
            : currentState === 'THINKING'
            ? 'Processing your request...'
            : currentState === 'USING_TOOL'
            ? 'Executing productivity tool...'
            : isSpeaking
            ? 'AURA is speaking...'
            : 'Tap microphone to start speaking'}
        </h2>

        {/* Audio Volume Bar */}
        {isListening && (
          <div className="w-48 h-1.5 bg-slate-800 rounded-full overflow-hidden mx-auto">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-400 transition-all duration-75"
              style={{ width: `${Math.max(5, audioLevel)}%` }}
            />
          </div>
        )}

        {/* Interruption / Barge-in Action Button */}
        {isSpeaking && (
          <button
            onClick={onInterrupt}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-950/80 hover:bg-rose-900 text-rose-200 border border-rose-800/80 text-xs font-semibold transition-all transform active:scale-95 shadow-lg"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Interrupt AURA</span>
          </button>
        )}
      </div>
    </div>
  );
};
