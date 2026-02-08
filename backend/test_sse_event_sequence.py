"""Test that SSE events follow the correct v2 sequence."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.contract_v2 import StreamStatus
from app.services.database import get_db_connection
from app.services.grading_events import get_grading_events


async def test_sse_event_sequence():
    """Verify that a completed submission has events in correct v2 order."""
    connection = await get_db_connection()

    # Find a completed submission
    cursor = await connection.execute(
        """
        SELECT id FROM submissions
        WHERE status = 'complete'
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    row = await cursor.fetchone()

    if not row:
        print("❌ No completed submissions found - cannot test event sequence")
        return False

    submission_id = row[0]
    print(f"Testing event sequence for submission: {submission_id}")

    # Get all events
    events = await get_grading_events(connection, submission_id)
    await connection.close()

    if not events:
        print("❌ No events found for submission")
        return False

    print(f"\n📋 Found {len(events)} events:")
    for i, event in enumerate(events, 1):
        phase_info = f" (phase: {event.phase.value})" if event.phase else ""
        progress_info = f" [progress: {event.progress:.2f}]" if event.progress is not None else ""
        print(f"  {i}. {event.status.value:15} {phase_info:20} {progress_info:20} | {event.message}")

    # Expected v2 sequence (not all are required, but if present should be in order)
    expected_order = [
        StreamStatus.QUEUED,       # Optional: might not be emitted yet
        StreamStatus.PROCESSING,   # Required: initial processing
        StreamStatus.CLARIFY,      # Required: phase 1
        StreamStatus.ESTIMATE,     # Required: phase 2
        StreamStatus.DESIGN,       # Required: phase 3
        StreamStatus.EXPLAIN,      # Required: phase 4
        StreamStatus.SYNTHESIZING, # Required: synthesis
        StreamStatus.COMPLETE,     # Required: final
    ]

    # Extract unique statuses in order
    status_sequence = []
    for event in events:
        if not status_sequence or status_sequence[-1] != event.status:
            status_sequence.append(event.status)

    print(f"\n🔄 Status sequence: {' → '.join([s.value for s in status_sequence])}")

    # Validate critical statuses are present
    required_statuses = {
        StreamStatus.PROCESSING,
        StreamStatus.CLARIFY,
        StreamStatus.ESTIMATE,
        StreamStatus.DESIGN,
        StreamStatus.EXPLAIN,
        StreamStatus.SYNTHESIZING,
        StreamStatus.COMPLETE,
    }

    present_statuses = set(status_sequence)
    missing_statuses = required_statuses - present_statuses

    if missing_statuses:
        print(f"\n❌ Missing required statuses: {[s.value for s in missing_statuses]}")
        return False

    # Validate order is correct (each status in expected_order should come after previous)
    last_idx = -1
    for status in status_sequence:
        if status in expected_order:
            current_idx = expected_order.index(status)
            if current_idx < last_idx:
                print(f"\n❌ Status out of order: {status.value} came after a later status")
                return False
            last_idx = current_idx

    # Validate phase-specific fields
    phase_events = [e for e in events if e.phase is not None]
    if len(phase_events) < 4:
        print(f"\n⚠️  Only {len(phase_events)} phase events found (expected 4)")

    print(f"\n✅ Event sequence is valid and follows v2 contract")
    print(f"   • All required statuses present")
    print(f"   • Statuses in correct order")
    print(f"   • {len(phase_events)} phase events with phase field set")

    return True


if __name__ == "__main__":
    result = asyncio.run(test_sse_event_sequence())
    sys.exit(0 if result else 1)
