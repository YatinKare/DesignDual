"""Test grading events emission during submission processing."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database import get_db_connection
from app.services.grading_events import get_grading_events


async def check_grading_events(submission_id: str):
    """Check grading events for a submission."""
    connection = await get_db_connection()
    try:
        events = await get_grading_events(connection, submission_id)

        print(f"\n{'='*80}")
        print(f"Grading Events for Submission: {submission_id}")
        print(f"{'='*80}\n")

        if not events:
            print("❌ No grading events found")
            return False

        print(f"✓ Found {len(events)} grading events:\n")

        for i, event in enumerate(events, 1):
            phase_str = f" [Phase: {event.phase.value}]" if event.phase else ""
            progress_str = f" (Progress: {event.progress:.1%})" if event.progress is not None else ""
            print(f"{i}. Status: {event.status.value}{phase_str}{progress_str}")
            print(f"   Message: {event.message}\n")

        # Verify expected status sequence
        expected_statuses = [
            "processing",  # Initial
            "processing",  # Transcription start
            "processing",  # Transcription complete
            "clarify",     # Phase 1
            "estimate",    # Phase 2
            "design",      # Phase 3
            "explain",     # Phase 4
            "synthesizing",  # Synthesis
            "complete",    # Result saved
            "complete",    # Final
        ]

        actual_statuses = [e.status.value for e in events]

        print(f"\n{'='*80}")
        print("Status Sequence Validation:")
        print(f"{'='*80}\n")

        if len(actual_statuses) == len(expected_statuses):
            print(f"✓ Event count matches: {len(actual_statuses)}")
        else:
            print(f"⚠ Event count mismatch: expected {len(expected_statuses)}, got {len(actual_statuses)}")

        # Check for all required phases
        phase_events = [e for e in events if e.phase]
        phase_names = {e.phase.value for e in phase_events}
        required_phases = {"clarify", "estimate", "design", "explain"}

        if phase_names == required_phases:
            print(f"✓ All 4 phases present: {sorted(phase_names)}")
        else:
            missing = required_phases - phase_names
            extra = phase_names - required_phases
            if missing:
                print(f"⚠ Missing phases: {sorted(missing)}")
            if extra:
                print(f"⚠ Extra phases: {sorted(extra)}")

        # Check progress values
        progress_events = [e for e in events if e.progress is not None]
        if progress_events:
            print(f"✓ Progress tracking: {len(progress_events)} events with progress values")
            min_progress = min(e.progress for e in progress_events)
            max_progress = max(e.progress for e in progress_events)
            print(f"  Range: {min_progress:.1%} → {max_progress:.1%}")

        print(f"\n{'='*80}")
        print("✅ Grading events validation complete!")
        print(f"{'='*80}\n")

        return True

    finally:
        await connection.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python test_grading_events.py <submission_id>")
        print("\nTo test with the most recent submission:")
        print("  sqlite3 backend/data/designdual.db \"SELECT id FROM submissions ORDER BY created_at DESC LIMIT 1;\"")
        sys.exit(1)

    submission_id = sys.argv[1]
    asyncio.run(check_grading_events(submission_id))
