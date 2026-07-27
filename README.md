# Ephemeral Intent Synthesis System

<div align="center">

**IBM AI Builders Challenge 2026 — Finalist Project**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-3178C6?logo=typescript)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## What Is This?

The **Ephemeral Intent Synthesis System** is an AI-powered student learning assistant that reads your cognitive state through your webcam, then instantly synthesises a personalised lesson — content, pacing, and presentation mode all matched to *how your brain is working right now*.

When the learning goal is met, every compute resource is released. Nothing persists. Nothing idles. That is the **ephemeral** part.

### The Core Idea

> Traditional e-learning: pull a static course and hope it fits.
>
> This system: observe the learner → synthesise *exactly the right content* → terminate everything the moment it is no longer needed.

---

## ✨ Feature Highlights

| Capability | How it works |
|---|---|
| **Biometric Adaptation** | MediaPipe Face Mesh (468 landmarks) measures blink rate, gaze stability, micro-tension and eye aspect ratio. Cognitive load is classified in real-time — high / medium / low. |
| **Streaming RAG Engine** | Ollama (local) or IBM watsonx.ai drives a LangChain + ChromaDB RAG pipeline. Teaching modules stream to the browser as they are generated — first content appears in ~2 s. |
| **Adaptive UI** | The UI Orchestrator selects font size, text density, code visibility and pacing based on the biometric token. A stressed learner gets bullet points; a relaxed learner gets deep explanations. |
| **Local AI Video** | Optional Piper TTS + Wav2Lip pipeline generates talking-head MP4s for every module — 100 % on-device, no API key, no cloud. |
| **Video Library** | All generated videos are accessible from a built-in video browser, independent of the current session. |
| **Ephemeral Compute** | The Lifecycle Manager terminates sessions, releases memory, and scales to zero within 2 seconds of goal detection. |
| **Resource Ingestion** | Feed the RAG engine your own documents (text, Markdown, PDF) or any URL via the Resources panel. |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser                                                         │
│  React 18 + TypeScript + Tailwind CSS                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ BiometricCapture│  │  LearningView   │  │  VideoLibrary  │  │
│  │ (MediaPipe 468) │  │ (StreamedModules│  │  (MP4 browser) │  │
│  │                 │  │  + VideoPlayer) │  │                │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
└───────────┼────────────────────┼───────────────────┼───────────┘
            │     WebSocket /ws  │                   │ REST /api
            ▼                    ▼                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (Python 3.11)                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ BiometricAnalyzer│  │   RAG Engine     │  │ VideoGenerator│  │
│  │ → CognitiveLoad  │  │ LangChain+Chroma │  │ Piper+Wav2Lip │  │
│  │ → BiometricToken │  │ Ollama/watsonx.ai│  │ (optional)    │  │
│  └──────────────────┘  └────────┬─────────┘  └───────────────┘  │
│  ┌──────────────────┐           │                                │
│  │  UIOrchestrator  │◄──────────┘                                │
│  │  LifecycleManager│                                            │
│  └──────────────────┘                                            │
└──────────────┬───────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │   Ollama (local)    │   or   IBM watsonx.ai (cloud)
    │   phi3:mini default │        granite-13b-chat-v2
    └─────────────────────┘
```

---

## 🚀 Quick Start — Local (5 minutes)

### Prerequisites

| Tool | Min version | Notes |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 18 | `node --version` |
| Ollama | latest | https://ollama.ai — pull `phi3:mini` |
| Webcam | any | required for biometric capture |

### 1 — Clone & configure

```bash
git clone https://github.com/pepe-sm/ephemeral-intent-system.git
cd ephemeral-intent-system

# Backend environment
cp backend/.env.example backend/.env
# The defaults work out of the box with Ollama.
# To use IBM watsonx.ai instead, set USE_OLLAMA=false and fill in
# WATSONX_API_KEY + WATSONX_PROJECT_ID in backend/.env
```

### 2 — Start Ollama and pull a model

```bash
ollama serve           # starts the local LLM server
ollama pull phi3:mini  # ~2.3 GB — fastest model, great for demos
```

### 3 — Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python run.py
# → http://localhost:8000  (API docs at /docs)
```

### 4 — Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Demo flow

1. Open **http://localhost:3000**
2. Enter your name and student ID on the registration screen
3. Allow webcam access when prompted
4. Type a topic — *"How does a neural network learn?"*
5. Watch the biometric analysis run (3 seconds), then content streams in
6. Navigate the modules; click **Videos** in the header to see any generated lecture clips

---

