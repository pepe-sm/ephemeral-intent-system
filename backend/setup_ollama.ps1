# PowerShell setup script for Ollama integration on Windows

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Ollama Integration Setup (Windows)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
$ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $ollamaInstalled) {
    Write-Host "❌ Ollama is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Ollama first:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://ollama.ai/" -ForegroundColor Yellow
    Write-Host "  2. Or use WSL2: curl -fsSL https://ollama.ai/install.sh | sh" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "✅ Ollama is installed" -ForegroundColor Green
Write-Host ""

# Check if Ollama is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ Ollama is running" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Ollama is not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please start Ollama:" -ForegroundColor Yellow
    Write-Host "  - Windows: Start Ollama from Start Menu" -ForegroundColor Yellow
    Write-Host "  - WSL2: ollama serve" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Check for llama3.2 model
Write-Host "Checking for llama3.2 model..." -ForegroundColor Cyan
$models = ollama list

if ($models -match "llama3.2") {
    Write-Host "✅ llama3.2 is already installed" -ForegroundColor Green
}
else {
    Write-Host "📦 Downloading llama3.2 model (this may take a few minutes)..." -ForegroundColor Yellow
    ollama pull llama3.2
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ llama3.2 downloaded successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to download llama3.2" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "📋 Installed models:" -ForegroundColor Cyan
ollama list

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Install Python dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "  2. Configure .env file: Copy-Item .env.example .env" -ForegroundColor White
Write-Host "  3. Set USE_OLLAMA=true in .env" -ForegroundColor White
Write-Host "  4. Run test: python test_ollama_integration.py" -ForegroundColor White
Write-Host "  5. Start backend: uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""

# Made with Bob
