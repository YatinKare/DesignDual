# Progress: backend-to-frontend-routes

Started: Sun Feb  8 06:22:02 EST 2026

## Status

IN_PROGRESS

## Analysis

### Current State Snapshot

The codebase is in a **backend-ready / frontend-partial** state for this integration plan.

Backend is already feature-complete for the documented route set:
- `GET /api/problems`
- `GET /api/problems/{id}`
- `POST /api/submissions` (multipart, required canvases, optional audio, `phase_times` JSON)
- `GET /api/submissions/{id}` (returns `SubmissionResultV2`)
- `GET /api/submissions/{id}/stream` (SSE with grading lifecycle)
- `GET /api/dashboard`
- `GET /api/dashboard/history`
- `GET /api/dashboard/summary`

Frontend currently contains:
- Minimal root page (`/`) placeholder.
- Static interview UI at `/screen1` (hardcoded problem content; no backend data wiring).
- Demo-heavy report UI at `/screen2` (has fetch by submission ID, but still primarily normalized from demo structure and not fully aligned to backend contract).
- No shared API client layer.
- No dedicated problems list/detail pages.
- No dashboard pages.

### Multi-Perspective Gap Analysis

#### Perspective 1: API Surface Coverage (Route-by-Route)

| Plan Requirement | Current State | Gap |
|---|---|---|
| Problems list (`GET /api/problems`) | Backend ready, frontend not wired | Build list UI + API call + states |
| Problem detail (`GET /api/problems/{id}`) | Backend ready, frontend not wired | Build detail UI + route + fetch |
| Submission create (`POST /api/submissions`) | Backend ready, frontend not wired | Build multipart form-data assembly from screen1 artifacts |
| Submission result (`GET /api/submissions/{id}`) | Backend ready, partially consumed by screen2 | Normalize payload robustly + error handling |
| Submission stream (`GET /api/submissions/{id}/stream`) | Backend ready, frontend not implemented | EventSource progress UI + terminal routing |
| Dashboard combined (`GET /api/dashboard`) | Backend ready, no frontend view | Build dashboard page + limit query support |
| Dashboard history (`GET /api/dashboard/history`) | Backend ready, no frontend view | Build standalone history view |
| Dashboard summary (`GET /api/dashboard/summary`) | Backend ready, no frontend view | Build standalone summary view |

#### Perspective 2: Frontend Architecture Readiness

Observed constraints in frontend project:
- No Vite proxy configured in `frontend/design-dual/vite.config.ts`, so `fetch('/api/...')` on frontend dev server will not automatically reach backend.
- No runtime base URL strategy (e.g., `PUBLIC_API_BASE_URL`) exists.
- API and UI concerns are currently mixed inside route files (especially `screen2`).

Required architectural direction:
- Create a shared API client module with base URL handling.
- Create endpoint-specific methods.
- Add a normalization/mapping layer between backend contract and UI render model.
- Keep route files focused on state + presentation.

#### Perspective 3: Contract Compatibility (Backend vs Current UI Assumptions)

Critical mismatches identified:
1. `radar`
- Backend: `radar` is an array of `{ skill, score, label }`.
- Current screen2 UI: assumes object keys like `radar.clarity`.

2. `next_attempt_plan`
- Backend: list of `{ what_went_wrong, do_next_time }`.
- Current screen2 UI: expects `{ fix, why, do_next_time[] }`.

3. `reference_outline.sections`
- Backend: section key is `section`.
- Current screen2 UI: expects `title`.

4. Optional/null fields
- Backend `evidence[].noticed` may be null.
- Current screen2 UI dereferences `noticed.strength` / `noticed.issue` without full null guards.

5. Transcript fields
- Backend includes `highlights` list.
- Current UI expects `transcript_highlights` and `full_transcript` arrays (demo-specific).

#### Perspective 4: Runtime/Operational Risks

