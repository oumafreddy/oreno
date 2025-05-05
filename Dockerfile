syntax=docker/dockerfile:1

# --- Build stage ---
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --user -r requirements.txt

# --- Runtime stage ---
FROM python:3.12-slim
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy project files
COPY . .

# Create logs directory to satisfy Django file handler
RUN mkdir -p /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Healthcheck endpoint (ensure Django has a /health/ view)
HEALTHCHECK CMD curl --fail http://localhost:8000/health/ || exit 1

# Metadata labels
LABEL maintainer="fredfreeman68@gmail.com" \
      org.opencontainers.image.source="https://github.com/oumafreddy/oreno"

# Use a non-root user for security (optional, requires permission adjustments)
# RUN useradd -m django && chown -R django /app
# USER django

# Start Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]