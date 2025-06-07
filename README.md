# Oreno GRC v2

Oreno is a multi-tenant Governance, Risk, and Compliance (GRC) platform built with Django. The system combines several domain-specific apps (audit, risk, compliance, etc.) under one tenant-aware architecture so each organization operates in an isolated schema while sharing the same codebase.

## Features

- **Multi-Tenant Architecture** – Uses [`django_tenants`](https://github.com/django-tenants/django-tenants) so organizations have their own database schema and routing based on domain names.
- **Custom User Model** – Replaces Django's default user with `CustomUser` from `apps/users` and supports optional OTP-based login flows.
- **AI Assistant Integration** – `services/ai` provides local LLM integration through Ollama with an optional OpenAI fallback.
- **Modular Apps** – Business domains such as audit, risk, contracts, and compliance live in their own Django apps under `apps/`.

## Repository Structure

- **config/** – Settings modules, WSGI/ASGI config, URL routing, and Celery setup.
- **apps/** – Domain-specific applications. Common abstract models and mixins live in `apps/core`.
- **common/** – Reusable utilities and middleware.
- **services/** – External integrations like the AI assistant.
- **templates/** and **static/** – HTML templates and static assets.
- **tests/** – Unit tests for various apps (e.g., OTP logic under `apps/users/tests`).

## Getting Started

1. Clone the repository and create a Python 3.11 virtual environment.
2. Install dependencies from `requirements.txt`.
3. Create a `.env.oreno` file (see the example in the repo) and update database credentials and the Django secret key.
4. Run database migrations:
   ```bash
   python manage.py migrate --settings=config.settings.development
   ```
5. (Optional) create a superuser:
   ```bash
   python manage.py createsuperuser --settings=config.settings.development
   ```
6. Start the development server:
   ```bash
   python manage.py runserver --settings=config.settings.development
   ```

## Running Tests

The repository contains Django test cases. Run them with:

```bash
python manage.py test --settings=config.settings.development
```

## Database Dumps

Database dump files for development are not tracked in version control.
If you need sample dumps, request them from the maintainers and store them
outside the repository (for example in a sibling `dumps/` directory).
Update any local scripts to load the dump from that location.

## Learning More

Explore each app under `apps/` to see how domain logic is implemented. Reviewing tests is a good way to understand expected behavior. The `config/settings` modules show how environments are configured for development or production. To learn about tenant management, inspect the `organizations` app and middleware in `apps/core`.
