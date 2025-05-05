# syntax=docker/dockerfile:1

# --- Build stage ---
    FROM python:3.12-slim AS builder
    WORKDIR /app
    
    # Install build deps
    RUN apt-get update \
     && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
     && rm -rf /var/lib/apt/lists/*
    
    COPY requirements.txt ./
    RUN pip install --upgrade pip \
     && pip install --upgrade pip && pip install -r requirements.txt
    
    # --- Runtime stage ---
    FROM python:3.12-slim
    WORKDIR /app
    
    # Install runtime deps (system-level libpq)
    RUN apt-get update \
     && apt-get install -y --no-install-recommends libpq5 \
     && rm -rf /var/lib/apt/lists/*
    
    # Copy Python packages from builder
    COPY --from=builder /root/.local /root/.local
    RUN pip install --no-cache-dir gunicorn

    # Copy application code
    COPY . .
    
    # Create directories expected by Django logging
    RUN mkdir -p /app/logs /app/staticfiles
    
    # Collect static assets
    RUN python manage.py collectstatic --noinput
    
    # Expose HTTP port
    EXPOSE 8000
    
    # Healthcheck (ensure you have a /health/ view)
    HEALTHCHECK CMD curl --fail http://localhost:8000/health/ || exit 1
    
    # Metadata
    LABEL maintainer="fredfreeman68@gmail.com" \
          org.opencontainers.image.source="https://github.com/oumafreddy/oreno"
    
    # (Optional) Use a non-root user for security
    RUN useradd -m django && chown -R django /app
    USER django
    
    # Entrypoint: start Gunicorn
    CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
    