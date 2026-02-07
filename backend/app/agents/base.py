"""Base utilities and configuration for ADK agents."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from google.genai import types

# Agent model configuration
DEFAULT_MODEL = "gemini-2.5-flash"
JSON_RESPONSE_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json"
)


@dataclass
class AgentResult:
    """Represents the output from a specialist agent."""

    agent_name: str
    dimension_scores: Dict[str, Any] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    raw_output: str = ""


# Common instruction components
GRADING_SCALE = """
Use this 0-10 scoring scale:
- 9-10: Exceptional - demonstrates senior-level mastery
- 7-8: Strong - meets expectations for a mid-level engineer
- 5-6: Adequate - shows basic competency with some gaps
- 3-4: Weak - significant gaps in understanding
- 0-2: Insufficient - fundamental misunderstandings
"""

OUTPUT_FORMAT_INSTRUCTION = """
Return your evaluation as a JSON object with this structure:
{
  "scores": {
    "<dimension_name>": {
      "score": <0-10>,
      "feedback": "<detailed feedback>",
      "strengths": ["<strength 1>", ...],
      "weaknesses": ["<weakness 1>", ...]
    }
  },
  "observations": ["<observation 1>", ...],
  "summary": "<brief summary of evaluation>"
}
"""


def get_model_name() -> str:
    """Get the model name from environment or use default."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


__all__ = [
    "AgentResult",
    "DEFAULT_MODEL",
    "JSON_RESPONSE_CONFIG",
    "GRADING_SCALE",
    "OUTPUT_FORMAT_INSTRUCTION",
    "get_model_name",
]
