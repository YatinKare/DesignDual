"""Pydantic data models exposed by the backend application."""

from .common import (
    APISchema,
    DifficultyLevel,
    DimensionName,
    PhaseName,
    SubmissionStatus,
    VerdictLabel,
)
from .contract_v2 import (
    EvidenceItem,
    NextAttemptItem,
    PhaseScore,
    ProblemMetadata,
    RadarDimension,
    ReferenceOutline,
    ReferenceOutlineSection,
    RubricItem,
    RubricStatus,
    StreamStatus,
    StrengthWeakness,
    SubmissionResultV2,
    TranscriptSnippet,
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
    # V2 contract types
    "RubricStatus",
    "StreamStatus",
    "TranscriptSnippet",
    "EvidenceItem",
    "PhaseScore",
    "RubricItem",
    "RadarDimension",
    "StrengthWeakness",
    "NextAttemptItem",
    "ReferenceOutlineSection",
    "ReferenceOutline",
    "ProblemMetadata",
    "SubmissionResultV2",
]
