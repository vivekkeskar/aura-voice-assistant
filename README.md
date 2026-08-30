# AURA — Voice-First Personal Productivity Assistant

> *"Speak naturally. Get things done."*

AURA is a voice-first personal productivity assistant built with Python (FastAPI, AsyncIO, WebSockets, SQLAlchemy) and React + TypeScript. AURA allows users to interact naturally through speech, check real-time weather, save notes, schedule reminders, and receive spoken responses in real time.

---

## 🌟 Overview

AURA turns natural speech into productive action. Rather than feeling like a generic AI chatbot or futuristic sci-fi widget, AURA is engineered as a practical SaaS productivity application.

---

## 🚀 Features

- 🎤 **Real-Time Voice Interaction**: Streaming microphone capture (PCM 16-bit Mono @ 16kHz) over WebSockets.
- 🤖 **LLM Tool Calling & Routing**: Dynamic execution of real-world tools for weather, notes, and reminders.
- 🔊 **Streaming Text-to-Speech (TTS)**: Neural spoken audio responses using `Edge-TTS` (keyless out-of-the-box streaming) or ElevenLabs.
- ⚡ **User Interruption / Barge-in**: Instantly halts assistant audio playback in `< 50ms` and cancels backend AsyncIO tasks when user speaks.
- 📝 **Persistent SQLite Storage**: Async SQLAlchemy database for notes, reminders, and conversation memory.
- 📊 **Developer Mode & Performance Metrics**: Real-time display of observed empirical runtime latencies.
- 💻 **Modern SaaS UI**: Clean dark glassmorphism dashboard built with React 18, TypeScript, and Tailwind CSS.

---

## 🏗 System Architecture

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

## 🛠 Available Tools

### 1. Weather Tool (`get_weather`)
- **Function**: `get_weather(location)`
- **Integration**: Queries Open-Meteo Geocoding and Forecast REST APIs for current temperature, condition, and wind speed.

### 2. Notes Tool (`create_note`, `list_notes`)
- **Functions**: `create_note(content)`, `list_notes()`
- **Integration**: Persists notes in SQLite database with creation timestamps and REST API endpoints.

### 3. Reminders Tool (`create_reminder`, `list_reminders`)
- **Functions**: `create_reminder(title, datetime_str)`, `list_reminders()`
- **Integration**: Parses natural date/time strings (e.g. *"tomorrow at 8 PM"*, *"in 2 hours"*) using `dateparser` and persists entries in SQLite.

---

## ⚡ User Interruption / Barge-In

When AURA is speaking and the user begins speaking or taps "Interrupt AURA":
1. Frontend WebAudio context halts playback queue instantly (`< 50ms`).
2. Client emits `{"type": "interrupt"}` over WebSocket.
3. FastAPI server cancels the active Python `asyncio.Task` executing text generation/TTS streaming.
4. System state transitions to `LISTENING`, ready for the next command.

---

## 💻 Tech Stack

### Backend (Python-First)
- **Python**: 3.11+
- **Framework**: FastAPI + Uvicorn
- **Protocol**: WebSockets + AsyncIO
- **AI Agent**: `google-genai` (Gemini 2.5 Flash / 1.5 Flash) with fallback local tool engine
- **STT Engine**: Deepgram Live Streaming API (`deepgram-sdk`) + WebSpeech streaming bridge
- **TTS Engine**: `edge-tts` (Microsoft Neural Voices - zero API key required) / ElevenLabs
- **Database**: SQLite + SQLAlchemy 2.0 AsyncIO + `aiosqlite`
- **Testing & Quality**: `pytest`, `pytest-asyncio`, `ruff`, `black`, `mypy`

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Audio Capture**: WebAudio API (PCM16 16kHz Mono)

---

## 📁 Project Structure

```
aura-realtime-voice-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI application entrypoint
│   │   ├── api/                      # REST endpoints for Notes & Reminders
│   │   ├── websocket/
│   │   │   ├── manager.py            # WebSocket connection manager
│   │   │   └── voice_handler.py      # Real-time voice orchestrator & barge-in controller
│   │   ├── agent/
│   │   │   ├── agent.py              # LLM Agent engine & tool function router
│   │   │   ├── prompts.py            # System prompts
│   │   │   └── schemas.py            # Agent Pydantic schemas
│   │   ├── services/
│   │   │   ├── stt/                  # Deepgram STT service
│   │   │   └── tts/                  # Edge-TTS / ElevenLabs service wrapper
│   │   ├── tools/
│   │   │   ├── base.py               # Tool registry interface
│   │   │   ├── weather.py            # Open-Meteo live weather tool
│   │   │   ├── reminders.py          # SQLite Reminders tool
│   │   │   └── notes.py              # SQLite Notes tool
│   │   ├── database/
│   │   │   ├── database.py           # Async engine & sessionmaker
│   │   │   ├── models.py             # SQLAlchemy models
│   │   │   └── repository.py         # Async repositories
│   │   └── config/
│   │       └── settings.py           # Pydantic Settings & env configuration
│   └── tests/                        # Pytest suite & runtime verification
├── frontend/
│   ├── src/
│   │   ├── components/               # Header, VoiceVisualizer, LiveTranscript, ActivityFeed, Notes, Reminders
│   │   ├── hooks/                    # useVoiceAssistant, useAudioPlayback
│   │   ├── services/                 # WebSocket client
│   │   ├── types/                    # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── architecture.md               # Detailed architecture & interruption spec
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔑 Environment Variables

Copy `.env.example` to create your local `.env`:

```ini
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# AI & LLM Settings
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash

# Speech-to-Text
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Text-to-Speech (edge-tts is default keyless; optional ElevenLabs key below)
TTS_PROVIDER=edge
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Database
DATABASE_URL=sqlite+aiosqlite:///./aura.db
```

---

## ⚙️ Installation & Running Locally

### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start frontend dev server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🧪 Testing & Code Quality

Run backend pytest test suite:
```bash
cd backend
source .venv/bin/activate
pytest -v
```

Run code formatting & linting checks:
```bash
cd backend
source .venv/bin/activate
ruff check app tests
black --check app tests
```

Build frontend production bundle:
```bash
cd frontend
npm run build
```

---

## 📊 Performance

During local runtime testing, observed end-to-end latency metrics were recorded as follows:
- **LLM Time-to-First-Token**: `~0.008s - 0.015s`
- **TTS Time-to-First-Audio-Byte**: `~0.78s - 0.86s`
- **Total Pipeline Latency**: `~1.07s - 2.86s` (depending on network conditions and whether external weather geocoding APIs were called).

*Note: Metrics are measured empirically at runtime and displayed in Developer Mode in the frontend UI.*

---

## ⚠️ Known Limitations

- **Microphone Permissions**: Browser requires explicit microphone permission on initial launch.
- **External Network Dependency**: Weather tools query Open-Meteo live APIs and require internet connectivity.

---

## 🔮 Future Improvements

- Multi-language spoken synthesis support.
- Local Whisper STT model fallback for full offline capability.

---

## 📄 License
MIT License.
