# Integration: Backend Routes To Frontend

## Goal
Integrate the documented backend API routes into the frontend so users can browse problems, submit interviews, and view grading results with live progress updates.

## Requirements
- Implement API client utilities for `http://localhost:8000` with JSON defaults and `multipart/form-data` support for submissions.
- Wire UI flows to the following routes:
- `GET /api/problems` list and render problems.
- `GET /api/problems/{id}` fetch and render problem details.
- `POST /api/submissions` upload canvases, optional audio, and `phase_times` as JSON in `multipart/form-data`.
- `GET /api/submissions/{id}` fetch and render grading results (SubmissionResultV2).
- `GET /api/submissions/{id}/stream` consume SSE events and update progress UI in real time.
- `GET /api/dashboard` display summary + recent history; add optional `limit` query.
- `GET /api/dashboard/history` and `GET /api/dashboard/summary` supported as standalone views.
- Handle error responses with `{ "detail": "..." }` and display user-friendly messages.
- Manual end-to-end testing only. Do not add unit tests.
- Acceptance criteria:
- A user can load the problems list and open a problem detail page.
- A user can submit a solution with required canvas files; the UI shows progress via SSE; final results render when complete.
- Dashboard summary and history display correctly with sample data.
- Error states show clear messages and do not crash the UI.

## Context
- API documentation: `backend/docs/API.md`.
- Backend uses `uv` for running the server.
- Frontend uses `bun` for dev/build/test scripts.
- For AI UI development, use the `daisyui-mcp`.
- For AI Svelte development, use the Svelte autochecker (`mcp__svelte__svelte-autofixer`).
- There is sample data in `backend/temp` for manual testing.
- Base URL: `http://localhost:8000` with CORS origin `http://localhost:5173`.
