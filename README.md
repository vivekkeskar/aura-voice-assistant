# AURA — Voice-First Productivity Assistant

AURA is a real-time voice-first productivity assistant built with **Python, FastAPI, WebSockets, React, TypeScript, Gemini, Deepgram, Edge-TTS, SQLite, and Open-Meteo**.

It is designed around a natural voice interaction loop: speak to AURA, let it understand the request, execute a real tool when needed, and receive the response through streaming audio.

## ✨ Features

- 🎙️ Real-time voice interaction over WebSockets
- 🧠 Gemini-powered conversational agent
- 🌦️ Live weather for dynamically requested locations
- 📝 Persistent notes with SQLite
- ⏰ Persistent reminders with natural date/time parsing
- 🔊 Streaming text-to-speech with Edge-TTS
- 🛑 Barge-in / voice interruption support
- 📡 Streaming speech-to-text with Deepgram
- 💾 Conversation persistence
- ⚡ Runtime latency metrics
- 🖥️ Modern SaaS-style React dashboard
- 🧪 Automated backend tests and final QA verification

## 🏗️ Architecture

```text
Browser Microphone
       │
       ▼
  PCM16 / 16kHz
       │
       ▼
 WebSocket /ws/voice
       │
       ▼
 Python FastAPI
       │
       ├── Deepgram STT
       │
       ├── Gemini Agent
       │      │
       │      ├── Weather Tool ──► Open-Meteo
       │      ├── Notes Tool ────► SQLite
       │      └── Reminder Tool ─► SQLite
       │
       └── Edge-TTS
              │
              ▼
        WebSocket Audio
              │
              ▼
       Browser WebAudio
              │
              ▼
            Speaker
```

## 🔄 Voice Pipeline

1. Browser captures microphone audio.
2. Audio is converted to PCM16 mono at 16 kHz.
3. Audio chunks are streamed through WebSocket.
4. Deepgram produces partial and final transcripts.
5. The final transcript is passed to the Gemini agent.
6. Gemini decides whether a tool is required.
7. Tools execute against live services or SQLite.
8. The final response is sent to the TTS layer.
9. TTS audio is streamed back through WebSocket.
10. Browser WebAudio plays the response.
11. User speech during playback can trigger a controlled interruption.

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- WebSockets
- SQLAlchemy
- aiosqlite
- Pydantic
- pytest
- Ruff
- Black

### AI / Speech

- Google Gemini (`google-genai`)
- Deepgram Streaming STT
- Edge-TTS
- Optional browser Web Speech fallback for development

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- WebAudio API

### External Data

- Open-Meteo for live weather and geocoding

## 🌦️ Live Weather

Weather requests use the location extracted from the user's actual request.

Examples:

```text
What's the weather in Pune?
What's the weather in Mumbai?
What's the weather in Solapur?
What's the weather in Delhi?
What's the weather in London?
```

The requested location is passed dynamically to the weather tool and resolved through Open-Meteo.

## 📝 Notes

AURA can create and retrieve persistent notes.

Example:

```text
"Create a note saying I need to prepare for my AI interview."
```

The intended note content is extracted and stored in SQLite without the command prefix.

Example stored content:

```text
I need to prepare for my AI interview.
```

## ⏰ Reminders

AURA supports natural-language reminders.

Example:

```text
"Remind me to study Python tomorrow at 8 PM."
```

Reminders are stored persistently in SQLite and can be listed through voice or the dashboard.

## 🛑 Barge-in

AURA supports interruption while the assistant is speaking.

When genuine user speech is detected during playback:

```text
User Speech
    ↓
Speech Activity Detection
    ↓
Interrupt
    ↓
Stop Browser Playback
    ↓
Cancel Active Backend Task
    ↓
LISTENING
```

The implementation also uses browser audio constraints and guards against repeated false interruption events.

## ⚡ Runtime Metrics

The application records empirical runtime measurements rather than presenting hardcoded performance claims.

Available metrics include:

- LLM time-to-first-token
- Tool execution time
- TTS first-audio timing
- Total request latency

The metrics panel is available from the application header.

## 📁 Project Structure

```text
aura-voice-assistant/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   ├── api/
│   │   ├── config/
│   │   ├── database/
│   │   ├── services/
│   │   │   ├── llm/
│   │   │   ├── stt/
│   │   │   └── tts/
│   │   ├── tools/
│   │   ├── utils/
│   │   └── websocket/
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── docs/
│   └── architecture.md
│
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/vivekkeskar/aura-voice-assistant.git
cd aura-voice-assistant
```

### 2. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Add the required API credentials to `.env`.

**Never commit `.env` or API keys to GitHub.**

### 4. Start the backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

### 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will display the local frontend URL.

Usually:

```text
http://localhost:3000
```

If port 3000 is already occupied, Vite will automatically use another available port.

## 🔐 Environment Variables

Use `.env.example` as the configuration reference.

Keep real credentials only in your local `.env` file.

Integrations include credentials for:

- Gemini
- Deepgram
- Optional ElevenLabs configuration

## 🧪 Testing

### Backend tests

```bash
cd backend
pytest -v
```

### Code quality

```bash
ruff check app tests
black --check app tests
```

### Frontend production build

```bash
cd frontend
npm run build
```

### Verified Results

- **Pytest:** 8/8 passed
- **Ruff:** 0 errors
- **Black:** clean
- **Frontend production build:** passed
- **Functional QA:** 8/8 passed
- **Security checks:** passed

## 📚 Documentation

Detailed architecture documentation is available at:

```text
docs/architecture.md
```

It covers:

- Frontend/backend architecture
- PCM16 16kHz audio specification
- WebSocket protocol
- STT/TTS service isolation
- Database design
- Tool execution
- Barge-in handling
- Runtime latency tracking

## 🎯 Engineering Highlights

AURA focuses on practical real-time engineering rather than a static chatbot demo.

### Real-time communication

Uses WebSockets for bidirectional communication between the browser and Python backend.

### Streaming speech pipeline

Microphone audio is streamed to STT and assistant audio is streamed back to the browser.

### Tool calling

The Gemini agent can dynamically invoke tools for:

- Weather
- Notes
- Reminders

### Persistent storage

Notes, reminders, conversations, and messages are persisted using SQLite.

### Interruption handling

Active assistant generation and browser playback can be cancelled when the user interrupts.

### Runtime observability

The application records empirical latency metrics for the voice pipeline.

### Testing

Backend tools, agent behavior, database interactions, and final functional flows are covered by automated tests.

## ⚠️ Limitations

- Deepgram requires an API key for the primary streaming STT path.
- Browser Web Speech is available as a development fallback when configured.
- Voice quality and latency can vary depending on network conditions, external APIs, browser audio behavior, and the selected TTS voice.
- The application is currently intended for local development and portfolio demonstration.

## 🔒 Security

The repository is configured to keep sensitive and runtime files out of Git:

```text
.env
.venv/
*.db
*.db-wal
*.db-shm
*.db-journal
node_modules/
dist/
__pycache__/
*.pyc
```

Only `.env.example` is committed as the configuration template.

## 📌 Future Improvements

Potential future improvements include:

- Authentication and multi-user accounts
- Cloud database support
- Production deployment
- Additional productivity tools
- More advanced voice activity detection
- Improved observability and tracing
- Mobile client
- Calendar integration

## 📄 License

Add the license you prefer before distributing the project publicly.