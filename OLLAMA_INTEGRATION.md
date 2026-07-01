# Ollama Integration Guide
## Local AI for Ephemeral Intent Synthesis System

**Last Updated:** 2024-06-29  
**Status:** Production Ready ✅

---

## 📋 Overview

This guide explains how to use **Ollama** as a local AI alternative to IBM watsonx.ai for the RAG (Retrieval-Augmented Generation) engine. Ollama provides completely free, private, and fast local AI inference.

### Benefits of Ollama Integration

✅ **Completely Free** - No API costs or usage limits  
✅ **Privacy First** - All data stays on your machine  
✅ **Fast Response** - Low latency local inference  
✅ **No Internet Required** - Works offline after model download  
✅ **Easy Setup** - Simple installation and configuration  
✅ **Multiple Models** - Choose from various open-source models  

---

## 🚀 Quick Start

### 1. Install Ollama

#### Windows (WSL2 Recommended)
```bash
# In WSL2 terminal
curl -fsSL https://ollama.ai/install.sh | sh
```

#### macOS
```bash
brew install ollama
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Service

```bash
# Start Ollama server
ollama serve
```

The server will run on `http://localhost:11434`

### 3. Pull Recommended Model

```bash
# Download llama3.2 (recommended for education)
ollama pull llama3.2

# Optional: Download additional models
ollama pull codellama:7b  # For programming tutorials
ollama pull phi3:mini     # For fast responses
```

### 4. Configure Backend

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Set these values in `.env`:
```bash
USE_OLLAMA=true
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### 5. Install Python Dependencies

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (includes ollama packages)
pip install -r requirements.txt
```

### 6. Run the Application

```bash
# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO: RAGEngine initialized with ollama provider (model: llama3.2)
```

---

## 🎯 Recommended Models

### For Educational Content (Primary Use Case)

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.2** ⭐ | 3B | ⚡⚡⚡ | ⭐⭐⭐⭐ | General education, explanations |
| llama3.1:8b | 8B | ⚡⚡ | ⭐⭐⭐⭐⭐ | Detailed teaching, complex topics |
| codellama:7b | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Programming tutorials, code examples |
| phi3:mini | 3.8B | ⚡⚡⚡ | ⭐⭐⭐ | Quick responses, simple explanations |
| mistral:7b | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Advanced reasoning, complex concepts |

⭐ = **Recommended starting model**

### Model Selection Guide

**Choose `llama3.2` if:**
- You want balanced speed and quality
- Teaching general concepts
- Need good explanations with examples
- Have 4-8GB RAM available

**Choose `codellama:7b` if:**
- Focus on programming education
- Need code examples and debugging help
- Teaching software development
- Have 8-16GB RAM available

**Choose `phi3:mini` if:**
- Speed is critical
- Simple Q&A format
- Limited hardware (4GB RAM)
- Quick reference lookups

**Choose `llama3.1:8b` if:**
- Need highest quality responses
- Teaching complex subjects
- Have 16GB+ RAM available
- Can accept slower response times

---

## 🔧 Configuration Options

### Environment Variables

```bash
# Required
USE_OLLAMA=true                          # Enable Ollama
OLLAMA_MODEL=llama3.2                    # Model name
OLLAMA_BASE_URL=http://localhost:11434   # Ollama API URL

# Optional - IBM watsonx.ai (fallback)
WATSONX_API_KEY=                         # Leave empty when using Ollama
WATSONX_PROJECT_ID=                      # Leave empty when using Ollama
```

### Multi-Model Setup

You can download multiple models and switch between them:

```bash
# Download models
ollama pull llama3.2
ollama pull codellama:7b
ollama pull phi3:mini

# List installed models
ollama list

# Switch models by updating .env
OLLAMA_MODEL=codellama:7b  # For programming queries
OLLAMA_MODEL=llama3.2      # For general education
```

### Advanced Configuration

```python
# In your code, you can initialize with custom settings
from app.services.rag_engine import RAGEngine

rag_engine = RAGEngine(
    use_ollama=True,
    ollama_model="llama3.2",
    ollama_base_url="http://localhost:11434"
)
```

---

## 🖥️ System Requirements

### Minimum Requirements
- **RAM:** 4GB (for 3B models like llama3.2, phi3:mini)
- **Storage:** 2-5GB per model
- **CPU:** Modern multi-core processor
- **OS:** Windows 10/11 (WSL2), macOS 11+, Linux

### Recommended Requirements
- **RAM:** 8-16GB (for 7B models like codellama, mistral)
- **Storage:** 10GB+ for multiple models
- **CPU:** 8+ cores
- **GPU:** Optional (NVIDIA with CUDA for faster inference)

### Model Size Reference
```
llama3.2 (3B)      → ~2GB download, ~4GB RAM
phi3:mini (3.8B)   → ~2.3GB download, ~4GB RAM
codellama:7b       → ~4GB download, ~8GB RAM
mistral:7b         → ~4GB download, ~8GB RAM
llama3.1:8b        → ~4.7GB download, ~10GB RAM
```

---

## 🔍 Testing the Integration

### 1. Test Ollama Connection

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return JSON with installed models
```

### 2. Test Model Inference

```bash
# Test model directly
ollama run llama3.2 "Explain Python variables in simple terms"
```

### 3. Test Backend Integration

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Check logs for:
# "RAGEngine initialized with ollama provider (model: llama3.2)"
```

### 4. Test Full Pipeline

