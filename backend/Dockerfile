# syntax=docker/dockerfile:1
# --- Build Stage ---
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- Final Runtime Stage ---
FROM python:3.13-slim AS runner

WORKDIR /app

# Install runtime dependencies for psycopg2 and curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY app /app/backend/app

# Ensure proper ownership
RUN chown -R appuser:appgroup /app /home/appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