- `GET /api/submissions/{id}` can return 404 while grading is still in progress. UI must treat this as transitional during active stream.
- SSE terminal `complete` may include `result`; if result injection fails, frontend needs fallback fetch via `GET /api/submissions/{id}`.
- Dashboard summary can be empty (`total_submissions=0`, `average_score=null`) and must render cleanly.
- Artifact URLs are returned as `/uploads/...`; if uploads are not served in runtime, image rendering may fail. UI must degrade gracefully (fallback placeholder + no crash).

### What Already Exists (Confirmed)

Backend:
- Route handlers and service methods for all required endpoints.
- Consistent error envelope with `detail` messages.
- SSE event generation and replay persistence.
- Seed problems and sample artifacts in `backend/temp` for manual testing.

Frontend:
- Existing interview and report visual structures can be reused.
- `screen2` already has a payload normalization entry point that can be upgraded rather than rewritten from scratch.

### What Is Missing (Confirmed)

- Shared API integration layer in frontend.
- Problems list/detail user flow.
- End-to-end submission pipeline from `/screen1` (artifacts -> multipart -> stream -> final result).
- Live SSE progress UI.
- Dashboard views.
- Robust error and empty-state handling across all integrated pages.

### Dependency Strategy

Build should follow this order:
1. API client + error parsing + contract mapping (foundation).
2. Problem browsing pages (entry point to interview flow).
3. Screen1 submission data pipeline (capture, validate, submit).
4. SSE progress handling and completion routing.
5. Screen2 robust rendering against real payload.
6. Dashboard pages.
7. Manual E2E verification against acceptance criteria.

### API Contract Source of Truth (Critical Rule)

- Backend schemas and backend route response models are the sole source of truth for API contracts.
- Frontend must conform to backend contracts; frontend demo/sample shapes must never redefine API semantics.
- Any frontend mapping/normalization must be explicit compatibility adaptation from backend contract -> UI view model.
- If frontend expectations conflict with backend schema, update frontend types/components/mappers (not backend assumptions in this plan).
- During build, verify API payload fields against backend models/docs before implementing or changing frontend API code.

### Acceptance-Criteria Mapping

- Load problems list + open detail page: covered by Tasks 2.1-2.6.
- Submit solution with required canvases + show live SSE progress + render final result: covered by Tasks 3.1-4.8 + 5.1-5.7.
- Dashboard summary/history display correctly: covered by Tasks 6.1-6.5.
- Error states are clear and non-crashing: covered by Tasks 1.3, 3.6, 4.5, 5.6-5.8, 6.4, 8.7.

## Task List

### Phase 0: Planning Baseline (Completed)
- [x] 0.1: Read `backend-to-frontend-routes.md` and extract all route-level requirements.
- [x] 0.2: Verify progress-file state (file absent) and create planning file scaffold.
- [x] 0.3: Audit backend route/service/model contracts for required endpoints.
- [x] 0.4: Audit frontend route structure and identify existing integration points.
- [x] 0.5: Identify contract mismatches and runtime contingencies to shape build order.

### Phase 1: Frontend API Foundation
- [ ] 1.1: Add runtime API base URL configuration (`PUBLIC_API_BASE_URL`, default `http://localhost:8000`).
- [ ] 1.2: Create shared JSON request helper (method, headers, query serialization, non-2xx handling).
- [ ] 1.3: Create shared error parser for backend `{ detail }` responses with user-friendly fallback messages.
- [ ] 1.4: Create multipart submission builder utility (`problem_id`, four canvases, optional audio, `phase_times`).
- [ ] 1.5: Create SSE client helper with lifecycle callbacks and cleanup semantics.
- [ ] 1.6: Implement typed endpoint methods for problems, submissions, and dashboard.
- [ ] 1.7: Define/derive frontend API types directly from backend schemas/contracts and use them as integration contracts.

