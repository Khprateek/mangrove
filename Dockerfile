# Production Dockerfile for Mangrove SCM Cockpit Appliance
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

# Install system dependencies for networking and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application modules and deterministic data
COPY src/ ./src/
COPY data/ ./data/
COPY assets/ ./assets/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY .env.example ./.env

EXPOSE 8501

# Container healthcheck for automated orchestration
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Launch self-bootstrapping appliance entrypoint
ENTRYPOINT ["python", "scripts/entrypoint.py"]
