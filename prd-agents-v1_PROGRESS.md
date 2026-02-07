# Progress: prd-agents-v1

Started: Sat Feb  7 08:48:59 EST 2026

## Status

IN_PROGRESS

## Analysis

### Current State
The DesignDual project is at a **minimal skeleton state**:
- ✅ Project directories created (backend/, frontend/)
- ✅ Frontend framework configured (SvelteKit + Tailwind + TypeScript)
- ✅ Basic pyproject.toml exists (Python 3.13 specified)
- ❌ **NO Python code written yet** - completely empty backend
- ❌ **NO dependencies installed** - pyproject.toml has empty dependencies array
- ❌ **NO database schema** - no SQLite files or models
- ❌ **NO API routes** - no FastAPI app
- ❌ **NO ADK integration** - no agent code
- ❌ **NO data models** - no Pydantic schemas

### What Needs to Be Built

According to the PRD (prd-agents-v1.md + prd-v1.md), we need to implement:

**1. Backend Core (FastAPI + Database)**
- FastAPI application with 6 API endpoints
- SQLite database with 3 tables (problems, submissions, grading_results)
- Pydantic models for all data structures
- File upload handling (multipart/form-data for PNGs + webm audio)
- Environment configuration (.env for Gemini API key)

**2. Google ADK Multi-Agent System**
- 5 specialized agents using Gemini 2.5 Flash:
  1. **ScopingAgent** - Evaluates phases 1-2 (clarify + estimate)
  2. **DesignAgent** - Evaluates phase 3 (architecture design)
  3. **ScaleAgent** - Cross-cutting: bottleneck analysis across all phases
  4. **TradeoffAgent** - Evaluates phases 3-4 (tradeoff reasoning)
  5. **SynthesisAgent** - Combines all agent outputs into final report
- Agent orchestration using ADK's `SequentialAgent` + `ParallelAgent`
- Session state management for agent communication

**3. Audio Transcription Pipeline**
- Gemini API integration for audio-to-text (parallel transcription of up to 4 audio files)
- Base64 encoding for canvas PNGs
- Submission bundle assembly

**4. Server-Sent Events (SSE) Streaming**
- Real-time progress updates during grading
- Status transitions: started → scoping → design → scale → tradeoff → synthesizing → complete
- Themed messages for magic narrative

**5. Seed Data**
- 6 system design problems (URL Shortener, Rate Limiter, Spotify, Chat, YouTube, Google Docs)
- Problem metadata: prompt, difficulty, focus tags, rubric hints, time allocation

### Key Architecture Decisions from PRD

1. **Model Choice**: `gemini-2.5-flash` everywhere (fast, multimodal, cost-effective)
2. **Integration Pattern**: Wrap ADK's Runner in FastAPI (don't use ADK's built-in server)
3. **State Management**: Agents write to `output_key`, synthesis reads from ADK session state
4. **Database**: SQLite with `aiosqlite` for async operations
5. **Audio Handling**: Gemini API handles transcription natively (stay in one ecosystem)
6. **File Storage**: Save uploaded files to disk/memory temporarily for processing
7. **Docs**: Use the `google-adk` mcp server to get best practices, examples and should be used for everything.

### Developer notes:
- Before beginning a task, read the task, read the documentation via the docs mcp.
- **ONLY USE `UV` NO RAW PYTHON COMMANDS NEVER EVER RUN JUST PYTHON3 ...EVERYTHING NEEDS TO BE MANAGED VIA UV**.
- Architecture rule: routes delegate all business/data logic to services (routes stay thin).

### Dependencies Required

Based on the PRD, the backend needs:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `google-genai` or `google-adk-python` - Google ADK SDK for multi-agent orchestration
- `aiosqlite` - Async SQLite driver
- `pydantic` - Data validation and schemas
- `python-multipart` - File upload support
- `sse-starlette` - Server-Sent Events for FastAPI
- `python-dotenv` - Environment variable management

### Critical Integration Points

1. **Multipart Form Upload Flow**:
   ```
   POST /api/submissions
   ├── Receive 4 canvas PNGs + 4 optional audio webm files
   ├── Save files temporarily
   ├── Transcribe audio files in parallel via Gemini API
   ├── Create submission record in SQLite
   ├── Return submission_id immediately
   └── Trigger background grading task
   ```