## 🐳 Docker — Full Stack

The `docker-compose.yml` starts **every service** in one command:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  frontend    │  │  backend     │  │  ollama      │  │  redis       │
│  :3000       │  │  :8000       │  │  :11434      │  │  :6379       │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

```bash
# 1. Create your .env
cp backend/.env.example backend/.env

# 2. Start everything (backend + ollama + redis)
docker compose up --build

# The first run pulls the phi3:mini model (~2.3 GB) automatically.
# Subsequent starts reuse the cached model.

# 3. Open http://localhost:3000
```

### Production build (nginx-served frontend)

```bash
docker compose --profile prod up --build
```

### Stop / clean up

```bash
docker compose down          # stop containers, keep volumes
docker compose down -v       # stop containers AND delete all data volumes
```

### Volumes

| Volume | Contents |
|---|---|
| `ollama_models` | LLM model weights — reused across restarts |
| `chroma_data` | Vector store embeddings — survives container rebuild |
| `video_data` | Generated MP4 files — persistent video cache |
| `redis_data` | Session state log |

---

## 🎛️ Configuration Reference

All settings live in `backend/.env` (copy from `.env.example`).

### LLM provider

```bash
# Local (default — requires Ollama)
USE_OLLAMA=true
OLLAMA_MODEL=phi3:mini          # or llama3.2, mistral:7b, codellama:7b

# Cloud (requires IBM Cloud account)
USE_OLLAMA=false
WATSONX_API_KEY=<your-key>
WATSONX_PROJECT_ID=<your-project>
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

### Optional AI Video (Piper + Wav2Lip)

See [`LOCAL_VIDEO_GUIDE.md`](LOCAL_VIDEO_GUIDE.md) for the full setup.

```bash
VIDEO_ENABLED=true
PIPER_BINARY=C:/tools/piper/piper.exe
PIPER_MODEL=./models/piper-voices/en_US-lessac-medium.onnx
WAV2LIP_DIR=./Wav2Lip
WAV2LIP_CHECKPOINT=./Wav2Lip/checkpoints/wav2lip.pth
AVATAR_IMAGE=./data/avatar.png
```

---

## 📡 API Reference

Full interactive docs at **http://localhost:8000/docs** when the backend is running.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | System health — RAG status, video generator status |
| `WS` | `/ws/{session_id}` | Real-time pipeline — biometrics → content → UI |
| `GET` | `/api/v1/sessions` | List all active sessions |
| `GET` | `/api/v1/sessions/{id}/videos` | Poll for videos generated in a session |
| `POST` | `/api/v1/resources/ingest` | Add text / file to RAG knowledge base |
| `POST` | `/api/v1/resources/ingest-url` | Fetch a URL and add its text to RAG |
| `GET` | `/api/v1/resources` | List all indexed resources |
| `DELETE` | `/api/v1/resources/{source_id}` | Remove a resource |
| `GET` | `/api/v1/video/` | List all generated MP4 files |
| `GET` | `/api/v1/video/{filename}` | Stream a generated MP4 |

### WebSocket message types

```
Client → Server                Server → Client
──────────────────────         ─────────────────────────────
full_pipeline                  biometric_token
knowledge_query                module_stream  (per module, streaming)
biometric_analysis             knowledge_payload  (full, once done)
ping                           ui_update
                               video_ready  (per module)
                               pipeline_complete
                               error
