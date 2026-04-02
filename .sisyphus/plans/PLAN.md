# AI Internship Agent Stage Plan

> SSOT: this file is the stage-level source of truth for active delivery status.

## 1. Top-Level Goal

Build an AI-assisted internship job-search system with a stable backend, a demo-ready frontend workspace, and shared provider/runtime infrastructure that can evolve without breaking layered boundaries.

The product scope continues to center on:

- resume management, summary, and improvement
- job intake and matching
- interview preparation and evaluation
- application tracking and advice
- multi-agent collaboration built on shared core infrastructure

## 2. Stage Overview

### Wave 1: Foundation

- Status: completed
- Goal: establish the three-layer backend structure, auth baseline, migration path, and test skeleton

### Wave 2: Core MVP

- Status: completed
- Goal: deliver the main backend domain loops for Resume, Job, Interview, and Tracker

### Wave 3: Observability & Resilience

- Status: completed
- Goal: land tracing, rate limiting, circuit breaker behavior, and baseline runtime hardening

### Wave 4: Public API & Demo Baseline

- Status: completed
- Goal: stabilize public API docs, E2E demo flow, and baseline frontend/backend integration

### Wave 5: Frontend Productization

- Status: completed
- Goal:
  - unify the six core frontend pages into one product narrative
  - remove garbled copy from the main workspace flow
  - preserve the existing backend contract
  - add minimal smoke coverage for the frontend shell

### Wave 6: Frontend Capability Completion

- Status: in progress
- Goal:
  - complete deeper frontend capability loops on top of the Wave 5 product shell
  - prioritize richer form handling, error states, and resume workflow completion without inventing new backend contracts
- Current milestone completed:
  - `Resume lead` delivered a browser-side local resume import loop
  - supported local import types: `txt`, `md`, `json`
  - the frontend now reads a local file, creates the resume through the current API, then writes imported content back through the existing update route
  - resume-page regression coverage now includes the import-create-writeback path
  - `Resume lead` also delivered a browser-side local job description import loop on the Jobs page
  - markdown/text imports now prefill job title and description
  - JSON imports can prefill `title`, `company`, `location`, `description`, and `requirements` when those fields exist
  - jobs-page regression coverage now includes the import-prefill-create path
  - `Resume lead` also delivered a browser-side local interview-context import loop on the Interview page
  - local `txt`, `md`, and `json` files can now prefill `job_context`
  - JSON imports use heuristic extraction for common context fields such as `job_context`, `description`, `title`, and related metadata
  - interview-page regression coverage now includes the import-context-generate path
  - `Resume lead` also delivered a browser-side local tracker-note import loop on the Tracker page
  - local `txt`, `md`, and `json` files can now prefill tracker `job_id`, `resume_id`, `status`, and `notes`
  - freeform text imports fall back to notes-first parsing with simple field extraction when present
  - the tracker notes field now uses a multiline input better suited for imported context and manual follow-up notes
  - tracker-page regression coverage now includes the import-prefill-create path
- Remaining scope:
  - treat the remaining Wave 6 work as polish and consistency follow-up, not another major capability gap
  - keep the work frontend-first and contract-safe

### Wave 7: Real LLM Provider Integration

- Status: in progress
- Goal:
  - strengthen the shared real-provider runtime while preserving mock-first local development
  - keep provider/runtime ownership inside `src/core/llm`
- Current milestone completed:
  - `LLM/Core lead` stabilized provider/runtime resolution for the OpenAI path
  - `OpenAIAdapter` now resolves `api_key`, `model`, and `base_url` with a consistent precedence: top-level config -> nested `llm` config -> environment fallback
  - blank-string config values are treated as unset
  - unit coverage now locks provider precedence and runtime fallback behavior
  - `LLM/Core lead` also taught `LLMFactory` to resolve the default provider from environment/settings when caller config is otherwise silent
  - provider precedence is now locked as: explicit provider -> top-level config -> nested `llm.provider` -> `LLM_PROVIDER` env -> `Settings.LLM_PROVIDER` -> mock
  - `LLM/Core lead` also unified OpenAI runtime parsing for `temperature`, `max_tokens`, `timeout`, and `max_retries`
  - numeric strings are now safely coerced, blank strings are ignored, and `generate` / `chat` honor instance defaults when callers do not override them
  - `LLM/Core lead` also closed the remaining mixed-config runtime gap for OpenAI numeric options
  - invalid top-level numeric config values now fall through to nested `llm` config or environment values instead of forcing defaults too early
  - blank provider strings no longer block nested provider resolution or settings-based fallback in `LLMFactory`
- Remaining scope:
  - keep widening provider-facing verification only where a real deployment/runtime path requires it
  - avoid expanding provider breadth until a concrete non-mock deployment path needs it

### Wave 8: Stabilization & Scale

- Status: not started
- Goal:
  - tighten regression confidence, deployment readiness, and operational stability
  - deepen runbooks and release readiness once Wave 6 and Wave 7 converge

## 3. Milestones

| Milestone | Status | Notes |
| --- | --- | --- |
| M1: Backend foundation usable | completed | FastAPI, auth baseline, migrations, and tests are established |
| M2: Four domain loops demoable | completed | Resume, Job, Interview, and Tracker backend flows are usable |
| M3: Demo chain automated | completed | E2E demo path is part of project verification |
| M4: Frontend product shell unified | completed | Wave 5 unified the frontend shell and core product copy |
| M5: Frontend capability deepening | in progress | Wave 6 now covers resume, jobs, interview, and tracker local import loops |
| M6: Real provider runtime baseline | in progress | Wave 7 now covers provider precedence plus mixed config/env/settings runtime validation |
| M7: Stabilization and scale | not started | Final hardening stage remains after Wave 6 and Wave 7 |

## 4. Current Risks

| Risk | Current Judgment | Mitigation |
| --- | --- | --- |
| Frontend loops are more even, but final consistency polish remains | low | Treat remaining Wave 6 work as UX/test consistency follow-up rather than missing core loops |
| Real provider integration is still OpenAI-path only | medium | Continue Wave 7 within `src/core/llm` and preserve mock-first local behavior |
| Historical docs still contain encoding noise | medium | Keep updating the highest-value stage docs as active work continues |

## 5. Next Recommended Task

1. Decide whether to close `Wave 6` with a final consistency/polish pass or freeze it as functionally complete.
2. Continue `Wave 7: Real LLM Provider Integration` with the next deployment-driven verification step that still preserves existing agent fallback behavior.
3. Keep stage-level plan, progress, decision, and memory files synchronized for both active parallel tracks.
