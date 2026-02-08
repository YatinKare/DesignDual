#!/usr/bin/env python3
"""Direct test for QUEUED status on submission creation."""

import asyncio
import uuid
from pathlib import Path

import aiosqlite


async def test_queued_status():
    """Test that new submissions are created with QUEUED status."""
    backend_dir = Path(__file__).parent
    db_path = backend_dir / "data" / "designdual.db"

    # Import after setting up path
    import sys
    sys.path.insert(0, str(backend_dir))

    from app.models import PhaseName, PhaseArtifacts
    from app.services.submissions import create_submission

    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row

        # Create a test submission
        test_id = str(uuid.uuid4())
        phase_times = {
            PhaseName.CLARIFY: 180,
            PhaseName.ESTIMATE: 120,
            PhaseName.DESIGN: 240,
            PhaseName.EXPLAIN: 180,
        }
        phases = {
            PhaseName.CLARIFY: PhaseArtifacts(canvas_path="/tmp/test1.png"),
            PhaseName.ESTIMATE: PhaseArtifacts(canvas_path="/tmp/test2.png"),
            PhaseName.DESIGN: PhaseArtifacts(canvas_path="/tmp/test3.png"),
            PhaseName.EXPLAIN: PhaseArtifacts(canvas_path="/tmp/test4.png"),
        }

        print(f"Creating test submission {test_id}...")
        submission = await create_submission(
            connection=conn,
            problem_id="url-shortener",
            phase_times=phase_times,
            phases=phases,
            submission_id=test_id,
        )

        print(f"✅ Submission created with ID: {submission.id}")
        print(f"   Status: {submission.status}")
        print(f"   Expected: queued")

        # Verify in database
        cursor = await conn.execute(
            "SELECT status FROM submissions WHERE id = ?",
            (test_id,)
        )
        row = await cursor.fetchone()

        if row:
            db_status = row["status"]
            print(f"   Database status: {db_status}")

            if db_status == "queued":
                print("✅ TEST PASSED: Submission created with QUEUED status")
                return True
            else:
                print(f"❌ TEST FAILED: Expected 'queued', got '{db_status}'")
                return False
        else:
            print(f"❌ TEST FAILED: Submission not found in database")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_queued_status())
    exit(0 if success else 1)
