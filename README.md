# Oreno GRC v2

Oreno is a multi-tenant Governance, Risk, and Compliance (GRC) platform built with Django. The system combines several domain-specific apps (audit, risk, compliance, etc.) under one tenant-aware architecture so each organization operates in an isolated schema while sharing the same codebase.

## Features

- **Multi-Tenant Architecture** – Uses [`django_tenants`](https://github.com/django-tenants/django-tenants) so organizations have their own database schema and routing based on domain names.
- **Custom User Model** – Replaces Django's default user with `CustomUser` from `apps/users` and supports optional OTP-based login flows.
- **AI Assistant Integration** – `services/ai` provides local LLM integration through Ollama with an optional OpenAI fallback.
- **Modular Apps** – Business domains such as audit, risk, contracts, and compliance live in their own Django apps under `apps/`.

## Apps Overview

Oreno GRC is built around a set of modular Django apps, each handling a specific domain of governance, risk, and compliance:

- **Audit** – Manages the audit lifecycle, including workplans, engagements, objectives, procedures, issues, and recommendations. It follows the Global Internal Audit Standards (GIAS) 2024, ensuring a risk-based, objective-driven approach.
- **Risk** – Handles risk management, including risk registers, risk matrices, and key risk indicators (KRIs). It supports risk assessment, monitoring, and mitigation strategies.
- **Compliance** – Manages compliance frameworks, policy documents, compliance requirements, and obligations. It ensures that organizations meet regulatory and internal policy requirements.
- **Contracts** – Manages contract types, parties, contracts, and milestones. It supports contract lifecycle management, including drafting, execution, and monitoring.
- **Document Management** – Handles document requests and document uploads. It provides a secure way to manage and track documents within the organization.
- **Organizations** – Manages organization settings, subscriptions, and user associations. It supports multi-tenancy by isolating data and settings per organization.
- **Users** – Provides a custom user model and authentication mechanisms, including OTP-based login flows.
- **Core** – Contains common abstract models, mixins, and utilities used across the platform.
- **Admin Module** – Provides administrative functionalities for managing the platform.
- **AI Governance** – Handles AI models registration, setting up datasets, running tests using frameworks like EU AI act, NIST RSF and OECD guidelines.
- **Legal** – Handles legal aspects of the organization, including legal documents and compliance.
- **Reports** – Generates reports and analytics for various aspects of the platform.

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
3. Copy `.env.validations` to `.env.oreno` and update the values with your real secrets.
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
