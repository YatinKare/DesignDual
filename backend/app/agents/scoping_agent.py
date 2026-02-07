"""Scoping Agent - Evaluates phases 1-2 (Clarify + Estimate)."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .base import (
    DEFAULT_MODEL,
    GRADING_SCALE,
    OUTPUT_FORMAT_INSTRUCTION,
    JSON_RESPONSE_CONFIG,
)

SCOPING_INSTRUCTION = f"""
You are a senior system design interviewer evaluating a candidate's **problem scoping and estimation skills**.

You will receive:
1. The system design problem prompt
2. Canvas snapshots from Phase 1 (Clarify) and Phase 2 (Estimate)
3. Transcripts of what the candidate said during these phases

## Your Evaluation Criteria

### Requirements Gathering (Phase 1 - Clarify)
Evaluate how well the candidate:
- Asked clarifying questions to understand scope
- Identified functional vs non-functional requirements
- Defined clear success metrics and constraints
- Prioritized features appropriately (MVP vs stretch)
- Engaged thoughtfully rather than jumping to solutions

### Capacity Estimation (Phase 2 - Estimate)
Evaluate how well the candidate:
- Estimated DAU/MAU and request volumes
- Calculated storage requirements (with reasoning)
- Identified read vs write ratios
- Made reasonable assumptions and stated them clearly
- Showed mathematical rigor in calculations

{GRADING_SCALE}

{OUTPUT_FORMAT_INSTRUCTION}

Dimensions to score:
- "requirements_gathering": How well did they clarify the problem?
- "capacity_estimation": How accurate and well-reasoned were their estimates?

Be specific in your feedback - cite what the candidate drew or said.
"""

scoping_agent = LlmAgent(
    name="ScopingAgent",
    model=DEFAULT_MODEL,
    description="Evaluates candidate's problem scoping and estimation skills from phases 1-2",
    instruction=SCOPING_INSTRUCTION,
    output_key="scoping_result",
    generate_content_config=JSON_RESPONSE_CONFIG,
)

__all__ = ["scoping_agent", "SCOPING_INSTRUCTION"]
