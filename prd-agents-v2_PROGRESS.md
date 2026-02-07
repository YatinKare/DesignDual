# Progress: prd-agents-v1

## Status
IN_PROGRESS

## Task List
- [x] 1.1: Update pyproject.toml with all required dependencies
- [x] 1.2: Create .env.example file for configuration template
- [x] 1.3: Create backend/app/ directory structure (models/, routes/, services/, agents/)
- [x] 1.4: Define Pydantic schemas (Problem, Submission, GradingReport, DimensionScore)
- [x] 1.5: Create SQLite database schema and initialization script
- [x] 1.6: Create main.py FastAPI application with CORS middleware
- [x] 1.7: Implement GET /api/problems endpoint (list all problems)
- [x] 1.8: Implement GET /api/problems/{id} endpoint (problem details)
- [x] 1.9: Create seed data for 6 system design problems
- [x] 1.10: Test basic routes work (can fetch problems)
- [x] 2.1: Implement POST /api/submissions endpoint with multipart form-data handling
- [x] 2.2: Create file storage service (save uploaded PNGs and webm files)
- [x] 2.3: Implement submission record creation in SQLite
- [x] 2.4: Add file validation (check file types, size limits)
- [x] 2.5: Return submission_id immediately upon upload
- [x] 2.6: Test file upload flow end-to-end by making a temp file, doing a curl, deleting temp file
- [x] 3.1: Research Gemini API audio transcription capabilities using the gemini-docs-mcp mcp server
- [x] 3.2: Create transcription service using Gemini API
- [x] 3.3: Implement parallel transcription of up to 4 audio files
- [x] 3.4: Handle null/missing audio files gracefully
- [x] 3.5: Store transcripts in submission record
- [x] 3.6: Test transcription using the sample audio files in frontend/design-dual/static, doing a curl, comparing transcript, and cleaning up
- [x] 4.1: Research Google ADK Python SDK installation and basic usage
- [x] 4.2: Create agents/ directory with base agent structure
- [x] 4.3: Implement ScopingAgent prompt and logic (evaluates phases 1-2)
- [x] 4.4: Implement DesignAgent prompt and logic (evaluates phase 3)
- [x] 4.5: Implement ScaleAgent prompt and logic (cross-cutting evaluation)
- [x] 4.6: Implement TradeoffAgent prompt and logic (evaluates phases 3-4)
- [x] 4.7: Implement SynthesisAgent prompt and logic (combines all outputs)
- [x] 4.8: Create ADK orchestration with SequentialAgent + ParallelAgent
- [x] 4.9: Test individual agents with sample inputs
- [ ] 4.11: Test full agent pipeline with mock submission data, doing a curl, and keep mock submission data in temp folder for later testing
- [ ] 5.1: Create grading service that assembles submission bundle
- [ ] 5.2: Implement ADK session state initialization from submission data
- [ ] 5.3: Create background task for running grading pipeline
- [ ] 5.4: Store grading results in database (grading_results table)
- [ ] 5.5: Implement error handling for agent failures
- [ ] 5.6: Test full grading pipeline with real submission via curl
- [ ] 6.1: Install and configure sse-starlette for FastAPI
- [ ] 6.2: Implement GET /api/submissions/{id}/stream SSE endpoint
- [ ] 6.3: Create event generator that yields grading progress updates
- [ ] 6.4: Emit themed status messages (magic narrative)
- [ ] 6.5: Emit final result when grading completes
- [ ] 6.6: Test SSE connection and event streaming
- [ ] 7.1: Implement GET /api/submissions/{id} endpoint (fetch grading result)
- [ ] 7.2: Implement GET /api/dashboard endpoint (user score history - stretch goal)
- [ ] 7.3: Test results retrieval
- [ ] 7.4: Add proper error handling for not-found cases
- [ ] 8.1: Document all API endpoints with example requests/responses
- [ ] 8.2: Test CORS configuration for frontend connection
- [ ] 8.3: Verify file upload size limits are appropriate
- [ ] 8.4: Create Postman/Thunder Client collection for testing
- [ ] 8.5: End-to-end test: upload submission → stream progress → fetch result via curl
- [ ] 9.1: Add comprehensive error handling to all routes
- [ ] 9.2: Add logging for debugging (use Python logging module)
- [ ] 9.3: Handle edge cases (missing files, invalid data, API failures)
- [ ] 9.4: Add request validation with Pydantic
- [ ] 9.5: Test failure scenarios (invalid problem_id, corrupt files, etc.)
- [ ] 10.1: Create requirements.txt or finalize pyproject.toml
- [ ] 10.2: Write setup instructions in README
- [ ] 10.3: Test fresh installation from scratch
- [ ] 10.4: Verify all environment variables are documented
- [ ] 10.5: Add health check endpoint (GET /health or GET /)

## Completed This Iteration
- Task 4.9: Updated JSON extraction in agent test harness to strip markdown fences and verified individual agent tests parse JSON successfully.

## Notes
- Agent test harness now handles fenced JSON (```json ... ```), so outputs from Scoping/Design/Scale/Tradeoff parse cleanly.
- Ran `uv run python -m app.agents.test_pipeline` successfully; results saved to backend/temp/agent_test_results.json.

## Completed This Iteration
- Enforced JSON-only responses from ADK agents by setting `response_mime_type="application/json"` in agent configs.

## Notes
- Individual agent outputs now return raw JSON without markdown fences in the test harness.
- Full pipeline still returned an unexpected JSON payload (not the final report); may need investigation in Task 4.11 or later.
