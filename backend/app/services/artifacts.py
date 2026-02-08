"""Service for persisting and retrieving submission artifacts."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import aiosqlite

from app.models import PhaseName

logger = logging.getLogger(__name__)


async def save_submission_artifact(
    connection: aiosqlite.Connection,
    submission_id: str,
    phase: PhaseName,
    canvas_url: Optional[str],
    audio_url: Optional[str],
    canvas_mime_type: Optional[str] = None,
    audio_mime_type: Optional[str] = None,
) -> None:
    """Persist artifact URLs for a specific submission phase.

    Args:
        connection: Database connection
        submission_id: Submission ID
        phase: Phase name (clarify/estimate/design/explain)
        canvas_url: URL to canvas snapshot (e.g., "/uploads/{id}/canvas_clarify.png")
        audio_url: Optional URL to audio recording
        canvas_mime_type: MIME type for canvas (default: image/png)
        audio_mime_type: MIME type for audio (default: audio/webm)
    """
    # Set default MIME types if not provided
    if canvas_url and not canvas_mime_type:
        canvas_mime_type = "image/png"
    if audio_url and not audio_mime_type:
        audio_mime_type = "audio/webm"

    try:
        await connection.execute(
            """
            INSERT INTO submission_artifacts
            (submission_id, phase, canvas_url, audio_url, canvas_mime_type, audio_mime_type)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(submission_id, phase) DO UPDATE SET
                canvas_url = excluded.canvas_url,
                audio_url = excluded.audio_url,
                canvas_mime_type = excluded.canvas_mime_type,
                audio_mime_type = excluded.audio_mime_type
            """,
            (
                submission_id,
                phase.value,
                canvas_url,
                audio_url,
                canvas_mime_type,
                audio_mime_type,
            ),
        )
        await connection.commit()
        logger.debug(
            f"Saved artifact for submission {submission_id}, phase {phase.value}: "
            f"canvas={canvas_url}, audio={audio_url}"
        )
    except Exception as e:
        logger.error(
            f"Failed to save artifact for submission {submission_id}, phase {phase.value}: {e}"
        )
        raise


async def save_submission_artifacts_batch(
    connection: aiosqlite.Connection,
    submission_id: str,
    artifacts: Dict[PhaseName, Dict[str, Optional[str]]],
) -> None:
    """Persist multiple artifacts for a submission in a batch.

    Args:
        connection: Database connection
        submission_id: Submission ID
        artifacts: Dict mapping phase to artifact URLs
            Example: {
                PhaseName.CLARIFY: {
                    "canvas_url": "/uploads/abc/canvas_clarify.png",
                    "audio_url": "/uploads/abc/audio_clarify.webm",
                    "canvas_mime_type": "image/png",
                    "audio_mime_type": "audio/webm"
                }
            }
    """
    for phase, artifact_data in artifacts.items():
        await save_submission_artifact(
            connection,
            submission_id,
            phase,
            canvas_url=artifact_data.get("canvas_url"),
            audio_url=artifact_data.get("audio_url"),
            canvas_mime_type=artifact_data.get("canvas_mime_type"),
            audio_mime_type=artifact_data.get("audio_mime_type"),
        )


async def get_submission_artifacts(
    connection: aiosqlite.Connection,
    submission_id: str,
) -> Dict[str, Dict[str, Optional[str]]]:
    """Retrieve all artifacts for a submission.

    Args:
        connection: Database connection
        submission_id: Submission ID

    Returns:
        Dict mapping phase to artifact URLs
        Example: {
            "clarify": {
                "canvas_url": "/uploads/abc/canvas_clarify.png",
                "audio_url": "/uploads/abc/audio_clarify.webm",
                "canvas_mime_type": "image/png",
                "audio_mime_type": "audio/webm"
            }
        }
    """
    cursor = await connection.execute(
        """
        SELECT phase, canvas_url, audio_url, canvas_mime_type, audio_mime_type
        FROM submission_artifacts
        WHERE submission_id = ?
        ORDER BY
            CASE phase
                WHEN 'clarify' THEN 1
                WHEN 'estimate' THEN 2
                WHEN 'design' THEN 3
                WHEN 'explain' THEN 4
            END
        """,
        (submission_id,),
    )

    artifacts = {}
    async for row in cursor:
        phase, canvas_url, audio_url, canvas_mime, audio_mime = row
        artifacts[phase] = {
            "canvas_url": canvas_url,
            "audio_url": audio_url,
            "canvas_mime_type": canvas_mime,
            "audio_mime_type": audio_mime,
        }

    return artifacts


__all__ = [
    "save_submission_artifact",
    "save_submission_artifacts_batch",
    "get_submission_artifacts",
]
