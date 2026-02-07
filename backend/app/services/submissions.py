"""Submission data access and creation helpers."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Dict, Optional

import aiosqlite

from app.models import PhaseArtifacts, PhaseName, Submission, SubmissionStatus


async def create_submission(
    connection: aiosqlite.Connection,
    problem_id: str,
    phase_times: Dict[PhaseName, int],
    phases: Dict[PhaseName, PhaseArtifacts],
) -> Submission:
    """Create a new submission record in the database.

    Args:
        connection: Active database connection
        problem_id: ID of the problem being solved
        phase_times: Client-supplied elapsed time (seconds) per phase
        phases: Per-phase artifact metadata (canvas_path, audio_path, etc.)

    Returns:
        Newly created Submission object
    """
    submission_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Convert phase_times to JSON (PhaseName -> seconds)
    phase_times_json = json.dumps(
        {phase.value: seconds for phase, seconds in phase_times.items()}
    )

    # Convert phases to JSON (PhaseName -> PhaseArtifacts dict)
    phases_json = json.dumps(
        {phase.value: artifacts.model_dump() for phase, artifacts in phases.items()}
    )

    await connection.execute(
        """
        INSERT INTO submissions (id, problem_id, status, phase_times, phases, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id,
            problem_id,
            SubmissionStatus.RECEIVED.value,
            phase_times_json,
            phases_json,
            now,
            now,
        ),
    )
    await connection.commit()

    return Submission(
        id=submission_id,
        problem_id=problem_id,
        status=SubmissionStatus.RECEIVED,
        created_at=now,
        updated_at=now,
        phase_times=phase_times,
        phases=phases,
    )


async def get_submission_by_id(
    connection: aiosqlite.Connection,
    submission_id: str,
) -> Optional[Submission]:
    """Fetch a single submission by ID.

    Args:
        connection: Active database connection
        submission_id: Submission ID to fetch

    Returns:
        Submission object if found, None otherwise
    """
    cursor = await connection.execute(
        """
        SELECT id, problem_id, status, phase_times, phases, created_at, updated_at
        FROM submissions
        WHERE id = ?
        """,
        (submission_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row is None:
        return None

    # Parse JSON fields
    phase_times_dict = json.loads(row["phase_times"] or "{}")
    phases_dict = json.loads(row["phases"] or "{}")

    # Convert string keys back to PhaseName enums
    phase_times = {PhaseName(k): v for k, v in phase_times_dict.items()}
    phases = {
        PhaseName(k): PhaseArtifacts(**v) for k, v in phases_dict.items()
    }

    return Submission(
        id=row["id"],
        problem_id=row["problem_id"],
        status=SubmissionStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        phase_times=phase_times,
        phases=phases,
    )


__all__ = ["create_submission", "get_submission_by_id"]
