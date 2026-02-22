# Dockerfile for Vedic Astrology Backend
#
# Security hardening applied:
#     - Run container as non-root user (appuser)
#     - Install from poetry.lock for reproducible/pinned builds

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Swiss Ephemeris + Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

#  : Create a non-root user before any app code is present
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

#  : Install exact versions from lockfile using Poetry
# --no-dev    skips pytest / httpx etc.
# --no-root   skips installing the project package itself (done below)
RUN pip install --no-cache-dir "poetry==1.8.3" && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root --no-interaction --no-ansi

# Copy source code
COPY src/ ./src/

# Give the non-root user ownership of the app directory
RUN chown -R appuser:appgroup /app

#  : Drop privileges — run as non-root
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run the application — $PORT injected by Heroku/Render, fallback to 8000 locally
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
