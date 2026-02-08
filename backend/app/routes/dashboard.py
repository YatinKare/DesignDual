"""Dashboard routes for score history and performance summary."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services import db_connection
from app.services.dashboard import get_score_history, get_score_summary

router = APIRouter(prefix="/api", tags=["dashboard"])
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of history entries"),
    connection: aiosqlite.Connection = Depends(db_connection),
) -> Dict[str, Any]:
    """
    Get the user's dashboard with score history and performance summary.

    This is a stretch goal endpoint for displaying user score history and
    aggregate performance statistics.

    Args:
        limit: Maximum number of history entries to return (1-100, default 50)

    Returns:
        Dashboard data containing:
        - summary: Performance summary with counts and averages
        - history: List of recent completed submissions with scores

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        # Get performance summary
        summary = await get_score_summary(connection)

        # Get score history
        history = await get_score_history(connection, limit=limit)

        return {
            "summary": summary,
            "history": history,
        }
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard data",
        )


@router.get("/dashboard/history")
async def get_dashboard_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of entries"),
    connection: aiosqlite.Connection = Depends(db_connection),
) -> List[Dict[str, Any]]:
    """
    Get just the score history without the summary.

    A lightweight endpoint for fetching only the history data.

    Args:
        limit: Maximum number of entries to return (1-100, default 50)

    Returns:
        List of score history entries with submission details and scores.

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        return await get_score_history(connection, limit=limit)
    except Exception as e:
        logger.error(f"Failed to retrieve score history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve score history",
        )


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    connection: aiosqlite.Connection = Depends(db_connection),
) -> Dict[str, Any]:
    """
    Get just the performance summary without the history.

    A lightweight endpoint for fetching only aggregate statistics.

    Returns:
        Performance summary with total submissions, average score,
        best/worst scores, and verdict breakdown.

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        return await get_score_summary(connection)
    except Exception as e:
        logger.error(f"Failed to retrieve score summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve score summary",
        )


__all__ = ["router"]
