# Quick Start Guide - Ephemeral Intent Synthesis System

## 🚀 Get Started in 5 Minutes

This guide will help you set up and run the Ephemeral Intent Synthesis System backend.

---

## Prerequisites

- **Python 3.11+** (tested on 3.12)
- **pip** package manager
- **Git** for version control
- **Webcam** (for future frontend integration)

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ephemeral-intent-system
```

### 2. Set Up Python Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This will install all required packages including:
- FastAPI & Uvicorn (API server)
- MediaPipe & OpenCV (biometric analysis)
- LangChain & ChromaDB (RAG engine)
- sentence-transformers (embeddings)
- IBM watsonx.ai SDK

**Installation time:** ~5-10 minutes depending on your internet connection.

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials (optional for demo)
# For demo mode, you can skip IBM watsonx.ai credentials
```

**Minimum configuration for demo:**
```env
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
MOCK_MODE=true
```

---

## Running the System

### Option 1: Run the Biometric Demo (Recommended First)

This standalone demo shows the biometric analyzer in action without requiring any external services.

```bash
cd backend
python demo_biometric_standalone.py
```

**Expected output:**
- 3 test scenarios (Normal, High Stress, Low Stress)
- Biometric analysis results for each
- Cognitive load classification
- Stress indicators
- Processing time metrics

**Demo runs in:** ~5 seconds

### Option 2: Start the FastAPI Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access the API:**
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **System Info:** http://localhost:8000/api/v1/system/info

**WebSocket endpoint:**
- **URL:** ws://localhost:8000/ws/{session_id}

### Option 3: Run the Full Service Demo

**Note:** Requires sentence-transformers to be installed.

```bash
cd backend
python demo_services.py
```

This demonstrates the full pipeline:
1. Biometric Analysis
2. Knowledge Synthesis (RAG)
3. UI Orchestration

---

## Testing

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Models only
pytest tests/test_models.py -v

# Biometric Analyzer only
pytest tests/test_biometric_analyzer.py -v

# UI Orchestrator only
pytest tests/test_ui_orchestrator.py -v

# RAG Engine only
pytest tests/test_rag_engine.py -v
```

### Run Tests with Coverage

```bash
pytest tests/ -v --cov=app --cov-report=html
```

View coverage report: `open htmlcov/index.html`

**Current Test Status:**
- ✅ 73/102 tests passing (71.5%)
- ✅ Models: 100% passing
- ✅ Biometric Analyzer: 92% coverage
- ✅ UI Orchestrator: 100% passing

---

## API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/v1/system/info` | GET | System information |
| `/api/v1/biometric/analyze` | POST | Analyze biometric data |
| `/api/v1/knowledge/query` | POST | Query knowledge base |
| `/api/v1/ui/orchestrate` | POST | Generate UI configuration |
| `/docs` | GET | Swagger documentation |

### WebSocket API

**Connect to:** `ws://localhost:8000/ws/{session_id}`

**Message Types:**

1. **Biometric Analysis**
```json
{
  "type": "biometric_analysis",
  "data": {
    "landmarks": [[x, y, z], ...],
    "frame_count": 90,
    "capture_duration": 3.0
  }
}
```

2. **Knowledge Query**
```json
{
  "type": "knowledge_query",
  "data": {
    "query": "How do I use React hooks?",
    "max_sources": 5,
    "complexity_preference": "intermediate"
  }
}
```

3. **Full Pipeline**
```json
{
  "type": "full_pipeline",
  "data": {
    "biometric": { ... },
    "query": { ... }
  }
}
```

4. **Ping (Health Check)**
```json
{
  "type": "ping"
}
```

---

## Project Structure

```
ephemeral-intent-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── websocket.py          # WebSocket handler
│   │   ├── models/
│   │   │   ├── biometric_token.py    # Biometric data models
│   │   │   └── knowledge_payload.py  # Knowledge data models
│   │   ├── services/
│   │   │   ├── biometric_analyzer.py # Facial analysis service
│   │   │   ├── rag_engine.py         # Knowledge retrieval
│   │   │   ├── ui_orchestrator.py    # Dynamic UI generation
│   │   │   └── lifecycle_manager.py  # Session management
│   │   └── main.py                   # FastAPI application
│   ├── tests/                        # Unit tests
│   ├── demo_biometric_standalone.py  # Standalone demo
│   ├── demo_services.py              # Full pipeline demo
│   ├── requirements.txt              # Python dependencies
│   └── .env.example                  # Environment template
├── frontend/                         # React frontend (TBD)
├── docs/                             # Documentation
├── README.md                         # Project overview
└── QUICKSTART.md                     # This file
```

---

## Common Issues & Solutions

### Issue: Import errors with LangChain

**Solution:** Make sure you have the latest requirements installed:
```bash
pip install --upgrade -r requirements.txt
```

### Issue: MediaPipe not found

**Solution:** MediaPipe requires specific Python versions. Ensure you're using Python 3.11 or 3.12:
```bash
python --version
```

### Issue: Tests failing with "sentence_transformers not found"

**Solution:** Install sentence-transformers:
```bash
pip install sentence-transformers>=2.2.0
```

### Issue: WebSocket connection refused

**Solution:** Make sure the FastAPI server is running:
```bash
uvicorn app.main:app --reload
```

---

## Development Workflow

### 1. Make Changes

Edit files in `backend/app/`

### 2. Run Tests

```bash
pytest tests/ -v
```

### 3. Test Manually

```bash
# Start server
uvicorn app.main:app --reload

# In another terminal, run demo
python demo_biometric_standalone.py
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: your feature description"
git push origin master
```

---

## Next Steps

### For Backend Development:
1. ✅ Install dependencies
2. ✅ Run biometric demo
3. ✅ Start FastAPI server
4. ⏳ Implement full API routes
5. ⏳ Add integration tests

### For Frontend Development:
1. ⏳ Set up React project
2. ⏳ Implement BiometricCapture component
3. ⏳ Create WebSocket client
4. ⏳ Build DynamicUI renderer
5. ⏳ Connect to backend

### For Production:
1. ⏳ Configure IBM watsonx.ai credentials
2. ⏳ Set up Redis for session management
3. ⏳ Configure Docker deployment
4. ⏳ Set up monitoring and logging
5. ⏳ Deploy to IBM Cloud

---

## Support & Resources

- **Documentation:** See `docs/` directory
- **API Docs:** http://localhost:8000/docs (when server is running)
- **Test Coverage:** Run `pytest --cov` and check `htmlcov/`
- **Issues:** Check GitHub issues or create a new one

---

## Performance Benchmarks

**Biometric Analysis:**
- Processing time: ~30-50ms per analysis
- Frames processed: 90 frames (3 seconds of video)
- Confidence: 80-100%

**API Response Times:**
- Health check: <5ms
- Biometric analysis: <100ms
- Knowledge query: <500ms (mock mode)
- Full pipeline: <1000ms

**Test Execution:**
- All tests: ~10-15 seconds
- Unit tests only: ~5 seconds

---

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ for the IBM AI Builders Challenge**

Last updated: 2026-06-22