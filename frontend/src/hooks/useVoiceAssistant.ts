import { useState, useEffect, useRef, useCallback } from 'react';
import { AssistantState, ActivityItem, Note, Reminder, WSMessage, LatencyMetrics } from '../types';
import { VoiceWebSocketClient } from '../services/websocket';
import { useAudioPlayback } from './useAudioPlayback';

export function useVoiceAssistant() {
  const [currentState, setCurrentState] = useState<AssistantState>('IDLE');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [assistantText, setAssistantText] = useState<string>('');
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [metrics, setMetrics] = useState<LatencyMetrics | null>(null);

  const { enqueueAudioBase64, stopAudio, getAudioContext } = useAudioPlayback();

  const wsClientRef = useRef<VoiceWebSocketClient | null>(null);
  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef<boolean>(false);
  const audioAnalyserRef = useRef<AnalyserNode | null>(null);

  // Fetch initial REST data for Notes and Reminders
  const fetchNotesAndReminders = useCallback(async () => {
    try {
      const [notesRes, remsRes] = await Promise.all([
        fetch('/api/notes'),
        fetch('/api/reminders')
      ]);
      if (notesRes.ok) {
        const notesData = await notesRes.json();
        setNotes(notesData);
      }
      if (remsRes.ok) {
        const remsData = await remsRes.json();
        setReminders(remsData);
      }
    } catch (e) {
      console.error("Failed to fetch initial notes/reminders", e);
    }
  }, []);

  const addActivity = useCallback((type: ActivityItem['type'], details: string, toolName?: string) => {
    const newItem: ActivityItem = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type,
      details,
      toolName
    };
    setActivities(prev => [newItem, ...prev.slice(0, 19)]);
  }, []);

  // Handle incoming WebSocket messages
  const handleWSMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'state':
        if (msg.value) {
          setCurrentState(msg.value);
        }
        break;

      case 'transcript_partial':
        if (msg.text) {
          setTranscript(msg.text);
        }
        break;

      case 'transcript_final':
        if (msg.text) {
          setTranscript(msg.text);
          addActivity('transcript', `You said: "${msg.text}"`);
        }
        break;

      case 'assistant_text':
        if (msg.text) {
          setAssistantText(msg.text);
          addActivity('assistant_speech', msg.text);
        }
        break;

      case 'tool_start':
        if (msg.tool) {
          setCurrentState('USING_TOOL');
          addActivity('tool_start', `Tool started: ${msg.tool}`, msg.tool);
        }
        break;

      case 'tool_result':
        if (msg.tool) {
          addActivity('tool_result', `Tool completed: ${msg.tool}`, msg.tool);
          fetchNotesAndReminders();
        }
        break;

      case 'audio':
        if (msg.data) {
          enqueueAudioBase64(msg.data);
        }
        break;

      case 'metrics':
        if (msg.metrics) {
          setMetrics(msg.metrics);
        }
        break;

      case 'conversation_cleared':
        setTranscript('');
        setAssistantText('');
        addActivity('transcript', 'Conversation cleared');
        break;

      case 'error':
        setCurrentState('ERROR');
        addActivity('interruption', msg.message || "An error occurred");
        break;
    }
  }, [addActivity, enqueueAudioBase64, fetchNotesAndReminders]);

  // Setup WebSocket connection
  useEffect(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/voice`;
    const client = new VoiceWebSocketClient(
      wsUrl,
      handleWSMessage,
      (connected) => setIsConnected(connected)
    );
    client.connect();
    wsClientRef.current = client;

    fetchNotesAndReminders();

    return () => {
      client.disconnect();
    };
  }, [handleWSMessage, fetchNotesAndReminders]);

  // Setup Web Speech Recognition API for continuous client-side speech input
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let interimText = '';
        let finalSegment = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalSegment += event.results[i][0].transcript;
          } else {
            interimText += event.results[i][0].transcript;
          }
        }

        if (interimText) {
          setTranscript(interimText);
          // BARGE-IN INTERRUPTION CHECK:
          // If assistant is currently SPEAKING and user starts talking, interrupt immediately!
          if (currentState === 'SPEAKING') {
            triggerInterruption();
          }
        }

        if (finalSegment) {
          setTranscript(finalSegment);
          if (wsClientRef.current) {
            wsClientRef.current.sendText(finalSegment);
          }
        }
      };

      recognition.onerror = (event: any) => {
        console.warn("Speech recognition notice:", event.error);
      };

      recognitionRef.current = recognition;
    }
  }, [currentState]);

  // BARGE-IN INTERRUPTION TRIGGER
  const triggerInterruption = useCallback(() => {
    console.log("Triggering User Interruption / Barge-In");
    stopAudio();
    if (wsClientRef.current) {
      wsClientRef.current.sendInterrupt();
    }
    setCurrentState('LISTENING');
    addActivity('interruption', 'Speech interrupted by user');
  }, [stopAudio, addActivity]);

  // Start Mic Recording & Audio Visualizer with PCM16 16kHz Mono Stream
  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx({ sampleRate: 16000 });
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 128;

      // ScriptProcessor node for converting Float32 mic stream -> PCM16 Signed 16kHz mono
      const processor = ctx.createScriptProcessor(4096, 1, 1);

      processor.onaudioprocess = (e) => {
        if (!isListeningRef.current) return;
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Convert Float32Array to Int16Array (PCM 16-bit Mono)
        const pcm16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcm16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Convert PCM Int16 bytes to Base64 frame
        const bytes = new Uint8Array(pcm16Data.buffer);
        let binaryStr = '';
        for (let i = 0; i < bytes.byteLength; i++) {
          binaryStr += String.fromCharCode(bytes[i]);
        }
        const b64PCM = window.btoa(binaryStr);

        // Send raw PCM16 16kHz chunk to Python backend WS
        if (wsClientRef.current) {
          wsClientRef.current.send({ type: 'audio', data: b64PCM, format: 'pcm16', sample_rate: 16000 });
        }
      };

      source.connect(analyser);
      analyser.connect(processor);
      processor.connect(ctx.destination);
      audioAnalyserRef.current = analyser;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const checkAudioLevel = () => {
        if (!isListeningRef.current) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const average = sum / bufferLength;
        setAudioLevel(Math.min(100, Math.round(average * 1.5)));
        requestAnimationFrame(checkAudioLevel);
      };

      isListeningRef.current = true;
      requestAnimationFrame(checkAudioLevel);

      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {}
      }

      setCurrentState('LISTENING');
    } catch (err) {
      console.error("Microphone access error:", err);
      setCurrentState('ERROR');
    }
  }, [getAudioContext]);

  // Stop Mic Recording
  const stopListening = useCallback(() => {
    isListeningRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    setAudioLevel(0);
    setCurrentState('IDLE');
  }, []);

  const sendManualText = useCallback((text: string) => {
    if (wsClientRef.current && text.trim()) {
      // If assistant is currently speaking, interrupt first
      if (currentState === 'SPEAKING') {
        triggerInterruption();
      }
      setTranscript(text);
      wsClientRef.current.sendText(text.trim());
    }
  }, [currentState, triggerInterruption]);

  const clearConversation = useCallback(() => {
    setTranscript('');
    setAssistantText('');
    if (wsClientRef.current) {
      wsClientRef.current.send({ type: 'clear_conversation' });
    }
  }, []);

  return {
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
    refreshData: fetchNotesAndReminders
  };
}