2. **ADK Session State Shape** (as defined in PRD):
   ```json
   {
     "problem": {...},           // Input: problem details + rubric
     "phases": [...],            // Input: 4 phase snapshots + transcripts
     "phase_times": {...},       // Input: timing data
     "scoping_result": {...},    // Output: ScopingAgent result
     "design_result": {...},     // Output: DesignAgent result
     "scale_result": {...},      // Output: ScaleAgent result
     "tradeoff_result": {...},   // Output: TradeoffAgent result
     "final_report": {...}       // Output: SynthesisAgent final grading
   }
   ```

3. **SSE Event Sequence**:
   ```
   Event 1: { status: "started", message: "Your spell has been submitted..." }
   Event 2: { status: "scoping", message: "The Scoping Oracle examines..." }
   Event 3: { status: "design", message: "The Architecture Archmage studies..." }
   Event 4: { status: "scale", message: "The Scale Sorcerer tests..." }
   Event 5: { status: "tradeoff", message: "The Wisdom Keeper weighs..." }
   Event 6: { status: "synthesizing", message: "The Council deliberates..." }
   Event 7: { status: "complete", message: "The verdict is ready.", result: {...} }
   ```

### Risks & Contingencies

1. **ADK SDK Documentation**: If Google ADK Python SDK is poorly documented or unstable:
   - **Contingency**: Use Google Generative AI SDK directly with manual orchestration
   - **Tradeoff**: Lose automatic parallel execution, but gain more control

2. **Gemini Audio Transcription**: If Gemini API doesn't support direct webm audio:
   - **Contingency**: Use `ffmpeg` to convert webm → wav, or use OpenAI Whisper API
   - **Tradeoff**: Adds dependency, but ensures transcription works

3. **File Storage**: Uploaded files need temporary storage during processing:
   - **Approach**: Save to `/tmp` or a dedicated `uploads/` directory
   - **Cleanup**: Delete files after grading completes to save space

4. **Background Task Processing**: Grading can take 30+ seconds:
   - **Approach**: Use FastAPI `BackgroundTasks` for async processing
   - **Alternative**: Use Celery if BackgroundTasks proves insufficient

5. **Agent Prompt Engineering**: Agent outputs must be structured JSON:
   - **Approach**: Use Gemini's `response_mime_type="application/json"` parameter
   - **Validation**: Parse and validate all agent outputs with Pydantic schemas

## Task List

### Phase 1: Backend Foundation (Dependencies + Database + Basic Routes)
- [x] 1.1: Update pyproject.toml with all required dependencies
- [x] 1.2: Create .env.example file for configuration template
- [x] 1.3: Create backend/app/ directory structure (models/, routes/, services/, agents/)
- [x] 1.4: Define Pydantic schemas (Problem, Submission, GradingReport, DimensionScore)
- [x] 1.5: Create SQLite database schema and initialization script
- [x] 1.6: Create main.py FastAPI application with CORS middleware
- [x] 1.7: Implement GET /api/problems endpoint (list all problems)
- [x] 1.8: Implement GET /api/problems/{id} endpoint (problem details)
- [x] 1.9: Create seed data for 6 system design problems
- [ ] 1.10: Test basic routes work (can fetch problems)

### Phase 2: File Upload & Storage (Submission Creation)
- [ ] 2.1: Implement POST /api/submissions endpoint with multipart form-data handling
- [ ] 2.2: Create file storage service (save uploaded PNGs and webm files)
- [ ] 2.3: Implement submission record creation in SQLite
- [ ] 2.4: Add file validation (check file types, size limits)
- [ ] 2.5: Return submission_id immediately upon upload
- [ ] 2.6: Test file upload flow end-to-end by making a temp file, doing a curl, deleting temp file.

### Phase 3: Audio Transcription (Gemini API Integration)
- [ ] 3.1: Research Gemini API audio transcription capabilities
- [ ] 3.2: Create transcription service using Gemini API
- [ ] 3.3: Implement parallel transcription of up to 4 audio files
- [ ] 3.4: Handle null/missing audio files gracefully
- [ ] 3.5: Store transcripts in submission record
- [ ] 3.6: Test transcription with sample audio files, doing a curl, deleting audio files.

