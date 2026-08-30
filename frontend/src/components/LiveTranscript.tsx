import React, { useState } from 'react';
import { Send, User, Bot, Sparkles } from 'lucide-react';

interface LiveTranscriptProps {
  transcript: string;
  assistantText: string;
  onSendText: (text: string) => void;
}

export const LiveTranscript: React.FC<LiveTranscriptProps> = ({
  transcript,
  assistantText,
  onSendText,
}) => {
  const [textInput, setTextInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onSendText(textInput);
      setTextInput('');
    }
  };

  return (
    <div className="glass-panel p-6 flex flex-col justify-between h-full min-h-[380px]">
      <div>
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-brand-500" />
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Live Conversation</h3>
          </div>
          <span className="text-xs text-slate-400">Real-time Stream</span>
        </div>

        {/* Conversation Display */}
        <div className="space-y-4 max-h-[260px] overflow-y-auto pr-2">
          {/* User Transcript */}
          {transcript && (
            <div className="flex items-start space-x-3 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
              <div className="w-7 h-7 rounded-lg bg-blue-950 text-blue-400 flex items-center justify-center shrink-0 border border-blue-800/50">
                <User className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 mb-0.5">You</p>
                <p className="text-sm text-slate-200 leading-relaxed font-normal">{transcript}</p>
              </div>
            </div>
          )}

          {/* Assistant Text Response */}
          {assistantText && (
            <div className="flex items-start space-x-3 bg-brand-950/20 p-3.5 rounded-xl border border-brand-800/30">
              <div className="w-7 h-7 rounded-lg bg-brand-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-brand-500/20">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-brand-400 mb-0.5">AURA</p>
                <p className="text-sm text-slate-100 leading-relaxed font-normal">{assistantText}</p>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!transcript && !assistantText && (
            <div className="text-center py-12 text-slate-500">
              <p className="text-sm">No active transcript yet.</p>
              <p className="text-xs mt-1 text-slate-600">Speak into your mic or type a prompt below.</p>
            </div>
          )}
        </div>
      </div>

      {/* Manual Input Fallback */}
      <form onSubmit={handleSubmit} className="mt-4 pt-3 border-t border-slate-800/80">
        <div className="relative flex items-center">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type a command (e.g. What's the weather in Pune?)..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-4 pr-12 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!textInput.trim()}
            className="absolute right-2 p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:hover:bg-brand-600 text-white transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
