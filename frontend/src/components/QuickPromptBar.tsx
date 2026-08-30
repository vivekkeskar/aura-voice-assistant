import React from 'react';
import { Command } from 'lucide-react';

interface QuickPromptBarProps {
  onSelectPrompt: (prompt: string) => void;
}

const ASSESSMENT_PROMPTS = [
  "What's the weather in Pune?",
  "Create a note saying I need to prepare for my AI interview.",
  "Show my notes.",
  "Remind me to study tomorrow at 8 PM.",
  "What reminders do I have?",
  "What's the weather in Mumbai and create a note saying carry an umbrella.",
  "Cancel my previous request."
];

export const QuickPromptBar: React.FC<QuickPromptBarProps> = ({ onSelectPrompt }) => {
  return (
    <div className="glass-panel p-4 mb-6">
      <div className="flex items-center space-x-2 mb-3">
        <Command className="w-4 h-4 text-brand-400" />
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Example Voice Commands</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {ASSESSMENT_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(prompt)}
            className="text-xs px-3 py-1.5 rounded-xl bg-slate-950/80 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-brand-500/50 transition-all text-left shadow-sm active:scale-95"
          >
            "{prompt}"
          </button>
        ))}
      </div>
    </div>
  );
};