### Phase 4: Google ADK Multi-Agent Setup (Core Orchestration)
- [ ] 4.1: Research Google ADK Python SDK installation and basic usage from the google-adk mcp.
- [ ] 4.2: Create agents/ directory with base agent structure
- [ ] 4.3: Implement ScopingAgent prompt and logic (evaluates phases 1-2)
- [ ] 4.4: Implement DesignAgent prompt and logic (evaluates phase 3)
- [ ] 4.5: Implement ScaleAgent prompt and logic (cross-cutting evaluation)
- [ ] 4.6: Implement TradeoffAgent prompt and logic (evaluates phases 3-4)
- [ ] 4.7: Implement SynthesisAgent prompt and logic (combines all outputs)
- [ ] 4.8: Create ADK orchestration with SequentialAgent + ParallelAgent
- [ ] 4.9: Test individual agents with sample inputs
- [ ] 4.11: Test full agent pipeline with mock submission data, doing a curl, and keep mock submission data in that temp folder for later testing.

### Phase 5: Grading Pipeline Integration (Backend Processing)
- [ ] 5.1: Create grading service that assembles submission bundle
- [ ] 5.2: Implement ADK session state initialization from submission data
- [ ] 5.3: Create background task for running grading pipeline
- [ ] 5.4: Store grading results in database (grading_results table)
- [ ] 5.5: Implement error handling for agent failures
- [ ] 5.6: Test full grading pipeline with real submission via curl.

### Phase 6: Server-Sent Events (Real-time Progress Streaming)
- [ ] 6.1: Install and configure sse-starlette for FastAPI
- [ ] 6.2: Implement GET /api/submissions/{id}/stream SSE endpoint
- [ ] 6.3: Create event generator that yields grading progress updates
- [ ] 6.4: Emit themed status messages (magic narrative)
- [ ] 6.5: Emit final result when grading completes
- [ ] 6.6: Test SSE connection and event streaming

### Phase 7: Results Retrieval & Dashboard (Read Endpoints)
- [ ] 7.1: Implement GET /api/submissions/{id} endpoint (fetch grading result)
- [ ] 7.2: Implement GET /api/dashboard endpoint (user score history - stretch goal)
- [ ] 7.3: Test results retrieval
- [ ] 7.4: Add proper error handling for not-found cases

### Phase 8: Frontend Integration Points (Backend Ready for Frontend)
- [ ] 8.1: Document all API endpoints with example requests/responses
- [ ] 8.2: Test CORS configuration for frontend connection
- [ ] 8.3: Verify file upload size limits are appropriate
- [ ] 8.4: Create Postman/Thunder Client collection for testing
- [ ] 8.5: End-to-end test: upload submission → stream progress → fetch result via curl.

### Phase 9: Error Handling & Robustness
- [ ] 9.1: Add comprehensive error handling to all routes
- [ ] 9.2: Add logging for debugging (use Python logging module)
- [ ] 9.3: Handle edge cases (missing files, invalid data, API failures)
- [ ] 9.4: Add request validation with Pydantic
- [ ] 9.5: Test failure scenarios (invalid problem_id, corrupt files, etc.)

### Phase 10: Deployment Preparation
- [ ] 10.1: Create requirements.txt or finalize pyproject.toml
- [ ] 10.2: Write setup instructions in README
- [ ] 10.3: Test fresh installation from scratch
- [ ] 10.4: Verify all environment variables are documented
- [ ] 10.5: Add health check endpoint (GET /health or GET /)

## Task Dependencies

```
Phase 1 (Foundation)
  └── Phase 2 (File Upload)
      └── Phase 3 (Transcription)
          └── Phase 4 (Agents)
              └── Phase 5 (Grading Pipeline)
                  ├── Phase 6 (SSE Streaming)
                  └── Phase 7 (Results Retrieval)
                      └── Phase 8 (Frontend Integration)
                          └── Phase 9 (Error Handling)
                              └── Phase 10 (Deployment)
```

**Critical Path**: Foundation → File Upload → Agents → Grading Pipeline → SSE
**Parallel Work Possible**:
- Tasks 1.7-1.8 (problem endpoints) can be done in parallel with 1.4-1.6
- Phase 7 (results retrieval) can be done in parallel with Phase 6 (SSE)
- Phase 9 (error handling) can be incrementally added throughout

## Notes

### ADK Research Needed
- **Critical**: Verify Google ADK Python SDK is available and stable
- **Backup Plan**: If ADK doesn't exist or is unstable, use Google Generative AI SDK with manual agent orchestration
- **Documentation**: Check if ADK supports SequentialAgent and ParallelAgent as shown in PRD

