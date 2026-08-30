import React, { useState } from 'react';
import { FileText, Plus, Trash2, Search } from 'lucide-react';
import { Note } from '../types';

interface NotesWidgetProps {
  notes: Note[];
  onRefresh: () => void;
}

export const NotesWidget: React.FC<NotesWidgetProps> = ({ notes, onRefresh }) => {
  const [newNoteContent, setNewNoteContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteContent.trim()) return;

    setIsSubmitting(true);
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newNoteContent.trim() })
      });
      if (res.ok) {
        setNewNoteContent('');
        onRefresh();
      }
    } catch (e) {
      console.error("Failed to create note", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteNote = async (id: number) => {
    try {
      const res = await fetch(`/api/notes/${id}`, { method: 'DELETE' });
      if (res.ok) {
        onRefresh();
      }
    } catch (e) {
      console.error("Failed to delete note", e);
    }
  };

  const filteredNotes = notes.filter(n => 
    n.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="glass-panel p-6 h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Notes ({notes.length})</h3>
          </div>
        </div>

        {/* Search input */}
        <div className="relative mb-3">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search saved notes..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-1.5 pl-8 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </div>

        {/* Notes List */}
        <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
          {filteredNotes.map((note) => (
            <div 
              key={note.id} 
              className="group flex items-start justify-between bg-slate-950/60 p-3 rounded-xl border border-slate-800 hover:border-slate-700 transition-all"
            >
              <div className="flex-1 pr-2 min-w-0">
                <p className="text-xs text-slate-200 leading-relaxed font-normal break-words">{note.content}</p>
                <p className="text-[10px] text-slate-500 mt-1">
                  {new Date(note.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <button
                onClick={() => handleDeleteNote(note.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                title="Delete note"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}

          {filteredNotes.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              <p className="text-xs">No notes found.</p>
            </div>
          )}
        </div>
      </div>

      {/* Direct Add Note Form */}
      <form onSubmit={handleCreateNote} className="mt-4 pt-3 border-t border-slate-800/80">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={newNoteContent}
            onChange={(e) => setNewNoteContent(e.target.value)}
            placeholder="Add a new note..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!newNoteContent.trim() || isSubmitting}
            className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
