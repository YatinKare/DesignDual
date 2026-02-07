"""Problem data access helpers."""

from __future__ import annotations

import json
from typing import List

import aiosqlite

from app.models import ProblemSummary


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


__all__ = ["list_problem_summaries"]
