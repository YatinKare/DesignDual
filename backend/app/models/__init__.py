"""Pydantic data models exposed by the backend application."""

from .common import (
    APISchema,
    DifficultyLevel,
    DimensionName,
    PhaseName,
    SubmissionStatus,
    VerdictLabel,
)
from .grading import DimensionScore, GradingReport
from .problem import Problem, ProblemSummary
from .submission import PhaseArtifacts, Submission

# Rebuild Submission model after GradingReport is imported to resolve forward references
Submission.model_rebuild()

__all__ = [
    "APISchema",
    "DifficultyLevel",
    "DimensionName",
    "PhaseName",
    "Problem",
    "ProblemSummary",
    "PhaseArtifacts",
    "Submission",
    "SubmissionStatus",
    "DimensionScore",
    "GradingReport",
    "VerdictLabel",
]