```python
# Test script: test_ollama.py
import asyncio
from app.services.rag_engine import RAGEngine
from app.models.knowledge_payload import RAGQueryRequest

async def test_ollama():
    engine = RAGEngine(use_ollama=True)
    
    request = RAGQueryRequest(
        session_id="test_001",
        query="What is Python?",
        max_sources=3
    )
    
    response = await engine.query(request)
    print(f"Success: {response.success}")
    print(f"Modules: {len(response.payload.teaching_modules)}")
    print(f"Core Concept: {response.payload.core_concept}")

asyncio.run(test_ollama())
```

---

## 🐛 Troubleshooting

### Issue: "Ollama SDK not available"

**Solution:**
```bash
pip install ollama langchain-ollama
```

### Issue: "Failed to initialize Ollama"

**Cause:** Ollama service not running

**Solution:**
```bash
# Start Ollama
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

### Issue: "Model 'llama3.2' not found"

**Solution:**
```bash
# Pull the model
ollama pull llama3.2

# Verify installation
ollama list
```

### Issue: Slow responses

**Solutions:**
1. Use smaller model: `phi3:mini` instead of `llama3.1:8b`
2. Close other applications to free RAM
3. Enable GPU acceleration (if available)
4. Reduce context length in prompts

### Issue: Out of memory

**Solutions:**
1. Use smaller model (3B instead of 7B)
2. Close other applications
3. Restart Ollama service
4. Check available RAM: `free -h` (Linux) or Task Manager (Windows)

### Issue: WSL2 connection problems

**Solution:**
```bash
# In WSL2, use localhost
OLLAMA_BASE_URL=http://localhost:11434

# If that doesn't work, use WSL2 IP
ip addr show eth0 | grep inet
# Use the IP shown, e.g., http://172.x.x.x:11434
```

---

## 🔄 Switching Between Ollama and watsonx.ai

### Use Ollama (Local)
```bash
# .env
USE_OLLAMA=true
OLLAMA_MODEL=llama3.2
```

### Use IBM watsonx.ai (Cloud)
```bash
# .env
USE_OLLAMA=false
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
```

### Automatic Fallback

The system automatically falls back to mock mode if neither provider is available:

```python
# Priority order:
1. Ollama (if USE_OLLAMA=true and Ollama is running)
2. watsonx.ai (if credentials provided)
3. Mock mode (pre-defined educational content)
```

---

## 📊 Performance Comparison

| Metric | Ollama (llama3.2) | watsonx.ai | Mock Mode |
|--------|-------------------|------------|-----------|
| **Response Time** | 2-5s | 3-8s | <100ms |
| **Cost** | Free | Pay per token | Free |
| **Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Privacy** | 100% local | Cloud | Local |
| **Offline** | ✅ Yes | ❌ No | ✅ Yes |
| **Setup** | Easy | Medium | None |

---

## 🎓 Educational Content Examples

### Example 1: Programming Query

**Query:** "Explain Python functions"

**Ollama Response:**
```
Module 1: Understanding Functions
- Functions are reusable blocks of code
- They help organize and structure programs
- Example: def greet(name): return f"Hello, {name}!"

Module 2: Function Parameters
- Functions can accept inputs (parameters)
- Return values send data back to caller
- Example with multiple parameters...
```

### Example 2: Web Development Query

**Query:** "How do I create a responsive website?"

**Ollama Response:**
```
Module 1: Responsive Design Basics
- Use flexible layouts (flexbox, grid)
- Media queries for different screen sizes
- Mobile-first approach...

Module 2: Practical Implementation
- HTML structure with semantic tags
- CSS media queries example
- Testing on different devices...
```

---

## 🔐 Security & Privacy

### Data Privacy
- ✅ All processing happens locally
- ✅ No data sent to external servers
- ✅ No usage tracking or telemetry
- ✅ Complete control over your data

### Network Security
- Ollama runs on localhost by default
- No external network access required (after model download)
- Can run completely offline

### Best Practices
1. Keep Ollama updated: `ollama update`
2. Use firewall to restrict Ollama port (11434) to localhost
3. Don't expose Ollama to public internet
4. Regularly update models for security patches

---

## 📚 Additional Resources

### Official Documentation
- Ollama Website: https://ollama.ai/
- Ollama GitHub: https://github.com/ollama/ollama
- Model Library: https://ollama.ai/library

### Community
- Ollama Discord: https://discord.gg/ollama
- GitHub Discussions: https://github.com/ollama/ollama/discussions

### Model Information
- Llama 3.2: https://ollama.ai/library/llama3.2
- CodeLlama: https://ollama.ai/library/codellama
- Phi-3: https://ollama.ai/library/phi3

---

## 🤝 Contributing

Found an issue or have suggestions? Please contribute:

1. Test the integration
2. Report bugs in GitHub issues
3. Submit improvements via pull requests
4. Share your model recommendations

---

## 📝 Changelog

### v1.0.0 (2024-06-29)
- ✅ Initial Ollama integration
- ✅ Support for multiple models
- ✅ Automatic model detection and pulling
- ✅ Fallback to watsonx.ai or mock mode
- ✅ Comprehensive error handling
- ✅ WSL2 compatibility

---

## 📄 License

This integration is part of the Ephemeral Intent Synthesis System.  
MIT License - See LICENSE file for details.

---

**Made with ❤️ for IBM AI Builders Challenge 2024**  
**Powered by Ollama - Local AI for Everyone**