### Phase 2: Problem Browsing Flow
- [ ] 2.1: Create problems list page wired to `GET /api/problems`.
- [ ] 2.2: Add loading, empty, and error UI states for problems list.
- [ ] 2.3: Create problem detail page wired to `GET /api/problems/{id}`.
- [ ] 2.4: Render full problem detail contract safely (constraints, hints, phase time map, rubric definition).
- [ ] 2.5: Add entry action from list/detail to begin interview for selected problem.
- [ ] 2.6: Ensure routing preserves selected `problem_id` into screen1 flow.

### Phase 3: Screen1 Submission Pipeline
- [ ] 3.1: Replace hardcoded screen1 problem content with fetched backend problem details.
- [ ] 3.2: Implement per-phase timer accounting to produce valid `phase_times` payload.
- [ ] 3.3: Implement capture/export of four required canvas PNG artifacts.
- [ ] 3.4: Implement optional per-phase audio attachment/recording state.
- [ ] 3.5: Implement pre-submit validation for required canvases and phase-time completeness.
- [ ] 3.6: Submit multipart request to `POST /api/submissions` and capture returned `submission_id`.
- [ ] 3.7: Add submit-in-flight state and user feedback for upload failures.
- [ ] 3.8: Persist enough client state to recover or retry after transient failures.

### Phase 4: Real-Time Grading Stream
- [ ] 4.1: Start SSE stream using `submission_id` via `GET /api/submissions/{id}/stream`.
- [ ] 4.2: Map stream statuses (`queued`, `processing`, phase statuses, `synthesizing`, `complete`, `failed`) to UI progress.
- [ ] 4.3: Handle terminal `complete` with inline `result` payload when present.
- [ ] 4.4: Add terminal fallback: if `complete` arrives without usable `result`, fetch `GET /api/submissions/{id}`.
- [ ] 4.5: Handle `failed` stream status with clear retry/recover options.
- [ ] 4.6: Handle disconnect/timeout without duplicate terminal transitions.
- [ ] 4.7: Route to `/screen2` with `submission_id` after successful completion.
- [ ] 4.8: Prevent race conditions between stream completion and result-page fetch.

### Phase 5: Screen2 Contract Alignment and Resilience
- [ ] 5.1: Move payload normalization into a dedicated mapper module shared by screen2 loaders/components.
- [ ] 5.2: Map backend `radar[]` into UI rendering model expected by existing radar canvas logic.
- [ ] 5.3: Map backend `next_attempt_plan` into UI cards with graceful fallback copy.
- [ ] 5.4: Map backend `reference_outline.sections[].section` into display title field.
- [ ] 5.5: Map backend `highlights` into transcript highlight UI, with fallback when detailed transcript is absent.
- [ ] 5.6: Add null-safe handling for optional `noticed`, `transcripts`, and missing evidence fields.
- [ ] 5.7: Add robust error state for result fetch failure (not found, still processing, network errors).
- [ ] 5.8: Add image fallback behavior when `/uploads/...` assets fail to load.

### Phase 6: Dashboard Views
- [ ] 6.1: Build dashboard overview page consuming `GET /api/dashboard`.
- [ ] 6.2: Implement optional `limit` query behavior in overview page controls.
- [ ] 6.3: Build standalone history page consuming `GET /api/dashboard/history`.
- [ ] 6.4: Build standalone summary page consuming `GET /api/dashboard/summary`.
- [ ] 6.5: Add empty-state rendering for first-time users (no completed submissions).

### Phase 7: Navigation and Route Cohesion
- [ ] 7.1: Add top-level navigation among Problems, Interview, Results, Dashboard.
- [ ] 7.2: Ensure root route points users to actionable entry path (not placeholder-only).
- [ ] 7.3: Preserve direct-link compatibility for `/screen1` and `/screen2` query-based access.

