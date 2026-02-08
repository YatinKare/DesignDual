"""Service layer for managing submission transcripts.

This module handles storing and retrieving timestamped transcript segments
for each phase of a submission.
"""

import logging
from typing import List, Optional

import aiosqlite

from app.models.contract_v2 import TranscriptSnippet

logger = logging.getLogger(__name__)


async def save_transcript_snippet(
    connection: aiosqlite.Connection,
    submission_id: str,
    phase: str,
    timestamp_sec: float,
    text: str,
    is_highlight: bool = False,
) -> None:
    """Save a single transcript snippet to the database.

    Args:
        connection: Active database connection
        submission_id: Submission ID
        phase: Phase name (clarify, estimate, design, explain)
        timestamp_sec: Timestamp in seconds from phase start
        text: Transcript text
        is_highlight: Whether this snippet is highlighted as important
    """
    await connection.execute(
        """
        INSERT INTO submission_transcripts (
            submission_id, phase, timestamp_sec, text, is_highlight
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (submission_id, phase, timestamp_sec, text, int(is_highlight)),
    )
    await connection.commit()


async def save_transcript_snippets_batch(
    connection: aiosqlite.Connection,
    submission_id: str,
    phase: str,
    snippets: List[TranscriptSnippet],
) -> None:
    """Save multiple transcript snippets for a phase in a batch.

    Args:
        connection: Active database connection
        submission_id: Submission ID
        phase: Phase name
        snippets: List of transcript snippets
    """
    if not snippets:
        logger.debug(f"No transcript snippets to save for {submission_id} phase {phase}")
        return

    try:
        rows = [
            (
                submission_id,
                phase,
                snippet.timestamp_sec,
                snippet.text,
                0,  # is_highlight defaults to False
            )
            for snippet in snippets
        ]

        await connection.executemany(
            """
            INSERT INTO submission_transcripts (
                submission_id, phase, timestamp_sec, text, is_highlight
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        await connection.commit()
        logger.info(
            f"Saved {len(snippets)} transcript snippets for submission {submission_id} phase {phase}"
        )

    except Exception as e:
        logger.error(
            f"Failed to save transcript snippets for {submission_id} phase {phase}: {e}"
        )
        raise


async def get_transcript_snippets(
    connection: aiosqlite.Connection,
    submission_id: str,
    phase: Optional[str] = None,
    highlights_only: bool = False,
) -> List[TranscriptSnippet]:
    """Retrieve transcript snippets for a submission.

    Args:
        connection: Active database connection
        submission_id: Submission ID
        phase: Optional phase filter (if None, returns all phases)
        highlights_only: If True, only return highlighted snippets

    Returns:
        List of transcript snippets ordered by timestamp
    """
    query = """
        SELECT timestamp_sec, text
        FROM submission_transcripts
        WHERE submission_id = ?
    """
    params = [submission_id]

    if phase:
        query += " AND phase = ?"
        params.append(phase)

    if highlights_only:
        query += " AND is_highlight = 1"

    query += " ORDER BY timestamp_sec ASC"

    cursor = await connection.execute(query, params)
    rows = await cursor.fetchall()

    return [TranscriptSnippet(timestamp_sec=row[0], text=row[1]) for row in rows]


async def mark_snippet_as_highlight(
    connection: aiosqlite.Connection,
    submission_id: str,
    phase: str,
    timestamp_sec: float,
) -> None:
    """Mark a specific transcript snippet as a highlight.

    Args:
        connection: Active database connection
        submission_id: Submission ID
        phase: Phase name
        timestamp_sec: Timestamp of the snippet to mark
    """
    await connection.execute(
        """
        UPDATE submission_transcripts
        SET is_highlight = 1
        WHERE submission_id = ? AND phase = ? AND timestamp_sec = ?
        """,
        (submission_id, phase, timestamp_sec),
    )
    await connection.commit()


async def delete_transcripts(
    connection: aiosqlite.Connection,
    submission_id: str,
) -> None:
    """Delete all transcript snippets for a submission.

    Args:
        connection: Active database connection
        submission_id: Submission ID
    """
    await connection.execute(
        "DELETE FROM submission_transcripts WHERE submission_id = ?",
        (submission_id,),
    )
    await connection.commit()
    logger.info(f"Deleted all transcript snippets for submission {submission_id}")