### Gemini API Considerations
- **Audio Format**: PRD mentions webm audio - verify Gemini API supports this format directly
- **Multimodal Input**: Gemini 2.5 Flash must handle both images (PNG) and text (transcripts)
- **Structured Output**: Use `response_mime_type="application/json"` for consistent agent outputs
- **Rate Limits**: Consider rate limits for hackathon usage (6 problems × multiple submissions)

### Implementation Priorities
1. **Must-Have**: Phases 1-6 (core grading pipeline with SSE)
2. **Should-Have**: Phases 7-8 (results retrieval + frontend integration)
3. **Nice-to-Have**: Phase 9 (comprehensive error handling)
4. **Stretch**: Task 7.2 (dashboard endpoint for score history)

### Testing Strategy

### Time Estimates (Hackathon Context)
Based on PRD milestone: Backend agents should take ~5 hours (hours 10-15)
- Phase 1: ~2 hours (setup + basic routes)
- Phase 2: ~1 hour (file upload)
- Phase 3: ~1.5 hours (audio transcription + Gemini research)
- Phase 4: ~3 hours (5 agents + orchestration)
- Phase 5: ~1.5 hours (grading integration)
- Phase 6: ~1 hour (SSE)
- Phase 7: ~0.5 hours (results endpoints)
- Phases 8-10: ~1.5 hours (testing + polish)
**Total**: ~12 hours for full backend

## Completed This Iteration
- Task 1.9: Created seed data for 6 system design problems
  - Created `backend/app/db/seed_data.sql` with INSERT statements for all 6 problems
  - Problems: URL Shortener (apprentice), Rate Limiter (apprentice), Spotify (sorcerer), Chat System (sorcerer), YouTube (archmage), Google Docs (archmage)
  - Each problem includes: title, prompt, difficulty, focus_tags, constraints, estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
  - All JSON fields properly formatted and validated by SQLite CHECK constraints
  - Successfully inserted seed data into database - verified 6 rows in problems table
  - Tested query: all problems have correct difficulty levels and time allocations

## Completed Previously
- Task 1.1: Updated pyproject.toml with correct dependencies
  - Changed `google-genai>=1.0.0` to `google-adk>=0.1.0` (the correct ADK package)
  - Verified all dependencies install successfully with `uv sync`
  - Installed packages: google-adk==1.24.1, fastapi==0.128.4, uvicorn==0.40.0, aiosqlite==0.22.1, pydantic==2.12.5, python-multipart==0.0.22, sse-starlette==3.2.0, python-dotenv==1.2.1
- Task 1.2: Added `.env.example` configuration template
  - Documented FastAPI host/port, SQLite path, upload settings, and Gemini/ADK keys
  - Set sensible defaults (dev host, 50 MB upload cap) so teammates can copy to `.env`
- Task 1.3: Scaffolded `backend/app` package layout
  - Added `app/` package with `models`, `routes`, `services`, and `agents` subpackages plus `__init__.py` exports to prepare for future modules
- Task 1.4: Added core Pydantic schemas for API contracts
  - Created enums + shared `APISchema` config plus `Problem`, `Submission`, `DimensionScore`, and `GradingReport` models with per-phase metadata
- Task 1.5: Added SQLite schema + init utility
  - Authored `app/db/schema.sql` for problems, submissions, grading_results with JSON checks + FK constraints and provided `uv run python -m app.db.init_db` helper to bootstrap `backend/data/designdual.db`
- Task 1.6: Added FastAPI app factory with CORS configuration
  - Added `app/main.py` to load `.env`, configure CORS from `FRONTEND_ORIGIN`, and expose `app` for uvicorn
- Task 1.7: Implemented problem listing endpoint
  - Added `app/routes/problems.py` to fetch problem summaries from SQLite and wired the router into `app/main.py`
- Task 1.8: Implemented problem detail endpoint
  - Added `get_problem_by_id` service function to `app/services/problems.py` that fetches full Problem with all fields (prompt, constraints, rubric_hints, etc.)
  - Added GET `/api/problems/{id}` route that returns 404 with proper error message if problem not found
  - Tested endpoint with curl: returns empty array for list, 404 for nonexistent ID
  - Created backend/.env from .env.example for testing

## Notes
- The correct package for Google ADK is `google-adk`, not `google-adk-python` or just `google-genai`
- `google-genai==1.62.0` is automatically installed as a dependency of `google-adk`
- All 112 packages installed successfully in backend/.venv
- Backend still requires a real `.env` populated with secrets before running uvicorn; `.env.example` is checked in for reference
- Next up: Task 1.3 to scaffold `backend/app` layout
