# AURA Architecture & Engineering Specification

AURA is a voice-first personal productivity assistant built with Python (FastAPI, AsyncIO, WebSockets, SQLAlchemy) and React + TypeScript.

---

## 1. High-Level Architecture Diagram

```
                      ┌─────────────────────────┐
                      │     React Frontend      │
                      │ (WebAudio PCM16 + WS)   │
                      └───────────┬─────────────┘
                                  │
                                  │ WebSocket (PCM16 16kHz & JSON)
                                  ▼
                      ┌─────────────────────────┐
                      │  FastAPI WebSocket API  │
                      │  (voice_handler.py)     │
                      └───────────┬─────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │ STT Engine       │  │ LLM Agent Router │  │ BaseTTSService   │
  │ (Deepgram Stream)│  │ (Gemini Flash /  │  │ ├── EdgeTTS      │
  │ / WebSpeech API  │  │  Tool Executor)  │  │ └── ElevenLabs   │
  └──────────────────┘  └─────────┬────────┘  └──────────────────┘
                                  │
                      ┌───────────┴───────────┐
                      ▼                       ▼
            ┌───────────────────┐   ┌───────────────────┐
            │ Real-World Tools  │   │ Persistent Storage│
            │ ├── Weather API   │   │ (SQLite Async     │
            │ ├── Notes Tool    │   │  SQLAlchemy ORM)  │
            │ └── Reminder Tool │   └───────────────────┘
            └───────────────────┘
```

---

## 2. Component Specifications

### 2.1 Frontend Architecture
- **Tech Stack**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React icons.
- **Audio Capture**: WebAudio API `AudioContext` sampled at 16,000 Hz with `ScriptProcessorNode` converting Float32 microphone data to signed PCM 16-bit Mono Integers (`Int16Array`).
- **Audio Playback**: Sequential `AudioContext` queue (`useAudioPlayback`) decoding streaming base64 MP3/PCM chunks.
- **State Synchronization**: Receives real-time state updates (`IDLE`, `LISTENING`, `THINKING`, `USING_TOOL`, `SPEAKING`, `ERROR`) over WebSockets.

### 2.2 Python Backend Architecture
- **Framework**: Python 3.11+, FastAPI, Uvicorn, AsyncIO, WebSockets.
- **Voice Orchestration**: `voice_handler.py` manages session lifecycles, dispatches streaming LLM reasoning, executes tools asynchronously, triggers streaming TTS audio generation, and cancels pending AsyncIO tasks on user interruption.

### 2.3 Audio Format Specification
- **Sampling Rate**: 16,000 Hz (16kHz).
- **Channels**: 1 (Mono).
- **Encoding**: Signed 16-bit Little-Endian PCM (`linear16`).
- **Chunk Size**: 4096 samples (~256ms audio frames).

### 2.4 WebSocket Protocol Reference
- **Client -> Server**:
  - `{"type": "audio", "data": "<base64_pcm16_16k>", "sample_rate": 16000}`
  - `{"type": "interrupt"}`: User barge-in signal.
  - `{"type": "text_input", "text": "<prompt>"}`: Text command fallback.
  - `{"type": "clear_conversation"}`: Clears conversation context and transcript log.
- **Server -> Client**:
  - `{"type": "state", "value": "IDLE" | "LISTENING" | "THINKING" | "USING_TOOL" | "SPEAKING" | "ERROR"}`
  - `{"type": "transcript_final", "text": "..."}`
  - `{"type": "assistant_text", "text": "...", "is_final": true}`
  - `{"type": "tool_start", "tool": "<name>", "params": {...}}`
  - `{"type": "tool_result", "tool": "<name>", "result": {...}}`
  - `{"type": "audio", "data": "<base64_audio_chunk>", "sample_rate": 24000}`
  - `{"type": "metrics", "metrics": {"llm_ttft": 0.013, "tool_execution_time": 0.35, "tts_first_audio": 0.78, "total_latency": 1.14}}`

### 2.5 STT Pipeline
- **Primary**: Deepgram Live Streaming WebSocket API (`deepgram-sdk`) processing `linear16` 16kHz PCM audio stream in real-time.
- **Dev Fallback**: Client-side WebSpeech streaming bridge when `DEEPGRAM_API_KEY` is omitted.

### 2.6 LLM Agent Architecture
- Powered by `google-genai` (Gemini 2.5 Flash / 1.5 Flash) with fallback local tool router engine.
- Supports single-step commands, multi-step requests (e.g. *"What's the weather in Mumbai and create a note saying carry an umbrella"*), structured parameter validation, and multi-turn context retention.

### 2.7 Tool Architecture & Registry
- Base abstract class `BaseTool` in `app/tools/base.py` with `ToolRegistry`.
- **`WeatherTool`**: Geocodes location using Open-Meteo Geocoding API and queries live weather forecast (temperature, condition, wind speed) with HTTP timeouts.
- **`CreateNoteTool` & `ListNotesTool`**: SQLite notes persistence via `NoteRepository`.
- **`CreateReminderTool` & `ListRemindersTool`**: Natural language date parsing using `dateparser` and SQLite scheduling via `ReminderRepository`.

### 2.8 Database Architecture
- SQLite (`aura.db`) with SQLAlchemy 2.0 AsyncIO ORM (`aiosqlite`).
- `PRAGMA journal_mode=WAL` enabled on startup for non-blocking concurrent reads/writes across WebSocket streams and REST endpoints.

### 2.9 TTS Pipeline
- Isolated behind `BaseTTSService` Python abstract interface (`app/services/tts/tts_service.py`).
- **`EdgeTTSService`**: Default zero-configuration neural voice stream generator (`edge-tts`).
- **`ElevenLabsTTSService`**: Pluggable ElevenLabs provider activated via `.env` setting `TTS_PROVIDER=elevenlabs`.

### 2.10 User Interruption / Barge-in Architecture
```
[User Speaks / Taps Interrupt] ──► Client WebAudio Queue Halts (<50ms)
                                  ──► Client sends {"type": "interrupt"}
                                  ──► Python AsyncIO cancels voice_pipeline Task
                                  ──► Session State resets to LISTENING
```

### 2.11 Error Handling Policy
- Graceful exception trapping in tool execution, API timeouts, and WebSocket disconnects without exposing backend tracebacks to frontend users.

### 2.12 Security
- Credentials maintained strictly in `.env` (ignored by `.gitignore`).
- No secrets committed to source control or logged in cleartext.

### 2.13 Latency Measurement Policy
- Latency metrics (LLM time-to-first-token, tool duration, TTS time-to-first-audio-byte, total pipeline duration) are measured empirically at runtime and emitted via WebSocket `metrics` frame.
