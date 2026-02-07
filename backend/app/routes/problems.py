"""Problem listing endpoints."""

from __future__ import annotations

from typing import List

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.models import Problem, ProblemSummary
from app.services.database import db_connection
from app.services.problems import get_problem_by_id, list_problem_summaries

router = APIRouter(tags=["problems"])


@router.get("/api/problems", response_model=List[ProblemSummary])
async def list_problems(
    connection: aiosqlite.Connection = Depends(db_connection),
) -> List[ProblemSummary]:
    return await list_problem_summaries(connection)


@router.get("/api/problems/{id}", response_model=Problem)
async def get_problem(
    id: str,
    connection: aiosqlite.Connection = Depends(db_connection),
) -> Problem:
    problem = await get_problem_by_id(connection, id)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"Problem '{id}' not found")
    return problem


__all__ = ["router"]