```

---

## 📂 Project Structure

```
ephemeral-intent-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── pipeline.py       ← full pipeline + video job orchestration
│   │   │   └── websocket.py      ← WS connection manager + message routing
│   │   ├── models/
│   │   │   ├── biometric_token.py
│   │   │   └── knowledge_payload.py
│   │   ├── services/
│   │   │   ├── biometric_analyzer.py   ← 468-landmark cognitive load engine
│   │   │   ├── rag_engine.py           ← LangChain + ChromaDB + Ollama/watsonx
│   │   │   ├── ui_orchestrator.py      ← biometric → UI config mapping
│   │   │   ├── lifecycle_manager.py    ← ephemeral session management
│   │   │   ├── video_generator.py      ← Piper TTS + Wav2Lip pipeline
│   │   │   └── video_cache.py          ← on-disk LRU cache
│   │   └── main.py               ← FastAPI app, all REST endpoints
│   ├── data/videos/              ← generated MP4 files (gitignored)
│   ├── chroma_db/                ← vector store (gitignored)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BiometricCapture.tsx    ← MediaPipe webcam capture
│   │   │   ├── VideoPlayer.tsx         ← MP4 player with scrubber + download
│   │   │   ├── VideoLibrary.tsx        ← browse all cached videos
│   │   │   ├── ResourcesPanel.tsx      ← RAG ingestion UI
│   │   │   ├── RegistrationPanel.tsx
│   │   │   ├── TopicPanel.tsx
│   │   │   └── DynamicUI/
│   │   │       └── DynamicUIRenderer.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts         ← WS lifecycle + all message handlers
│   │   ├── services/
│   │   │   ├── websocket.ts
│   │   │   └── voiceNarration.ts
│   │   ├── store/appStore.ts            ← Zustand global state
│   │   ├── config/index.ts
│   │   ├── types/index.ts
│   │   └── App.tsx                     ← main view router
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml            ← full stack: backend + frontend + ollama + redis
├── LOCAL_VIDEO_GUIDE.md          ← Piper + Wav2Lip local setup
├── AI_VIDEO_INTEGRATION_GUIDE.md ← cloud video API alternatives
├── OLLAMA_INTEGRATION.md
├── DEPLOYMENT_GUIDE.md
└── README.md
```

---

## 🧪 Testing

```bash
# Backend unit tests
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend type-check
cd frontend
npx tsc --noEmit

# Frontend lint
npm run lint
```

---

## 🔧 Technology Stack

### Frontend
| Library | Purpose |
|---|---|
| React 18 + TypeScript | Component framework |
| Vite 5 | Dev server + production bundler |
| Tailwind CSS 3 | Utility-first styling |
| Framer Motion | Smooth content transitions |
| Zustand | Lightweight global state |
| MediaPipe Face Mesh | 468-point facial landmark detection (client-side) |
| lucide-react | Icon set |

### Backend
| Library | Purpose |
|---|---|
| FastAPI 0.109 | Async API framework + WebSocket |
| Uvicorn | ASGI server |
| LangChain 0.3 | RAG orchestration |
| ChromaDB | Local vector store |
| sentence-transformers | `all-MiniLM-L6-v2` embeddings |
| Ollama SDK | Local LLM inference |
| IBM watsonx.ai SDK | Cloud LLM alternative |
| Piper TTS | Local text-to-speech (optional) |
| Wav2Lip | Talking-head video synthesis (optional) |
| Redis | Ephemeral session state |
| Prometheus client | Metrics |

### Infrastructure
| Tool | Purpose |
|---|---|
| Docker + Compose | Single-command full-stack deployment |
| Ollama | Runs phi3:mini, llama3.2, mistral, codellama locally |
| nginx | Production static file serving |

---

## 🔐 Privacy

- **Biometric data never leaves the browser** — MediaPipe runs client-side; only computed scores (a few floats) cross the WebSocket.
- **No video frames stored** — the camera feed is processed frame-by-frame in memory only.
- **Local AI by default** — Ollama means no data leaves your machine.
- **Video generation is 100 % on-device** — Piper + Wav2Lip run locally.
- **Ephemeral sessions** — all in-memory state is released on session end; ChromaDB stores only your explicitly ingested knowledge, not conversation history.

---

## 🌱 Environmental Impact

This system is designed around the **low-power imperative**:

- Compute is active only for the duration of a single learning exchange.
- After goal detection, the LifecycleManager releases all session memory.
- No idle servers polling for work.
- Local models eliminate cloud round-trips and the associated data-centre energy.

Estimated savings vs a persistent cloud learning platform: **>90 % reduction in active compute time** for equivalent knowledge delivery.

---

## 📋 Roadmap

- [x] Biometric cognitive-load engine (468-landmark MediaPipe)
- [x] Streaming RAG engine (Ollama + watsonx.ai)
- [x] Adaptive UI orchestration
- [x] Ephemeral session lifecycle management
- [x] WebSocket real-time pipeline
- [x] Local AI video generation (Piper TTS + Wav2Lip)
- [x] Video library — browse all cached MP4s
- [x] Resource ingestion (text, PDF, URL)
- [x] Full Docker Compose stack
- [ ] Mobile-responsive layout pass
- [ ] Offline mode (service worker + cached embeddings)
- [ ] Multi-language support (Piper has 60+ language voices)
- [ ] Learning path persistence across sessions
- [ ] Custom avatar upload UI
- [ ] Gamification — streaks, badges, progress export

---

## 📝 License

MIT — see [LICENSE](LICENSE).

---

## 👥 Contributors

Built for the **IBM AI Builders Challenge 2026**.

---

*Made with ❤️ — Ephemeral Intent Synthesis System*
