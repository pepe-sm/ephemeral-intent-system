# Backend Dockerfile — Ephemeral Intent Synthesis System
# Multi-stage build: keeps the final image lean (~500 MB)

# ── Stage 1: dependency cache ──────────────────────────────────────────────
FROM python:3.11-slim AS deps

WORKDIR /build

# System libraries needed to compile wheels (numpy, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Runtime system libraries only
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed Python packages from the deps stage
COPY --from=deps /install /usr/local

# Copy application source
COPY --chown=appuser:appuser . .

# Create runtime directories
RUN mkdir -p /app/data/videos /app/backend/chroma_db && \
    chown -R appuser:appuser /app/data /app/backend/chroma_db

USER appuser

# FastAPI port
EXPOSE 8000

# Health check — waits up to 60 s for RAG warm-up
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default environment (overridden by docker-compose or .env mount)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000

CMD ["python", "run.py"]

# Made with Bob
