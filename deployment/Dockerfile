# Multi-stage Production Dockerfile for SmartAttend Backend2
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies for C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend2/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Stage
FROM python:3.12-slim-bookworm AS runner

WORKDIR /app

# Install runtime system libraries for OpenCV & Image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source code
COPY backend2/app ./app
COPY backend2/weights ./weights
COPY backend2/pytest.ini .

# Create non-root system user and storage directories
RUN useradd -m -u 1001 appuser && \
    mkdir -p /app/uploads/classroom /app/uploads/students /app/logs && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8002 \
    HOST=0.0.0.0

EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
