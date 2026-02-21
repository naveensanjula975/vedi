# Dockerfile for Vedic Astrology Backend

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Swiss Ephemeris
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir pip --upgrade && \
    pip install --no-cache-dir .

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run the application — uses $PORT injected by Render/cloud hosts, fallback to 8000 locally
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}

