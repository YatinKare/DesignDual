"""Problem domain schemas returned by the problem endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import Field

from .common import APISchema, DifficultyLevel, PhaseName


class RubricDefinition(APISchema):
    """Individual rubric criterion with phase weights."""

    label: str = Field(description="Rubric criterion label")
    description: str = Field(description="What this criterion evaluates")
    phase_weights: Dict[PhaseName, float] = Field(
        description="Phase weights for computing this rubric score (should sum to 1.0)"
    )


class ProblemSummary(APISchema):
    """Lightweight view used for problem list responses."""

    id: str
    slug: str
    title: str
    difficulty: DifficultyLevel
    focus_tags: List[str] = Field(default_factory=list)
    estimated_time_minutes: int = Field(ge=5, description="Suggested total time budget.")


class Problem(ProblemSummary):
    """Full problem detail with rubric hints and per-phase metadata."""

    prompt: str
    constraints: List[str] = Field(default_factory=list)
    phase_time_minutes: Dict[PhaseName, int] = Field(
        default_factory=dict,
        description="Minutes allocated per phase for this prompt.",
    )
    rubric_hints: Dict[str, str] = Field(
        default_factory=dict,
        description="Key things graders look for in each phase or dimension.",
    )
    rubric_definition: List[RubricDefinition] = Field(
        default_factory=list,
        description="Structured rubric criteria with phase weights for v2 contract.",
    )
    sample_solution_outline: Optional[str] = Field(
        default=None,
        description="High-level outline used to inspire feedback or references.",
    )


__all__ = ["Problem", "ProblemSummary", "RubricDefinition"]
