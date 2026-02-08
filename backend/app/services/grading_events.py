"""Service for persisting and replaying grading SSE events."""

from __future__ import annotations

import logging
from typing import List, Optional

import aiosqlite

from app.models import PhaseName
from app.models.contract_v2 import StreamStatus

LOGGER = logging.getLogger(__name__)


class GradingEvent:
    """Represents a single grading status event."""

    def __init__(
        self,
        submission_id: str,
        status: StreamStatus,
        message: str,
        phase: Optional[PhaseName] = None,
        progress: Optional[float] = None,
    ):
        self.submission_id = submission_id
        self.status = status
        self.message = message
        self.phase = phase
        self.progress = progress


async def save_grading_event(
    connection: aiosqlite.Connection,
    submission_id: str,
    status: StreamStatus,
    message: str,
    phase: Optional[PhaseName] = None,
    progress: Optional[float] = None,
) -> None:
    """Persist a grading event to the database for SSE replay.

    Args:
        connection: Active database connection
        submission_id: ID of the submission being graded
        status: Stream status enum value
        message: Human-readable status message
        phase: Optional phase name if event is phase-specific
        progress: Optional progress value (0.0 to 1.0)
    """
    try:
        await connection.execute(
            """
            INSERT INTO grading_events (submission_id, status, message, phase, progress)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                status.value,
                message,
                phase.value if phase else None,
                progress,
            ),
        )
        await connection.commit()
        LOGGER.debug(
            "Saved grading event for submission %s: status=%s, phase=%s",
            submission_id,
            status.value,
            phase.value if phase else None,
        )
    except Exception as e:
        LOGGER.error(
            "Failed to save grading event for submission %s: %s",
            submission_id,
            e,
        )
        # Don't raise - event persistence should not block grading


async def get_grading_events(
    connection: aiosqlite.Connection,
    submission_id: str,
) -> List[GradingEvent]:
    """Retrieve all grading events for a submission in chronological order.

    Args:
        connection: Active database connection
        submission_id: ID of the submission

    Returns:
        List of GradingEvent objects ordered by creation time
    """
    cursor = await connection.execute(
        """
        SELECT submission_id, status, message, phase, progress, created_at
        FROM grading_events
        WHERE submission_id = ?
        ORDER BY created_at ASC
        """,
        (submission_id,),
    )

    events = []
    async for row in cursor:
        submission_id, status_str, message, phase_str, progress, created_at = row
        events.append(
            GradingEvent(
                submission_id=submission_id,
                status=StreamStatus(status_str),
                message=message,
                phase=PhaseName(phase_str) if phase_str else None,
                progress=progress,
            )
        )

    return events


__all__ = ["GradingEvent", "save_grading_event", "get_grading_events"]
