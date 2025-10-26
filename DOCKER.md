# Docker Setup Guide (Optional)

This guide explains how to use Docker with Oreno GRC. Docker is **optional** and not required for development or deployment.

## Why Use Docker?

Docker provides:
- Consistent development environments
- Easy deployment options
- Simplified dependency management
- Containerized production deployments

## Prerequisites

- Docker installed on your system
- Docker Compose (usually included with Docker)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/oumafreddy/oreno.git
   cd oreno
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Web interface: http://localhost:8000
   - Database: localhost:5432

## Docker Services

The `docker-compose.yml` includes:

- **web**: Django application server
- **db**: PostgreSQL database
- **redis**: Redis cache (if needed)
- **celery**: Background task worker

## Environment Configuration

Docker uses environment variables from `docker-compose.yml`. You can:

1. **Modify docker-compose.yml** directly
2. **Create .env file** for local overrides
3. **Use environment variables** in your shell

## Development with Docker

### Running Commands

```bash
# Run Django management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U oreno_user -d oreno

# View logs
docker-compose logs db
```

### Debugging

```bash
# View application logs
docker-compose logs web

# Follow logs in real-time
docker-compose logs -f web
```

## Production Deployment

### Building Production Image

```bash
# Build production image
docker build -t oumafreddy/oreno:latest .

# Run production container
docker run -d \
  --name oreno-app \
  -p 8000:8000 \
  -e DJANGO_SETTINGS_MODULE=config.settings.production \
  oumafreddy/oreno:latest
```

### Environment Variables for Production

```bash
# Required production variables
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DB_ENGINE=django.db.backends.postgresql
DB_NAME=oreno_prod
DB_USER=oreno_user
DB_PASS=secure-password
DB_HOST=your-db-host
```

## Docker Hub Integration (Optional)

To enable automatic Docker builds in CI/CD:

1. **Create Docker Hub account**
2. **Add repository secrets** in GitHub:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub password/token

3. **Uncomment Docker section** in `.github/workflows/ci.yml`

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

**Database connection issues:**
```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db
```

**Permission issues:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### Useful Commands

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache

# View resource usage
docker stats
```

## Alternative: Python-Only Setup

If you prefer not to use Docker:

1. **Install Python 3.11+**
2. **Install PostgreSQL**
3. **Follow standard setup** in README.md
4. **Use virtual environment** for isolation

## Support

For Docker-related issues:
- Check Docker documentation
- Review docker-compose logs
- Contact: fredouma@oreno.tech | oumafredomondi@gmail.com

---

**Remember**: Docker is optional! You can develop and deploy Oreno GRC using standard Python tools without Docker.
