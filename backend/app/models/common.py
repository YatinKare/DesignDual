"""Common enums and Pydantic helpers shared across backend schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class DifficultyLevel(str, Enum):
    """Difficulty tiers shown in the problem browser."""

    APPRENTICE = "apprentice"
    SORCERER = "sorcerer"
    ARCHMAGE = "archmage"


class PhaseName(str, Enum):
    """Canonical identifiers for the four interview phases."""

    CLARIFY = "clarify"
    ESTIMATE = "estimate"
    DESIGN = "design"
    EXPLAIN = "explain"


class DimensionName(str, Enum):
    """Rubric dimension identifiers for grading."""

    SCOPING = "scoping"
    DESIGN = "design"
    SCALE = "scale"
    TRADEOFF = "tradeoff"


class SubmissionStatus(str, Enum):
    """Lifecycle states for a submission as it moves through the pipeline."""

    RECEIVED = "received"
    TRANSCRIBING = "transcribing"
    GRADING = "grading"
    COMPLETE = "complete"
    FAILED = "failed"


class VerdictLabel(str, Enum):
    """High-level hiring verdicts mapped from the overall score."""

    STRONG_NO_HIRE = "strong_no_hire"
    LEAN_NO_HIRE = "lean_no_hire"
    NO_DECISION = "no_decision"
    LEAN_HIRE = "lean_hire"
    HIRE = "hire"
    STRONG_HIRE = "strong_hire"


class APISchema(BaseModel):
    """Base schema with shared config for API responses."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )


__all__ = [
    "APISchema",
    "DifficultyLevel",
    "DimensionName",
    "PhaseName",
    "SubmissionStatus",
    "VerdictLabel",
]
