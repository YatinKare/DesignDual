"""Screen 2 contract types for the v2 API responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from .common import APISchema, DifficultyLevel, PhaseName


class RubricStatus(str, Enum):
    """Status for individual rubric items."""

    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"


class StreamStatus(str, Enum):
    """SSE status values for real-time grading progress."""

    QUEUED = "queued"
    PROCESSING = "processing"
    CLARIFY = "clarify"
    ESTIMATE = "estimate"
    DESIGN = "design"
    EXPLAIN = "explain"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


class TranscriptSnippet(APISchema):
    """Timestamped transcript segment for evidence."""

    timestamp_sec: float = Field(ge=0, description="Time in seconds from phase start")
    text: str = Field(min_length=1, description="Transcribed text at this timestamp")


class EvidenceItem(APISchema):
    """Evidence for a single phase: snapshot + timestamped transcripts."""

    phase: PhaseName
    snapshot_url: str = Field(description="URL to the canvas PNG for this phase")
    transcripts: List[TranscriptSnippet] = Field(
        default_factory=list,
        description="Timestamped transcript snippets (empty if no audio)",
    )
    noticed: Optional[Dict[str, str]] = Field(
        default=None,
        description="Agent observations (e.g., {'strength': '...', 'issue': '...'})",
    )


class PhaseScore(APISchema):
    """Score and feedback for a single phase."""

    phase: PhaseName
    score: float = Field(ge=0, le=10, description="0-10 score for this phase")
    bullets: List[str] = Field(
        min_length=3,
        max_length=6,
        description="3-6 concise feedback bullets",
    )


class RubricItem(APISchema):
    """Individual rubric criterion score."""

    label: str = Field(description="Rubric criterion label")
    description: str = Field(description="What this criterion evaluates")
    score: float = Field(ge=0, le=10, description="Weighted score for this criterion")
    status: RubricStatus
    computed_from: List[PhaseName] = Field(
        description="Phases this rubric item is derived from"
    )


class RadarDimension(APISchema):
    """Radar chart skill dimension."""

    skill: str = Field(description="Skill name (e.g., 'clarity', 'structure')")
    score: float = Field(ge=0, le=10, description="0-10 score for this skill")
    label: str = Field(description="Display label for the skill")


class StrengthWeakness(APISchema):
    """Timestamped strength or weakness observation."""

    phase: PhaseName
    text: str = Field(min_length=1, description="The observation text")
    timestamp_sec: Optional[float] = Field(
        default=None,
        description="Timestamp in seconds if linked to transcript",
    )


class NextAttemptItem(APISchema):
    """Improvement plan item for next attempt."""

    what_went_wrong: str = Field(description="What to improve")
    do_next_time: str = Field(description="Actionable steps for next attempt")


class ReferenceOutlineSection(APISchema):
    """Section in the reference solution outline."""

    section: str = Field(description="Section name")
    bullets: List[str] = Field(description="Key points for this section")


class ReferenceOutline(APISchema):
    """Structured reference solution outline."""

    sections: List[ReferenceOutlineSection]


class ProblemMetadata(APISchema):
    """Problem metadata for submission result."""

    id: str
    name: str
    difficulty: DifficultyLevel


class SubmissionResultV2(APISchema):
    """Complete grading result conforming to Screen 2 contract."""

    # Metadata
    result_version: int = Field(default=2, description="Schema version for compatibility")
    submission_id: str
    problem: ProblemMetadata
    phase_times: Dict[PhaseName, int] = Field(
        description="Time spent per phase in seconds"
    )
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Core scores (exactly 4 entries)
    phase_scores: List[PhaseScore] = Field(
        min_length=4,
        max_length=4,
        description="Exactly 4 phase scores in order: clarify, estimate, design, explain",
    )

    # Evidence (exactly 4 entries)
    evidence: List[EvidenceItem] = Field(
        min_length=4,
        max_length=4,
        description="Exactly 4 evidence items, one per phase",
    )

    # Rubric breakdown
    rubric: List[RubricItem] = Field(
        description="Rubric criteria with computed scores"
    )

    # Radar chart
    radar: List[RadarDimension] = Field(
        min_length=4,
        description="At least 4 radar dimensions (clarity, structure, power, wisdom)",
    )

    # Overall verdict
    overall_score: float = Field(ge=0, le=10)
    verdict: str = Field(description="Final verdict (e.g., 'hire', 'no_hire')")
    summary: str = Field(description="One-paragraph summary of performance")

    # Observations
    strengths: List[StrengthWeakness] = Field(default_factory=list)
    weaknesses: List[StrengthWeakness] = Field(default_factory=list)
    highlights: List[StrengthWeakness] = Field(
        default_factory=list,
        description="Key transcript moments worth highlighting",
    )

    # Next steps
    next_attempt_plan: List[NextAttemptItem] = Field(
        min_length=3,
        description="Top 3 improvements for next attempt",
    )
    follow_up_questions: List[str] = Field(
        min_length=3,
        description="At least 3 follow-up questions to deepen understanding",
    )
    reference_outline: ReferenceOutline = Field(
        description="Structured outline of reference solution"
    )


__all__ = [
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
