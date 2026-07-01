#!/bin/bash
# Setup script for Ollama integration

echo "=================================================="
echo "Ollama Integration Setup"
echo "=================================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed"
    echo ""
    echo "Please install Ollama first:"
    echo "  Linux/WSL: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  macOS: brew install ollama"
    echo "  Windows: Download from https://ollama.ai/"
    echo ""
    exit 1
fi

echo "✅ Ollama is installed"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running"
    echo ""
    echo "Starting Ollama in background..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "❌ Failed to start Ollama"
        echo "Please start manually: ollama serve"
        exit 1
    fi
fi

echo "✅ Ollama is running"
echo ""

# Check for llama3.2 model
echo "Checking for llama3.2 model..."
if ollama list | grep -q "llama3.2"; then
    echo "✅ llama3.2 is already installed"
else
    echo "📦 Downloading llama3.2 model (this may take a few minutes)..."
    ollama pull llama3.2
    
    if [ $? -eq 0 ]; then
        echo "✅ llama3.2 downloaded successfully"
    else
        echo "❌ Failed to download llama3.2"
        exit 1
    fi
fi

echo ""
echo "📋 Installed models:"
ollama list

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Install Python dependencies: pip install -r requirements.txt"
echo "  2. Configure .env file: cp .env.example .env"
echo "  3. Set USE_OLLAMA=true in .env"
echo "  4. Run test: python test_ollama_integration.py"
echo "  5. Start backend: uvicorn app.main:app --reload"
echo ""

# Made with Bob
