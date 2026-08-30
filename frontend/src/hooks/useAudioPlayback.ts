import { useRef, useCallback } from 'react';

export function useAudioPlayback() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const nextStartTimeRef = useRef<number>(0);
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([]);

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioCtx();
    }
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    return audioContextRef.current;
  }, []);

  const playNextChunk = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    const chunk = audioQueueRef.current.shift()!;
    const ctx = getAudioContext();

    try {
      const audioBuffer = await ctx.decodeAudioData(chunk);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      activeSourcesRef.current.push(source);

      const currentTime = ctx.currentTime;
      // Schedule gapless playback: start immediately if currentTime > nextStartTime, else at nextStartTime
      const startTime = Math.max(currentTime, nextStartTimeRef.current);
      nextStartTimeRef.current = startTime + audioBuffer.duration;

      source.onended = () => {
        activeSourcesRef.current = activeSourcesRef.current.filter(s => s !== source);
        if (audioQueueRef.current.length > 0) {
          playNextChunk();
        } else if (activeSourcesRef.current.length === 0) {
          isPlayingRef.current = false;
        }
      };

      source.start(startTime);
    } catch (e) {
      console.error("Audio decoding error:", e);
      playNextChunk();
    }
  }, [getAudioContext]);

  const enqueueAudioBase64 = useCallback((base64Data: string) => {
    try {
      const binaryString = window.atob(base64Data);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      audioQueueRef.current.push(bytes.buffer);

      if (!isPlayingRef.current) {
        playNextChunk();
      }
    } catch (e) {
      console.error("Failed to decode base64 audio frame", e);
    }
  }, [playNextChunk]);

  const stopAudio = useCallback(() => {
    // Instant cancellation of audio playback (Interruption / Barge-In)
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    nextStartTimeRef.current = 0;
    
    activeSourcesRef.current.forEach(source => {
      try {
        source.stop();
        source.disconnect();
      } catch (e) {}
    });
    activeSourcesRef.current = [];
  }, []);

  return {
    enqueueAudioBase64,
    stopAudio,
    getAudioContext
  };
}
