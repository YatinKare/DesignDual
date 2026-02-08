# SSE Event Flow v2 (Screen 2 Compliant)

## Overview
This document describes the standardized Server-Sent Events (SSE) flow for grading submissions in the v2 API system.

## Event Sequence

The complete grading pipeline emits events in the following order:

```
QUEUED → PROCESSING → CLARIFY → ESTIMATE → DESIGN → EXPLAIN → SYNTHESIZING → COMPLETE
```

If any error occurs, the flow terminates with:
```
... → FAILED
```

## Detailed Event Breakdown

### 1. QUEUED (Initial State)
- **Status**: `queued`
- **When**: Immediately after submission is created via POST /api/submissions
- **Message**: N/A (no event emitted yet - this is just the database status)
- **Progress**: N/A
- **Phase**: N/A

### 2. PROCESSING (Background Task Start)
- **Status**: `processing`
- **When**: Background grading task begins execution
- **Message**: "Your spell has been submitted to the Council..."
- **Progress**: 0.0
- **Phase**: N/A

### 3. PROCESSING (Transcription Sub-phase)
- **Status**: `processing`
- **When**: Audio transcription begins
- **Message**: "Deciphering your spoken incantations..."
- **Progress**: 0.1
- **Phase**: N/A

### 4. PROCESSING (Transcription Complete)
- **Status**: `processing`
- **When**: Audio transcription completes, before agent evaluation
- **Message**: "Transcription complete. The Council begins evaluation..."
- **Progress**: 0.2
- **Phase**: N/A

### 5. CLARIFY (Phase 1 Evaluation)
- **Status**: `clarify`
- **When**: Clarification phase agent begins evaluation
- **Message**: "The Clarification Sage examines your problem understanding..."
- **Progress**: 0.3
- **Phase**: `clarify`

### 6. ESTIMATE (Phase 2 Evaluation)
- **Status**: `estimate`
- **When**: Estimation phase agent begins evaluation
- **Message**: "The Estimation Oracle calculates your capacity planning..."
- **Progress**: 0.4
- **Phase**: `estimate`

### 7. DESIGN (Phase 3 Evaluation)
- **Status**: `design`
- **When**: Design phase agent begins evaluation
- **Message**: "The Architecture Archmage studies your system blueprint..."
- **Progress**: 0.5
- **Phase**: `design`

### 8. EXPLAIN (Phase 4 Evaluation)
- **Status**: `explain`
- **When**: Explanation phase agent begins evaluation
- **Message**: "The Wisdom Keeper weighs your reasoning and tradeoffs..."
- **Progress**: 0.6
- **Phase**: `explain`

### 9. SYNTHESIZING (Final Synthesis)
- **Status**: `synthesizing`
- **When**: All phase agents complete, synthesis agent combines results
- **Message**: "The Council deliberates and forges the final verdict..."
- **Progress**: 0.85
- **Phase**: N/A

### 10. COMPLETE (Success)
- **Status**: `complete`
- **When**: Grading result saved to database, submission marked complete
- **Message**: "The verdict is sealed. View your complete evaluation."
- **Progress**: 1.0
- **Phase**: N/A

### 11. FAILED (Error)
- **Status**: `failed`
- **When**: Any error occurs during grading (transcription, agent execution, persistence)
- **Message**: "Grading failed: [error message]"
- **Progress**: N/A
- **Phase**: N/A

## StreamStatus Enum

```python
class StreamStatus(str, Enum):
    """SSE status values for real-time grading progress."""

    QUEUED = "queued"           # Initial state (not emitted as event)
    PROCESSING = "processing"    # Background task running
    CLARIFY = "clarify"         # Phase 1: Problem clarification
    ESTIMATE = "estimate"       # Phase 2: Capacity estimation
    DESIGN = "design"           # Phase 3: System design
    EXPLAIN = "explain"         # Phase 4: Tradeoff explanation
    SYNTHESIZING = "synthesizing" # Combining all results
    COMPLETE = "complete"       # Success
    FAILED = "failed"           # Error
```

## Event Schema

Each grading event has the following structure:

```python
{
    "submission_id": str,       # UUID of the submission
    "status": StreamStatus,     # Current status (enum value)
    "message": str,             # Human-readable message (magic-themed)
    "phase": Optional[PhaseName], # Phase name if status is phase-specific
    "progress": Optional[float],  # Progress 0.0-1.0, or None
}
```

## Implementation Notes

### Event Persistence
All events are persisted to the `grading_events` table for:
- SSE replay on client reconnection
- Debugging grading pipeline execution
- Audit trail of submission processing

### Progress Values
Progress values are approximate and designed for UI progress bars:
- 0.0 - 0.2: Preprocessing (transcription)
- 0.3 - 0.6: Phase-by-phase evaluation (agents run in parallel but events emitted sequentially)
- 0.85: Synthesis
- 1.0: Complete

### Phase Events
Phase-specific events (clarify, estimate, design, explain) include the `phase` field to support:
- UI phase card highlighting during grading
- Phase-specific event filtering
- Detailed progress tracking per phase

### Parallel Agent Execution
Although the 4 phase agents run in parallel via ADK's ParallelAgent, we emit their status events sequentially to:
1. Create a smooth SSE stream experience for the frontend
2. Maintain predictable event ordering
3. Provide clear progress indication even though work happens concurrently

### Magic Narrative Theme
All messages maintain the "magic council" narrative for user engagement:
- Council = grading agents
- Spell = submission
- Incantations = audio transcripts
- Verdict = grading result

## Legacy Status Mapping (for compatibility)

If supporting legacy clients, map old statuses to new:
- `scoping` → `clarify`
- `tradeoff` → `explain`
- `scale` → `estimate` (or skip if not used)

## Testing

To test the event sequence:
1. Create a new submission via POST /api/submissions
2. Query grading_events table for the submission_id
3. Verify events appear in correct order with proper phase fields
4. Run: `uv run python test_sse_event_sequence.py`

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS grading_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    phase TEXT,
    progress REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_grading_events_submission
    ON grading_events(submission_id, created_at);
```

## Related Files
- `backend/app/services/grading.py` - Event emission logic
- `backend/app/services/grading_events.py` - Event persistence service
- `backend/app/models/contract_v2.py` - StreamStatus enum definition
- `backend/app/db/migrate_add_grading_events.py` - Database migration
