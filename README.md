# BANKING_APPLICATION

## Overview

Monorepo for a banking application.

* `backend/` — Django + PostgreSQL
* `frontend/` — placeholder service (stub)

The project is designed to be started locally with a single command via Docker Compose.

## Requirements

* Docker
* Docker Compose (v2)

## Quick start

1. Create local env file:

```bash
cp .env.example .env
```

On Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

1. Start services:

```bash
docker compose up --build
```

## How to verify everything works

### Backend

* Open: `http://localhost:8000/` (should return `OK`)
* Admin: `http://localhost:8000/admin/`

Run migrations (in a separate terminal):

```bash
docker compose exec backend python manage.py migrate
```

### Frontend (stub)

* Open: `http://localhost:3000/` (should return placeholder text)

## Project structure

```text
BANKING_APPLICATION/
  backend/
    Dockerfile
    manage.py
    requirements.txt
    config/
      __init__.py
      settings.py
      urls.py
      asgi.py
      wsgi.py
    apps/
      core/
        migrations/
        models.py
        apps.py

  frontend/
    Dockerfile
    package.json
    src/

  docker-compose.yml
  .env.example
  docs/
  README.md

## ENV strategy

* All configuration is provided via environment variables.
* Create your local `.env` from `.env.example`.
* `.env` must not be committed (it is ignored by `.gitignore`).

## Notes
* Stage 2 does not include business logic, ledger models, or auth.
* Documentation for Stage 1 (data model & invariants) is located in `docs/`.
