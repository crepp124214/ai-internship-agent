# AI Internship Job Search Agent System

This repository is a full-stack demo workspace for an AI-assisted internship job search product. It combines a FastAPI backend, a React frontend, and four connected product flows: Resume, Jobs, Interview, and Tracker.

## What This Repo Includes

- FastAPI backend APIs
- React + Vite frontend workspace
- Resume / Jobs / Interview / Tracker demo flows
- Local migrations, demo seeds, and release scripts

## Current Status

The project is in a demo-ready engineering stage. Wave 1 through Wave 7 are complete, and the current focus is Wave 8 stabilization and release hardening.

## Quick Start

### 1. Install dependencies

Backend:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Frontend:

```bash
cd frontend
npm install
cd ..
```

### 2. Prepare environment files

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Recommended local values:

- `DATABASE_URL=sqlite:///./data/app.db`
- `LLM_PROVIDER=mock`
- `VITE_API_BASE_URL=http://127.0.0.1:8000`

### 3. Run migrations and seed demo data

```bash
python scripts/migrate.py
python scripts/seed_demo.py
```

Demo account:

- Username: `demo`
- Password: `demo123`

### 4. Start the backend

```bash
make dev
```

### 5. Start the frontend

```bash
cd frontend
npm run dev
```

## Demo Flow

Recommended walkthrough order:

1. Login
2. Dashboard
3. Resume
4. Jobs
5. Interview
6. Tracker

## Docker Compose Demo Path

The official release-style demo path uses Docker Compose with [`docker/docker-compose.yml`](/D:/agent开发项目/AI实习求职Agent系统/ai-worktrees/project-repair/docker/docker-compose.yml). This is the supported bundled stack for the current release workflow.

## Common Commands

```bash
make test
make test-unit
make test-integration
make test-e2e
make test-smoke
make test-release
```

Frontend:

```bash
cd frontend
npm run build
npm test
```

## Documentation

- Project rules: `AGENTS.md`
- Team workflow: `AGENT_TEAM.md`
- Long-term memory: `PROJECT_MEMORY.md`
- Stage plan: `.sisyphus/plans/PLAN.md`
- Decision log: `docs/decisions/README.md`
- Deployment guide: `docs/deployment.md`
- Demo walkthrough: `docs/demo-walkthrough.md`
