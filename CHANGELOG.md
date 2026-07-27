# Changelog

All notable changes to the Ephemeral Intent Synthesis System are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [3.0.0] — 2025-07-01

### 🎉 Major Release — Production-Ready Full Stack

Complete Docker deployment story, video library, and challenge-ready documentation.

### Added

#### Video Library 🎬
- **`GET /api/v1/video/`** — new listing endpoint returns all cached MP4s with
  filename, URL, size, and creation timestamp. No session required.
- **`VideoLibrary` component** — browse every locally-generated video from a
  collapsible list; expands to an inline `VideoPlayer` with scrubber and download.
- **"Videos" button in header** — always visible regardless of login state.
- `'videos'` added to `LabView` union type.

#### Docker & Infrastructure 🐳
- **`backend/Dockerfile`** — multi-stage build (deps → runtime); non-root user,
  health-check, `libgomp1` for sentence-transformers.
- **`backend/.dockerignore`** — excludes venv, chroma_db, data/videos, tests.
- **`frontend/.dockerignore`** — excludes node_modules, dist.
- **`docker-compose.yml`** — complete rewrite:
  - `ollama` service with volume-cached model weights.
  - `ollama-pull` one-shot service that pulls `phi3:mini` automatically.
  - `redis` service with memory-capped LRU eviction policy.
  - `backend` service wired to ollama + redis with correct env overrides.
  - `frontend` dev service (Vite, `--profile dev`).
  - `frontend-prod` nginx service (`--profile prod`).
  - Named volumes: `chroma_data`, `video_data`, `ollama_models`, `redis_data`.

#### Documentation 📖
- **`README.md`** — complete rewrite for IBM AI Builders Challenge 2026:
  - Architecture ASCII diagram with all layers.
  - 5-minute quick-start guide.
  - Docker quick-start section.
  - Full API reference table.
  - Configuration reference.
  - Updated technology stack table.
  - Privacy + environmental impact sections.
  - Updated roadmap (reflects shipped features).

### Changed
- `CHANGELOG.md` updated to reflect all shipped work through v3.0.0.
- `LabView` type extended with `'videos'` variant.

### Fixed
- Backend `backend/Dockerfile` was empty — now a fully working multi-stage build.

---

## [2.1.0] — 2025-06-29

### Added

#### Local AI Video Pipeline 🎥
- **`VideoGenerator` service** — Piper TTS → Wav2Lip → ffmpeg pipeline.
  Produces talking-head MP4s entirely on-device; no cloud API required.
- **`VideoCache` service** — on-disk LRU cache with configurable max items.
- **`VideoPlayer` component** — custom player with timeline scrubber,
  mute toggle, download button, error fallback.
- **Video pipeline in `pipeline.py`** — fires after all modules are streamed;
  sequential per-module generation to avoid CPU overload.
- **In-memory video registry** — `{session_id → {module_id → url}}`; survives
  WebSocket close so the frontend can poll for missed videos.
- **`GET /api/v1/sessions/{id}/videos`** — polling endpoint for the registry.
- **`GET /api/v1/video/{filename}`** — secure MP4 file serving (path-traversal safe).
- `video_ready` WebSocket message type.
- `LOCAL_VIDEO_GUIDE.md` — 500-line setup guide (ffmpeg, Piper, Wav2Lip).

#### Resource Ingestion
- **`POST /api/v1/resources/ingest`** — text, Markdown, and PDF file upload.
- **`POST /api/v1/resources/ingest-url`** — URL fetch + HTML strip.
- **`GET /api/v1/resources`** and **`DELETE /api/v1/resources/{id}`**.
- **`ResourcesPanel`** component with drag-and-drop file UI.

#### Streaming RAG
- `RAGEngine.stream_modules()` — async generator yields modules as LLM produces them.
- Frontend shows first module in ~2 s; remaining arrive progressively.

#### Developer experience
- `pipeline.py` extracted from `websocket.py` — all pipeline logic isolated.
- `load_dotenv(override=True)` fixes stale shell env clobbering `.env`.
- `FFMPEG_BINARY` env var for explicit ffmpeg path (Windows PATH quirk fix).
- 120-second frontend timeout guard on topic submit.

### Fixed
- `videoEnabled` ref vs state race condition — frontend spinner now fires reliably.
- Wav2Lip subprocess uses `sys.executable` so the venv Python is used.
- `length_scale` for Piper TTS passed as string (subprocess safety).

---

## [2.0.0] — 2024-06-22

### Added
- Voice narration via Web Speech API (adaptive rate from biometric token).
- 15 comprehensive educational content modules (programming, web dev, data science).
- `AI_VIDEO_INTEGRATION_GUIDE.md` (D-ID, Synthesia, HeyGen, Runway ML comparison).
- `VERSION_CONTROL_GUIDE.md`.

### Changed
- Enhanced animations — card hover, button press, page transitions.
- Smart module navigation labels ("Continue →" vs "✓ Complete Session").

### Fixed
- Module index overflow — `completeModule` now clamps to `length - 1`.
- Module index reset to 0 on new UI tree arrival.

---

## [1.0.0] — 2024-06-15

### Initial Release
- Biometric capture — MediaPipe Face Mesh (468 landmarks).
- Cognitive load analysis — blink rate, EAR, gaze stability, micro-tension.
- RAG engine — IBM watsonx.ai + LangChain + ChromaDB.
- Dynamic UI orchestration — biometric token → presentation mode.
- WebSocket real-time pipeline.
- Ephemeral session lifecycle management.
- FastAPI backend, React + TypeScript frontend.

---

## Version History

| Version | Date | Highlight |
|---------|------|-----------|
| 3.0.0 | 2025-07-01 | Docker stack, video library, challenge-ready docs |
| 2.1.0 | 2025-06-29 | Local AI video, resource ingestion, streaming RAG |
| 2.0.0 | 2024-06-22 | Voice narration, 15 content modules |
| 1.0.0 | 2024-06-15 | Initial release |

---

**Made with ❤️ for the IBM AI Builders Challenge 2026**
