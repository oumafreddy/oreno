# syntax=docker/dockerfile:1

############################################################
# 1. Builder Stage
############################################################
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 1.1 Install build-time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
      libcairo2-dev \
      libpango1.0-dev \
      libpangoft2-1.0-0 \
      libharfbuzz-dev \
      libgdk-pixbuf2.0-dev \
      libfontconfig1 \
      libxml2 \
      libxslt1.1 \
      libffi-dev \
      libglib2.0-dev \
      libjpeg62-turbo-dev \
      libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# 1.2 Create virtual environment & install Python packages
RUN python3 -m venv $VIRTUAL_ENV \
 && pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 1.3 Copy application source
COPY . .

############################################################
# 2. Runtime Stage
############################################################
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    HOME=/app \
    MPLCONFIGDIR=/app/.cache/matplotlib

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install runtime libs (WeasyPrint, Postgres client, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl libpq5 libcairo2 libpango-1.0-0 libpangoft2-1.0-0 \
      libharfbuzz-subset0 libgdk-pixbuf2.0-0 libfontconfig1 \
      libxml2 libxslt1.1 libffi8 libglib2.0-0 libjpeg62-turbo \
      libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Prepare directories for logs, static files, Matplotlib cache
RUN mkdir -p /app/logs /app/static /app/staticfiles /app/.cache/matplotlib \
 && touch /app/logs/development.log

# Copy venv and app, set ownership...
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
RUN addgroup --system django \
 && adduser --system --ingroup django django \
 && chown -R django:django /app /opt/venv

# Entrypoint...
# Add wait-for-db capability
RUN apt-get update && apt-get install -y --no-install-recommends netcat
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--log-level=debug"]
