"""Problem listing endpoints."""

from __future__ import annotations

from typing import List

import aiosqlite
from fastapi import APIRouter, Depends

from app.models import ProblemSummary
from app.services.database import db_connection
from app.services.problems import list_problem_summaries

router = APIRouter(tags=["problems"])


@router.get("/api/problems", response_model=List[ProblemSummary])
async def list_problems(
    connection: aiosqlite.Connection = Depends(db_connection),
) -> List[ProblemSummary]:
    return await list_problem_summaries(connection)


__all__ = ["router"]
