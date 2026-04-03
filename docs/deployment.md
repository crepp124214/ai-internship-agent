# Deployment Guide

This project currently supports one official release-style deployment path:

- Docker Compose via [`docker/docker-compose.yml`](/D:/agent开发项目/AI实习求职Agent系统/ai-worktrees/project-repair/docker/docker-compose.yml)

The repository still contains Kubernetes-related assets, but they are not the maintained release path for the current stage. For now, "deployable" means the Compose stack can boot, pass health checks, and run the documented smoke and release flows.

## Prerequisites

- Docker
- Docker Compose v2
- A prepared `.env` file in the repository root

Start from the local template:

```bash
cp .env.example .env
```

Check these values before running a release-style stack:

- `SECRET_KEY`
- `LLM_PROVIDER`
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `CORS_ORIGINS`

`docker-compose.yml` overrides the database and Redis addresses so the app points at the internal Compose services.

## Production CORS Example

Before deploying to a real environment, replace `CORS_ORIGINS` with the actual frontend origin:

```bash
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

The default values only allow local development hosts such as `localhost:3000` and `localhost:4173`.

Other production-minded settings:

- `SECRET_KEY` should be a strong random value
- `APP_DEBUG=false`
- `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` should match expected traffic

## Start the Stack

```bash
docker compose -f docker/docker-compose.yml up --build
```

Or:

```bash
make compose-up
```

Services in the stack:

- `postgres`
- `redis`
- `app`

## Health and Readiness

After the stack starts, check:

- `GET /health`
- `GET /ready`

Example:

```bash
curl http://localhost:8000/ready
```

The stack is only considered ready when `/ready` returns `200`.

## Migrations

For local or CI-style execution:

```bash
python scripts/migrate.py
```

For Compose-based execution, run the same migration step before release or through an operational step using the app image. The repository does not yet define a dedicated migration job container.

## Stop the Stack

```bash
docker compose -f docker/docker-compose.yml down
```

Or:

```bash
make compose-down
```

## Release Boundary

Today, "release ready" means:

- the app boots from documented environment files
- Compose starts `postgres`, `redis`, and `app`
- `/health` and `/ready` respond correctly
- smoke and release verification commands pass

It does not mean:

- Kubernetes deployment is production ready
- refresh-token or session management is fully complete
- external secret management is fully integrated
- worker orchestration and async background hardening are finished
