# Wave 6: Frontend Capability Completion

## Background

Wave 5 unified the frontend shell and product copy, but the main business pages still depended too heavily on manual entry. Wave 6 was used to close the remaining browser-side import and prefill loops without changing the backend contract.

## Stage Goal

Complete the highest-value frontend capability loops without changing backend contracts:

- let users choose local files in the browser where that removes repetitive manual entry
- reuse current API routes instead of inventing upload endpoints
- add user-facing import feedback and regression coverage for each completed loop

## Core Decisions

### D6.1 Keep Wave 6 frontend-first and contract-safe

All completed loops stay inside the current frontend and existing API contract. No backend upload route or persistence contract was added.

### D6.2 Standardize on text-friendly local import types

Wave 6 consistently accepts `txt`, `md`, and `json`, which keeps browser-side parsing simple and reliable across Resume, Jobs, Interview, and Tracker.

### D6.3 Treat import as a complete user loop, not only a file picker

Each completed page now includes import feedback, best-effort parsing, and regression coverage rather than stopping at a raw file input.

### D6.4 Finish the remaining high-value page gaps in one batch

This accelerated batch closed the last major page-level gap on Tracker instead of continuing with another small milestone round.

## Impact Scope

### Code

- `frontend/src/pages/resume-page.tsx`
- `frontend/src/pages/resume-page.test.tsx`
- `frontend/src/pages/jobs-page.tsx`
- `frontend/src/pages/jobs-page.test.tsx`
- `frontend/src/pages/interview-page.tsx`
- `frontend/src/pages/interview-page.test.tsx`
- `frontend/src/pages/tracker-page.tsx`
- `frontend/src/pages/tracker-page.test.tsx`

### Stage Docs

- `.sisyphus/plans/PLAN.md`
- `.sisyphus/plans/progress.md`
- `docs/decisions/README.md`
- `PROJECT_MEMORY.md`

## Verification Result

- `npm test -- src/pages/tracker-page.test.tsx`
  - passed
- `npm test`
  - passed
  - current frontend result: `7` files / `10` tests passed
- `npm run build`
  - passed

## Current Judgment

Wave 6 is now in progress with four real completed milestones:

- the Resume page no longer stops at manual editing only, and now owns a browser-side local import loop built on the current backend contract
- the Jobs page now also supports browser-side local import, prefilling job fields before creation without any backend upload expansion
- the Interview page now supports browser-side local context import so question generation can start from imported role context instead of manual paste only
- the Tracker page now supports browser-side local tracker-note import, notes-first parsing, and a multiline notes entry flow that better matches imported follow-up context

## Next Recommended Task

Decide whether to freeze Wave 6 as functionally complete or spend one final pass on consistency polish while preserving the same contract-safe boundary.
