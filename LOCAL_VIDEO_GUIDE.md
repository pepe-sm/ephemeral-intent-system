# Local Video Generator Guide
## On-Device Talking-Head Videos for Ephemeral Intent Synthesis System

**Last Updated:** 2024-06-29  
**Status:** Optional Feature ✅ (disabled until tools are installed)

---

## 📋 Overview

This guide explains how to enable **fully local, API-free video generation** in the Ephemeral Intent Synthesis System. When active, the system produces instructor-style talking-head videos for every learning session — no data leaves your machine.

### How It Works

```
RAG Engine (Ollama)
       │
       │  script text
       ▼
  ┌─────────────┐      WAV audio      ┌──────────────┐     MP4 video
  │  Piper TTS  │ ──────────────────► │   Wav2Lip    │ ───────────────► Frontend
  │  (~50 MB)   │                     │  (~450 MB)   │
  └─────────────┘                     └──────────────┘
   CPU, real-time                      CPU: ~60 s/clip
                                       GPU: ~10 s/clip
```

### Why These Tools

| Component | Tool | Why |
|---|---|---|
| **Text → Speech** | [Piper](https://github.com/rhasspy/piper) | Single binary, ~50 MB voice model, faster than real-time on CPU |
| **Speech → Face** | [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) | Best lip-sync accuracy at lowest model weight (~450 MB) |
| **Assembly** | ffmpeg | Standard system tool, no extra download needed |

---

## 🚀 Quick Start

### Step 1 — Install ffmpeg

#### Windows
```powershell
# Via winget (recommended)
winget install Gyan.FFmpeg

# Or download from https://ffmpeg.org/download.html
# Add bin/ folder to your PATH
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt install ffmpeg
```

Verify:
```bash
ffmpeg -version
# Should print version info — e.g., ffmpeg version 6.x
```

---

### Step 2 — Install Piper TTS

Piper is a single self-contained binary. No Python packages needed.

#### Windows
1. Go to https://github.com/rhasspy/piper/releases/latest
2. Download `piper_windows_amd64.zip`
3. Extract to a folder, e.g. `C:\tools\piper\`
4. The binary is `C:\tools\piper\piper.exe`

#### macOS
```bash
# Download and extract
curl -L https://github.com/rhasspy/piper/releases/latest/download/piper_macos_amd64.tar.gz | tar xz
sudo mv piper /usr/local/bin/piper
```

#### Linux
```bash
curl -L https://github.com/rhasspy/piper/releases/latest/download/piper_linux_amd64.tar.gz | tar xz
sudo mv piper /usr/local/bin/piper
```

---

### Step 3 — Download a Piper Voice Model

Voice models are `.onnx` + `.onnx.json` file pairs. The recommended model is:

**`en_US-lessac-medium`** (~60 MB) — Clear, natural American English

```bash
# Create a directory for voice models
mkdir -p models/piper-voices
cd models/piper-voices

# Download the voice model (two files)
curl -L -O https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
curl -L -O https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

Test it works:
```bash
echo "Hello, let me explain this concept to you." | piper \
  --model models/piper-voices/en_US-lessac-medium.onnx \
  --output_file test.wav

# Play the result
# Windows: start test.wav
# macOS:   afplay test.wav
# Linux:   aplay test.wav
```

#### Alternative Voice Models

| Model | Size | Quality | Speed |
|---|---|---|---|
| `en_US-lessac-medium` ⭐ | ~60 MB | ⭐⭐⭐⭐ | Real-time |
| `en_US-amy-low` | ~25 MB | ⭐⭐⭐ | Very fast |
| `en_GB-alan-medium` | ~60 MB | ⭐⭐⭐⭐ | Real-time |
| `en_US-ryan-high` | ~130 MB | ⭐⭐⭐⭐⭐ | Slightly slower |

Browse all voices at: https://huggingface.co/rhasspy/piper-voices

---

### Step 4 — Set Up Wav2Lip

Wav2Lip requires Python, PyTorch, and OpenCV. It runs inside its own directory as a subprocess.

#### 4a. Clone the repository
```bash
git clone https://github.com/Rudrabha/Wav2Lip.git
cd Wav2Lip
```

#### 4b. Install Wav2Lip's Python dependencies
```bash
# Inside the Wav2Lip directory
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install opencv-python-headless librosa numpy tqdm
```

> **GPU acceleration (optional):**  
> If you have an NVIDIA GPU, replace the torch install line with:
> ```bash
> pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
> ```
> Generation time drops from ~60 s to ~10 s per clip.

#### 4c. Download the pre-trained model checkpoint

```bash
# From inside the Wav2Lip directory
mkdir -p checkpoints

# Download wav2lip.pth (~440 MB)
# Option A — gdown (Google Drive)
pip install gdown
gdown https://drive.google.com/uc?id=1dwHujOSEoOsKY_mTfRMBi0GDL-j5LYAB -O checkpoints/wav2lip.pth

# Option B — direct download if you have the link
# wget "LINK" -O checkpoints/wav2lip.pth
```

> The model file is also available on the  
> [Wav2Lip releases page](https://github.com/Rudrabha/Wav2Lip/releases) and various mirrors.

#### 4d. Test Wav2Lip
```bash
# Still inside Wav2Lip directory
python inference.py \
  --checkpoint_path checkpoints/wav2lip.pth \
  --face path/to/your_avatar.png \
  --audio path/to/test.wav \
  --outfile output_test.mp4

# Open output_test.mp4 — you should see the avatar speaking
```

---

### Step 5 — Prepare an Avatar Image

Wav2Lip needs a source face image. Requirements:
- **Format:** PNG or JPG
- **Resolution:** 512×512 px (recommended), minimum 256×256 px
- **Expression:** Neutral, mouth slightly closed
- **Lighting:** Even, frontal
- **Background:** Simple or blurred

You can:
- Use a photo of yourself
- Use a free AI-generated avatar from [thispersondoesnotexist.com](https://thispersondoesnotexist.com/)
- Use any neutral portrait photograph

Save it as `avatar.png` in your project, e.g. `backend/data/avatar.png`.

---

### Step 6 — Configure the Backend

Edit your `backend/.env` file:

```bash
# Enable the video generator
VIDEO_ENABLED=true

# Piper TTS
PIPER_BINARY=C:/tools/piper/piper.exe          # Windows
# PIPER_BINARY=/usr/local/bin/piper            # macOS/Linux
PIPER_MODEL=./models/piper-voices/en_US-lessac-medium.onnx

# Wav2Lip
WAV2LIP_DIR=./Wav2Lip
WAV2LIP_CHECKPOINT=./Wav2Lip/checkpoints/wav2lip.pth

# Avatar
AVATAR_IMAGE=./data/avatar.png

# Output and cache
VIDEO_OUTPUT_DIR=./data/videos
VIDEO_MAX_CACHE_ITEMS=50
```

---

### Step 7 — Verify the Setup

```bash
cd backend
python run.py
```

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "components": {
    "video_generator": "ready"
  }
}
```

If you see `"not_configured"`, check your `.env` paths.  
If you see `"disabled"`, set `VIDEO_ENABLED=true`.

---

## 💻 Using the Video Generator in Code

### Basic Usage

```python
from app.services.video_generator import VideoGenerator

generator = VideoGenerator()

# Async (recommended — won't block the event loop)
result = await generator.generate_async(
    script="Let me explain Python functions. A function is a reusable block of code...",
    session_id="sess_001",
    voice_pace="normal"   # "slow" | "normal" | "fast"
)

if result.success and not result.is_mock:
    print(f"Video ready: {result.video_path}")
    print(f"Generated in: {result.generation_time_ms:.0f}ms")
elif result.is_mock:
    print("Video generator not configured — showing text only")
else:
    print(f"Generation failed: {result.error}")
```

### Integrating with the RAG Pipeline

```python
from app.services.rag_engine import RAGEngine
from app.services.video_generator import VideoGenerator
from app.models.knowledge_payload import RAGQueryRequest

rag = RAGEngine(use_ollama=True)
video = VideoGenerator()

# Query knowledge
request = RAGQueryRequest(
    session_id="sess_001",
    query="What is Python?"
)
response = await rag.query(request)

# Build a narration script from the first teaching module
first_module = response.payload.teaching_modules[0]
script = f"{first_module.title}. {first_module.content}"

# Generate video in the background
result = await video.generate_async(
    script=script,
    session_id=request.session_id,
    voice_pace="normal"
)
```

### Cache Management

```python
from app.services.video_cache import VideoCache

cache = VideoCache(cache_dir="./data/videos", max_items=50)

# See what's cached
print(cache.stats())
# {"cache_dir": "./data/videos", "current_items": 12, "total_size_mb": 87.4}

# Remove oldest videos if over limit
removed = cache.evict_oldest()

# Clear everything
cache.clear_all()
```

---

## 🖥️ System Requirements

### Minimum (CPU-only)

| Component | Requirement |
|---|---|
| **RAM** | 4 GB (2 GB for Wav2Lip + 1 GB headroom) |
| **Storage** | 1 GB (models + output cache) |
| **CPU** | Any modern multi-core |
| **GPU** | Not required |

### Recommended

| Component | Requirement |
|---|---|
| **RAM** | 8 GB+ |
| **Storage** | 5 GB+ |
| **CPU** | 8+ cores |
| **GPU** | NVIDIA with 4 GB+ VRAM (CUDA) — optional |

### Generation Time Reference

| Hardware | Time per 30-second clip |
|---|---|
| Modern CPU (8-core) | 45–90 seconds |
| Older CPU (4-core) | 90–180 seconds |
| NVIDIA GPU (4 GB VRAM) | 8–15 seconds |
| NVIDIA GPU (8 GB VRAM) | 5–10 seconds |

> Generation happens asynchronously. The user sees text content immediately;  
> the video appears when ready.

---

## 🔄 Switching Video On/Off

### Enable video generation
```bash
# .env
VIDEO_ENABLED=true
```

### Disable video generation (text-only mode)
```bash
# .env
VIDEO_ENABLED=false
```

When disabled, `VideoGenerator.generate()` returns immediately with `is_mock=True`. The rest of the system (RAG, UI orchestration) continues working normally — video is purely additive.

---

## 📊 Performance Comparison

| Metric | Local Pipeline | D-ID API | HeyGen API |
|---|---|---|---|
| **Cost** | Free | $5.90/month | $24/month |
| **Privacy** | 100% local | Cloud | Cloud |
| **Offline** | ✅ Yes | ❌ No | ❌ No |
| **Setup time** | ~20 minutes | 5 minutes | 5 minutes |
| **Latency per clip** | 45–90 s (CPU) | 30–120 s | 30–120 s |
| **Avatar quality** | Good | Excellent | Excellent |
| **Custom avatar** | Any image | Extra cost | Extra cost |

---

## 🐛 Troubleshooting

### `"video_generator": "not_configured"` in /health

**Cause:** One or more `.env` paths are missing or wrong.

**Fix:**
```bash
# Check each path exists
ls -la $PIPER_BINARY
ls -la $PIPER_MODEL
ls -la $WAV2LIP_DIR/inference.py
ls -la $WAV2LIP_CHECKPOINT
ls -la $AVATAR_IMAGE
```

---

### Piper produces no audio / empty WAV

**Cause:** Model `.onnx.json` config file missing alongside the `.onnx`.

**Fix:** Both files must be in the same directory:
```
models/piper-voices/
├── en_US-lessac-medium.onnx
└── en_US-lessac-medium.onnx.json   ← must be present
```

---

### Wav2Lip `ModuleNotFoundError: No module named 'cv2'`

**Fix:**
```bash
cd Wav2Lip
pip install opencv-python-headless
```

---

### Wav2Lip output video has no audio

Wav2Lip merges audio during its own processing. If the output is silent, check:
```bash
# Confirm your WAV has audio
ffprobe path/to/speech.wav
# Should show: Stream #0:0: Audio: pcm_s16le
```

---

### Generation is very slow (>3 minutes)

**Solutions:**
1. Use a shorter script (first module only, not all modules)
2. Reduce resolution: add `--resize_factor 2` to the Wav2Lip command in `video_generator.py`
3. Install GPU-accelerated PyTorch (see Step 4b)

---

### Out of disk space

The video cache grows over time. Run eviction manually:
```python
from app.services.video_cache import VideoCache
VideoCache().clear_all()
```
Or lower `VIDEO_MAX_CACHE_ITEMS` in `.env`.

---

## 🔐 Privacy & Security

- ✅ All processing is local — no frames or audio leave your machine
- ✅ Generated videos are stored in `VIDEO_OUTPUT_DIR` only (local disk)
- ✅ Cache files are named by content hash — no session IDs in filenames
- ✅ `VIDEO_ENABLED=false` by default — must explicitly opt-in

---

## 📚 Resources

- Piper GitHub: https://github.com/rhasspy/piper
- Piper Voice Library: https://huggingface.co/rhasspy/piper-voices
- Wav2Lip GitHub: https://github.com/Rudrabha/Wav2Lip
- Wav2Lip Paper: https://arxiv.org/abs/2008.10010
- ffmpeg Download: https://ffmpeg.org/download.html

---

## 📝 Changelog

### v1.0.0 (2024-06-29)
- ✅ Initial local video generator implementation
- ✅ Piper TTS subprocess wrapper
- ✅ Wav2Lip subprocess wrapper
- ✅ On-disk LRU cache with eviction
- ✅ Async-safe (runs in thread pool — never blocks event loop)
- ✅ Mock mode when tools not configured
- ✅ Health endpoint integration

---

**Made with ❤️ for IBM AI Builders Challenge 2024**  
**Powered by Piper + Wav2Lip — Local AI Video for Everyone**
