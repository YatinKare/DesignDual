"""Problem listing endpoints."""

from __future__ import annotations

import json
from typing import List

import aiosqlite
from fastapi import APIRouter, Depends

from app.models import ProblemSummary
from app.services.database import db_connection

router = APIRouter(tags=["problems"])


@router.get("/api/problems", response_model=List[ProblemSummary])
async def list_problems(
    connection: aiosqlite.Connection = Depends(db_connection),
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


__all__ = ["router"]
