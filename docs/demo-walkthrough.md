# Demo Walkthrough

Use this script to present the repository as a real, runnable AI job-search product prototype instead of a loose set of backend endpoints.

## Demo Goals

This walkthrough should prove four things:

- the project boots locally without hidden manual steps
- the frontend and backend both run for real
- login and protected routes are connected
- Resume, Jobs, Interview, and Tracker form one connected product path

## Before the Demo

### 1. Prepare the environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
python scripts/migrate.py
python scripts/seed_demo.py
```

### 2. Start the backend

```bash
make run
```

Confirm:

- <http://127.0.0.1:8000/health>
- <http://127.0.0.1:8000/ready>

### 3. Start the frontend

```bash
cd frontend
npm run dev
```

Expected local URL:

- `http://127.0.0.1:4173`

If that port is busy, Vite will pick the next available port.

### 4. Demo account

- Username: `demo`
- Password: `demo123`

## Recommended Demo Order

### 1. Login

Open the login page and sign in with the demo account.

Call out:

- the frontend uses real bearer-token auth
- successful login calls `/api/v1/users/me`
- protected routes redirect back to the login page when the user is not authenticated

### 2. Dashboard

After login, open the dashboard and explain that it is a product workspace, not a fake summary page.

Call out:

- it combines existing Resume, Jobs, Interview, and Tracker results
- the latest AI output cards reflect saved records, not mocked screenshots
- the quick-start actions map to real product flows

### 3. Resume

Open the Resume page and show:

- resume content editing
- summary preview and save
- improvement preview and save
- summary history
- improvement history

Call out:

- the output is traceable over time instead of being a one-off response
- saved history feeds back into the dashboard view

### 4. Jobs

Open the Jobs page and show:

- job details
- selecting a resume for matching
- match preview
- saving a match
- match history

Call out:

- job matching depends on actual resume content
- saved match results flow back into the dashboard

### 5. Interview

Open the Interview page and walk through:

1. generate questions
2. save one generated question
3. write an answer
4. preview the evaluation
5. create a record
6. save the record evaluation

Call out:

- question generation and record persistence are separate steps
- the frontend now covers the full "generate -> save question -> create record" bridge

### 6. Tracker

Open the Tracker page and show:

- application records
- advice preview
- advice save
- advice history

Call out:

- tracker advice depends on the linked job, resume, and application state
- saved advice becomes a persistent history stream

### 7. Return to Dashboard

Go back to the dashboard and explain how the home view summarizes the latest results from all four product lanes.

## One-Pass Verification Flow

If you only need a quick confidence check before a demo:

1. `python scripts/migrate.py`
2. `python scripts/seed_demo.py`
3. `make run`
4. `cd frontend && npm run dev`
5. open the login page
6. sign in with `demo / demo123`
7. visit `/dashboard`
8. then open `/resume`, `/jobs`, `/interview`, and `/tracker`

## Suggested Closing Line

> This project is no longer just a backend endpoint collection. It is a runnable AI job-search product prototype with a real login flow, a connected frontend workspace, traceable AI history, and a layered backend architecture that supports end-to-end demos.

## Current Boundary

Be explicit about the current limits:

- the supported release-style path is Docker Compose
- this is not a production-ready Kubernetes stack
- refresh-token flows and worker orchestration are not fully finished
- the goal at this stage is a strong portfolio-grade product demo, not a fully hardened production system
