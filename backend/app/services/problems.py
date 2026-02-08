"""Problem data access helpers."""

from __future__ import annotations

import json
from typing import List, Optional

import aiosqlite

from app.models import Problem, ProblemSummary


async def list_problem_summaries(
    connection: aiosqlite.Connection,
) -> List[ProblemSummary]:
    cursor = await connection.execute(
        """
        SELECT id, slug, title, difficulty, focus_tags, estimated_time_minutes
        FROM problems
        ORDER BY created_at ASC
        """
    )
    rows = await cursor.fetchall()
    await cursor.close()

    summaries: List[ProblemSummary] = []
    for row in rows:
        focus_tags = json.loads(row["focus_tags"] or "[]")
        summaries.append(
            ProblemSummary(
                id=row["id"],
                slug=row["slug"],
                title=row["title"],
                difficulty=row["difficulty"],
                focus_tags=focus_tags,
                estimated_time_minutes=row["estimated_time_minutes"],
            )
        )
    return summaries


async def get_problem_by_id(
    connection: aiosqlite.Connection,
    problem_id: str,
) -> Optional[Problem]:
    """Fetch a single problem by ID with all details.

    Args:
        connection: Active database connection
        problem_id: Problem ID to fetch

    Returns:
        Problem object if found, None otherwise
    """
    cursor = await connection.execute(
        """
        SELECT id, slug, title, difficulty, focus_tags, estimated_time_minutes,
               prompt, constraints, phase_time_minutes, rubric_hints, rubric_definition,
               sample_solution_outline
        FROM problems
        WHERE id = ?
        """,
        (problem_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row is None:
        return None

    # Parse JSON fields
    focus_tags = json.loads(row["focus_tags"] or "[]")
    constraints = json.loads(row["constraints"] or "[]")
    phase_time_minutes = json.loads(row["phase_time_minutes"] or "{}")
    rubric_hints = json.loads(row["rubric_hints"] or "{}")
    rubric_definition = json.loads(row["rubric_definition"] or "[]")

    return Problem(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        difficulty=row["difficulty"],
        focus_tags=focus_tags,
        estimated_time_minutes=row["estimated_time_minutes"],
        prompt=row["prompt"],
        constraints=constraints,
        phase_time_minutes=phase_time_minutes,
        rubric_hints=rubric_hints,
        rubric_definition=rubric_definition,
        sample_solution_outline=row["sample_solution_outline"],
    )


__all__ = ["list_problem_summaries", "get_problem_by_id"]