### Phase 8: Manual End-to-End Validation (No Unit Tests)
- [ ] 8.1: Verify local backend/frontend startup assumptions (`uv` backend, `bun` frontend) and CORS path.
- [ ] 8.2: Manually validate problems list and detail retrieval.
- [ ] 8.3: Manually validate submission with required canvas files and optional audio.
- [ ] 8.4: Manually validate SSE progress lifecycle from submit to terminal status.
- [ ] 8.5: Manually validate final result rendering on `/screen2` with real backend payload.
- [ ] 8.6: Manually validate dashboard overview/history/summary views with sample data.
- [ ] 8.7: Manually validate key failure paths (bad problem id, missing canvas, network interruption, stream failure).
- [ ] 8.8: Record any residual gaps and implementation follow-ups directly in this progress file.
- [ ] 8.9: Contract conformance check: verify all frontend API calls/mappers against backend schema fields (no frontend-invented API fields).

### Task Dependencies

```text
Phase 0 (Completed planning baseline)
  -> Phase 1 (API foundation)
      -> Phase 2 (problems browse)
      -> Phase 3 (screen1 submit pipeline)
          -> Phase 4 (SSE live grading)
              -> Phase 5 (screen2 contract-safe rendering)
                  -> Phase 6 (dashboard views)
                      -> Phase 7 (navigation cohesion)
                          -> Phase 8 (manual E2E validation)
```

Critical path:
- 1 -> 3 -> 4 -> 5 -> 8

Parallelizable lanes after Phase 1:
- Lane A: Phase 2 (problems browsing)
- Lane B: Phase 6 (dashboard pages)

## Notes

- Planning-only pass complete; no implementation code changes were made.
- This file intentionally stays at `IN_PROGRESS` to signal build mode readiness.
- Do not write `RALPH_DONE` in planning mode.
- Skill note: available skills in this session (`skill-creator`, `skill-installer`) are not applicable to this route-integration planning task, so direct repository analysis was used.

## Status
IN_PROGRESS

## Task List
### Phase 0: Planning Baseline (Completed)
- [x] 0.1: Read `backend-to-frontend-routes.md` and extract all route-level requirements.
- [x] 0.2: Verify progress-file state (file absent) and create planning file scaffold.
- [x] 0.3: Audit backend route/service/model contracts for required endpoints.
- [x] 0.4: Audit frontend route structure and identify existing integration points.
- [x] 0.5: Identify contract mismatches and runtime contingencies to shape build order.

### Phase 1: Frontend API Foundation
- [x] 1.1: Add runtime API base URL configuration (`PUBLIC_API_BASE_URL`, default `http://localhost:8000`).
- [ ] 1.2: Create shared JSON request helper (method, headers, query serialization, non-2xx handling).
- [ ] 1.3: Create shared error parser for backend `{ detail }` responses with user-friendly fallback messages.
- [ ] 1.4: Create multipart submission builder utility (`problem_id`, four canvases, optional audio, `phase_times`).
- [ ] 1.5: Create SSE client helper with lifecycle callbacks and cleanup semantics.
- [ ] 1.6: Implement typed endpoint methods for problems, submissions, and dashboard.
- [ ] 1.7: Define/derive frontend API types directly from backend schemas/contracts and use them as integration contracts.

### Phase 2: Problem Browsing Flow
- [ ] 2.1: Create problems list page wired to `GET /api/problems`.
- [ ] 2.2: Add loading, empty, and error UI states for problems list.
- [ ] 2.3: Create problem detail page wired to `GET /api/problems/{id}`.
- [ ] 2.4: Render full problem detail contract safely (constraints, hints, phase time map, rubric definition).
- [ ] 2.5: Add entry action from list/detail to begin interview for selected problem.
- [ ] 2.6: Ensure routing preserves selected `problem_id` into screen1 flow.

### Phase 3: Screen1 Submission Pipeline
- [ ] 3.1: Replace hardcoded screen1 problem content with fetched backend problem details.
- [ ] 3.2: Implement per-phase timer accounting to produce valid `phase_times` payload.
- [ ] 3.3: Implement capture/export of four required canvas PNG artifacts.
- [ ] 3.4: Implement optional per-phase audio attachment/recording state.
- [ ] 3.5: Implement pre-submit validation for required canvases and phase-time completeness.
- [ ] 3.6: Submit multipart request to `POST /api/submissions` and capture returned `submission_id`.
- [ ] 3.7: Add submit-in-flight state and user feedback for upload failures.
- [ ] 3.8: Persist enough client state to recover or retry after transient failures.

