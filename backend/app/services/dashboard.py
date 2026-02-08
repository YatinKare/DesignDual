"""Dashboard service for retrieving user score history."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import aiosqlite

logger = logging.getLogger(__name__)


async def get_score_history(
    connection: aiosqlite.Connection,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Retrieve the score history for completed submissions.

    Returns a list of completed submissions with their grading results,
    ordered by completion date (most recent first).

    Args:
        connection: Database connection
        limit: Maximum number of results to return (default 50)

    Returns:
        List of score history entries, each containing:
        - submission_id: ID of the submission
        - problem_id: ID of the problem attempted
        - problem_title: Title of the problem
        - difficulty: Problem difficulty level
        - overall_score: Final score (0-10)
        - verdict: Grading verdict (hire/maybe/no-hire)
        - verdict_display: Human-readable verdict
        - created_at: When the submission was created
        - completed_at: When grading was completed
    """
    query = """
        SELECT 
            s.id AS submission_id,
            s.problem_id,
            p.title AS problem_title,
            p.difficulty,
            gr.overall_score,
            gr.verdict,
            gr.verdict_display,
            s.created_at,
            gr.created_at AS completed_at
        FROM submissions s
        INNER JOIN grading_results gr ON s.id = gr.submission_id
        INNER JOIN problems p ON s.problem_id = p.id
        WHERE s.status = 'complete'
        ORDER BY gr.created_at DESC
        LIMIT ?
    """

    try:
        cursor = await connection.execute(query, (limit,))
        rows = await cursor.fetchall()
        await cursor.close()

        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description]

        # Convert rows to dictionaries
        results = []
        for row in rows:
            entry = dict(zip(columns, row))
            results.append(entry)

        logger.debug(f"Retrieved {len(results)} score history entries")
        return results

    except Exception as e:
        logger.error(f"Error retrieving score history: {e}")
        raise


async def get_score_summary(
    connection: aiosqlite.Connection,
) -> Dict[str, Any]:
    """
    Get a summary of the user's performance across all completed submissions.

    Returns:
        Dictionary containing:
        - total_submissions: Count of completed submissions
        - average_score: Mean score across all submissions
        - best_score: Highest score achieved
        - worst_score: Lowest score achieved
        - verdict_breakdown: Count of each verdict type
    """
    summary_query = """
        SELECT 
            COUNT(*) AS total_submissions,
            AVG(gr.overall_score) AS average_score,
            MAX(gr.overall_score) AS best_score,
            MIN(gr.overall_score) AS worst_score
        FROM submissions s
        INNER JOIN grading_results gr ON s.id = gr.submission_id
        WHERE s.status = 'complete'
    """

    verdict_query = """
        SELECT 
            gr.verdict,
            COUNT(*) AS count
        FROM submissions s
        INNER JOIN grading_results gr ON s.id = gr.submission_id
        WHERE s.status = 'complete'
        GROUP BY gr.verdict
    """

    try:
        # Get summary stats
        cursor = await connection.execute(summary_query)
        row = await cursor.fetchone()
        await cursor.close()

        if row is None or row[0] == 0:
            return {
                "total_submissions": 0,
                "average_score": None,
                "best_score": None,
                "worst_score": None,
                "verdict_breakdown": {},
            }

        summary = {
            "total_submissions": row[0],
            "average_score": round(row[1], 2) if row[1] else None,
            "best_score": row[2],
            "worst_score": row[3],
        }

        # Get verdict breakdown
        cursor = await connection.execute(verdict_query)
        verdict_rows = await cursor.fetchall()
        await cursor.close()

        verdict_breakdown = {}
        for verdict_row in verdict_rows:
            verdict_breakdown[verdict_row[0]] = verdict_row[1]

        summary["verdict_breakdown"] = verdict_breakdown

        logger.debug(f"Score summary: {summary['total_submissions']} submissions, avg score: {summary['average_score']}")
        return summary

    except Exception as e:
        logger.error(f"Error retrieving score summary: {e}")
        raise
