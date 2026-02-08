"""Schemas describing rubric scoring returned by Gemini agents."""

from __future__ import annotations

from typing import Dict, List

from pydantic import Field

from .common import APISchema, DimensionName, PhaseName, VerdictLabel


class DimensionScore(APISchema):
    """Score plus qualitative feedback for a single rubric dimension."""

    score: float = Field(ge=0, le=10)
    feedback: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class GradingReport(APISchema):
    """Aggregated result returned to the frontend after grading."""

    overall_score: float = Field(ge=0, le=10)
    verdict: VerdictLabel
    verdict_display: str = Field(
        default="",
        description="Human-readable verdict label (e.g., 'Hire').",
    )
    dimensions: Dict[DimensionName, DimensionScore] = Field(
        default_factory=dict, description="Per-dimension structured feedback."
    )
    top_improvements: List[str] = Field(default_factory=list)
    phase_observations: Dict[PhaseName, str] = Field(default_factory=dict)


__all__ = ["DimensionScore", "GradingReport"]
