import React, { useState } from 'react';
import { useVoiceAssistant } from './hooks/useVoiceAssistant';
import { Header } from './components/Header';
import { VoiceVisualizer } from './components/VoiceVisualizer';
import { LiveTranscript } from './components/LiveTranscript';
import { ActivityFeed } from './components/ActivityFeed';
import { NotesWidget } from './components/NotesWidget';
import { RemindersWidget } from './components/RemindersWidget';
import { QuickPromptBar } from './components/QuickPromptBar';
import { DevMetricsPanel } from './components/DevMetricsPanel';

export const App: React.FC = () => {
  const [showDevMode, setShowDevMode] = useState<boolean>(false);

  const {
    currentState,
    isConnected,
    transcript,
    assistantText,
    activities,
    notes,
    reminders,
    audioLevel,
    metrics,
    startListening,
    stopListening,
    triggerInterruption,
    sendManualText,
    clearConversation,
    refreshData
  } = useVoiceAssistant();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header Bar */}
      <Header
        currentState={currentState}
        isConnected={isConnected}
        showDevMode={showDevMode}
        onToggleDevMode={() => setShowDevMode(!showDevMode)}
        onClearConversation={clearConversation}
      />

      {/* Main Dashboard Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        
        {/* Empirical Performance Metrics (Dev Mode) */}
        {showDevMode && <DevMetricsPanel metrics={metrics} />}

        {/* Quick Voice Commands Toolbar */}
        <QuickPromptBar onSelectPrompt={sendManualText} />

        {/* Top Grid: Voice Visualizer & Live Transcript */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5">
            <VoiceVisualizer
              currentState={currentState}
              audioLevel={audioLevel}
              onStartListening={startListening}
              onStopListening={stopListening}
              onInterrupt={triggerInterruption}
            />
          </div>

          <div className="lg:col-span-7">
            <LiveTranscript
              transcript={transcript}
              assistantText={assistantText}
              onSendText={sendManualText}
            />
          </div>
        </div>

        {/* Bottom Grid: Activity Feed, Notes, & Reminders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ActivityFeed activities={activities} />
          <NotesWidget notes={notes} onRefresh={refreshData} />
          <RemindersWidget reminders={reminders} onRefresh={refreshData} />
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-4 text-center text-xs text-slate-500">
        <p>AURA Voice-First Assistant &bull; Python FastAPI &bull; WebSocket Real-time Audio Engine</p>
      </footer>
    </div>
  );
};

export default App;