### Phase 4: Real-Time Grading Stream
- [ ] 4.1: Start SSE stream using `submission_id` via `GET /api/submissions/{id}/stream`.
- [ ] 4.2: Map stream statuses (`queued`, `processing`, phase statuses, `synthesizing`, `complete`, `failed`) to UI progress.
- [ ] 4.3: Handle terminal `complete` with inline `result` payload when present.
- [ ] 4.4: Add terminal fallback: if `complete` arrives without usable `result`, fetch `GET /api/submissions/{id}`.
- [ ] 4.5: Handle `failed` stream status with clear retry/recover options.
- [ ] 4.6: Handle disconnect/timeout without duplicate terminal transitions.
- [ ] 4.7: Route to `/screen2` with `submission_id` after successful completion.
- [ ] 4.8: Prevent race conditions between stream completion and result-page fetch.

### Phase 5: Screen2 Contract Alignment and Resilience
- [ ] 5.1: Move payload normalization into a dedicated mapper module shared by screen2 loaders/components.
- [ ] 5.2: Map backend `radar[]` into UI rendering model expected by existing radar canvas logic.
- [ ] 5.3: Map backend `next_attempt_plan` into UI cards with graceful fallback copy.
- [ ] 5.4: Map backend `reference_outline.sections[].section` into display title field.
- [ ] 5.5: Map backend `highlights` into transcript highlight UI, with fallback when detailed transcript is absent.
- [ ] 5.6: Add null-safe handling for optional `noticed`, `transcripts`, and missing evidence fields.
- [ ] 5.7: Add robust error state for result fetch failure (not found, still processing, network errors).
- [ ] 5.8: Add image fallback behavior when `/uploads/...` assets fail to load.

### Phase 6: Dashboard Views
- [ ] 6.1: Build dashboard overview page consuming `GET /api/dashboard`.
- [ ] 6.2: Implement optional `limit` query behavior in overview page controls.
- [ ] 6.3: Build standalone history page consuming `GET /api/dashboard/history`.
- [ ] 6.4: Build standalone summary page consuming `GET /api/dashboard/summary`.
- [ ] 6.5: Add empty-state rendering for first-time users (no completed submissions).

### Phase 7: Navigation and Route Cohesion
- [ ] 7.1: Add top-level navigation among Problems, Interview, Results, Dashboard.
- [ ] 7.2: Ensure root route points users to actionable entry path (not placeholder-only).
- [ ] 7.3: Preserve direct-link compatibility for `/screen1` and `/screen2` query-based access.

### Phase 8: Manual End-to-End Validation (No Unit Tests)
- [ ] 8.1: Verify local backend/frontend startup assumptions (`uv` backend, `bun` frontend) and CORS path.
- [ ] 8.2: Manually validate problems list and detail retrieval.
- [ ] 8.3: Manually validate submission with required canvas files and optional audio.
- [ ] 8.4: Manually validate SSE progress lifecycle from submit to terminal status.
- [ ] 8.5: Manually validate final result rendering on `/screen2` with real backend payload.
- [ ] 8.6: Manually validate dashboard overview/history/summary views with sample data.
- [ ] 8.7: Manually validate key failure paths (bad problem id, missing canvas, network interruption, stream failure).
- [ ] 8.8: Record any residual gaps and implementation follow-ups directly in this progress file.
- [ ] 8.9: Contract conformance check: verify all frontend API calls/mappers against backend schema fields (no frontend-invented API fields).

## Completed This Iteration
- 1.1: Added a runtime API base URL config module with `PUBLIC_API_BASE_URL` fallback to `http://localhost:8000`.

## Notes
- `bun run check` failed due to missing `react`, `react-dom/client`, and `@excalidraw/excalidraw` type resolution in `src/lib/Excalidraw.svelte`.
