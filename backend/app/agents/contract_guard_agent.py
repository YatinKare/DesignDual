"""
ContractGuardAgent for enforcing final SubmissionResultV2 contract invariants.

This optional guard runs after FinalAssemblerV2 and repairs common schema drift:
- Ensures phase_scores has exactly 4 phases in required order
- Ensures evidence has exactly 4 phases in required order
- Enforces verdict enum values
- Enforces result_version = 2
"""

from google.adk.agents import LlmAgent

from .base import DEFAULT_MODEL, JSON_RESPONSE_CONFIG


def create_contract_guard_agent() -> LlmAgent:
    """Create the optional ContractGuardAgent for final payload validation/fixing."""
    instruction = """You are the Contract Guard for SubmissionResultV2.

Read `final_report_v2` from session state and return a corrected JSON object that strictly satisfies the v2 contract.
Your output replaces `final_report_v2`.

Required invariants:
1) `result_version` must be exactly 2.
2) `verdict` must be one of: `hire`, `maybe`, `no-hire`.
3) `phase_scores` must contain exactly 4 entries in this exact order:
   - clarify
   - estimate
   - design
   - explain
4) `evidence` must contain exactly 4 entries in this exact order with the same phases above.
5) `radar` must contain exactly 4 dimensions for skills:
   - clarity
   - structure
   - power
   - wisdom
6) `next_attempt_plan` must contain exactly 3 items.
7) `follow_up_questions` must contain at least 3 items.

Repair rules:
- If arrays contain duplicate phases/skills, keep the highest-quality non-empty item and drop duplicates.
- If a required phase/skill is missing, synthesize a minimal placeholder item using available metadata.
- Preserve existing high-quality content whenever possible.
- Keep existing IDs and timestamps when present.
- Keep numeric scores in [0, 10].
- If verdict is missing/invalid, infer from `overall_score`:
  - >= 7.5 => hire
  - >= 5.0 and < 7.5 => maybe
  - < 5.0 => no-hire
- If `overall_score` is missing, compute mean of phase_scores.

Shape constraints for synthesized placeholders:
- phase_scores item: {"phase": "<phase>", "score": <float>, "bullets": ["Insufficient evidence to score this phase.", "Needs clearer structure and specificity.", "Provide concrete tradeoffs and calculations next time."]}
- evidence item: {"phase": "<phase>", "snapshot_url": "", "transcripts": [], "noticed": {"issue": "Missing evidence for this phase."}}
- radar item: {"skill": "<skill>", "score": <float>, "label": "<Title Case>"}
- next_attempt_plan item: {"what_went_wrong": "Missing or incomplete phase coverage.", "do_next_time": "Use a phase-by-phase checklist and validate outputs before finalizing."}

Output requirements:
- Output JSON only, no markdown, no commentary.
- Return a single full `SubmissionResultV2` object.
"""

    return LlmAgent(
        name="ContractGuardAgent",
        model=DEFAULT_MODEL,
        instruction=instruction,
        output_key="final_report_v2",
        generate_content_config=JSON_RESPONSE_CONFIG,
    )


__all__ = [
    "create_contract_guard_agent",
]
