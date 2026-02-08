"""Problem listing endpoints."""

from __future__ import annotations

import logging
from typing import List

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.models import Problem, ProblemSummary
from app.services.database import db_connection
from app.services.problems import get_problem_by_id, list_problem_summaries

router = APIRouter(tags=["problems"])
logger = logging.getLogger(__name__)


@router.get("/api/problems", response_model=List[ProblemSummary])
async def list_problems(
    connection: aiosqlite.Connection = Depends(db_connection),
) -> List[ProblemSummary]:
    try:
        return await list_problem_summaries(connection)
    except Exception as e:
        logger.error("Failed to list problems: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch problems")


@router.get("/api/problems/{id}", response_model=Problem)
async def get_problem(
    id: str,
    connection: aiosqlite.Connection = Depends(db_connection),
) -> Problem:
    try:
        problem = await get_problem_by_id(connection, id)
        if problem is None:
            raise HTTPException(status_code=404, detail=f"Problem '{id}' not found")
        return problem
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get problem %s: %s", id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch problem")


__all__ = ["router"]
