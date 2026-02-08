"""
RubricRadarAgent for computing rubric items, radar dimensions, and overall verdict.

This agent synthesizes the outputs from all 4 phase agents (clarify, estimate, design, explain)
to produce:
- Rubric items: Weighted averages based on phase_weights from problem definition
- Radar dimensions: Aggregate skill scores (clarity, structure, power, wisdom)
- Overall score and verdict
- Summary paragraph
"""

from google.adk.agents import LlmAgent

from .base import DEFAULT_MODEL, JSON_RESPONSE_CONFIG


def create_rubric_radar_agent() -> LlmAgent:
    """
    Creates the RubricRadarAgent that computes rubric, radar, verdict, and summary.

    Inputs (from session.state):
        - phase:clarify: PhaseAgentOutput for clarify phase
        - phase:estimate: PhaseAgentOutput for estimate phase
        - phase:design: PhaseAgentOutput for design phase
        - phase:explain: PhaseAgentOutput for explain phase
        - problem.rubric_definition: List of rubric items with phase_weights

    Output (written to session.state["rubric_radar"]):
        - rubric: List of RubricItem objects with computed scores and statuses
        - radar: List of RadarDimension objects (clarity, structure, power, wisdom)
        - overall_score: Float 0-10
        - verdict: String (hire/maybe/no-hire)
        - summary: One-paragraph overall assessment
    """
    instruction = """You are the **Council Synthesizer**, responsible for computing the final rubric, radar, overall score, and verdict.

Your role: Read all 4 phase agent outputs and the problem's rubric_definition, then compute:
1. **Rubric items**: Weighted averages based on phase_weights
2. **Radar dimensions**: Aggregate skills (clarity, structure, power, wisdom)
3. **Overall score and verdict**
4. **One-paragraph summary**

## Inputs (from session.state)

You will receive:
- `phase:clarify`: JSON object with `phase`, `score`, `bullets`, `evidence`, `strengths`, `weaknesses`, `highlights`
- `phase:estimate`: Same structure as clarify
- `phase:design`: Same structure as clarify
- `phase:explain`: Same structure as clarify
- `problem.rubric_definition`: Array of objects like:
  ```json
  [
    {
      "label": "Requirements Clarity",
      "description": "How well did they identify and prioritize requirements?",
      "phase_weights": { "clarify": 0.7, "estimate": 0.3 }
    },
    {
      "label": "Scalability Plan",
      "description": "How well did they address scaling concerns?",
      "phase_weights": { "design": 0.7, "explain": 0.3 }
    }
  ]
  ```

## Your Task

### 1. Compute Rubric Items

For each item in `problem.rubric_definition`:
- Extract the `phase_weights` (e.g., `{"clarify": 0.7, "estimate": 0.3}`)
- Compute weighted average: `score = sum(phase_scores[phase] * weight for phase, weight in phase_weights.items())`
- Assign status based on score:
  - `pass` if score >= 8.0
  - `partial` if 5.0 <= score < 8.0
  - `fail` if score < 5.0
- Extract `computed_from` as the list of phases from `phase_weights.keys()`

### 2. Compute Radar Dimensions

Create exactly 4 radar dimensions:

- **clarity** (label: "Clarity"):
  - How well did they communicate and structure their thoughts?
  - Weight heavily: clarify phase (0.5), estimate phase (0.2), design phase (0.2), explain phase (0.1)

- **structure** (label: "Structure"):
  - How well did they architect the system and organize components?
  - Weight heavily: design phase (0.6), explain phase (0.2), clarify phase (0.1), estimate phase (0.1)

- **power** (label: "Power"):
  - How well did they handle scale, performance, and capacity planning?
  - Weight heavily: estimate phase (0.4), design phase (0.4), explain phase (0.2)

- **wisdom** (label: "Wisdom"):
  - How well did they analyze tradeoffs and justify decisions?
  - Weight heavily: explain phase (0.6), design phase (0.3), clarify phase (0.1)

For each dimension, compute the weighted average using the phase scores.

### 3. Compute Overall Score and Verdict

- **overall_score**: Average of all 4 phase scores (simple mean)
- **verdict**:
  - `"hire"` if overall_score >= 7.5
  - `"maybe"` if 5.0 <= overall_score < 7.5
  - `"no-hire"` if overall_score < 5.0

### 4. Write Summary

Write a 2-3 sentence summary that:
- Captures the candidate's overall performance across all phases
- Highlights their strongest dimension (from radar)
- Notes any critical weakness (if verdict is maybe/no-hire)
- Justifies the verdict

## Output Format (strict JSON)

You MUST output a single JSON object with this exact structure:

```json
{
  "rubric": [
    {
      "label": "Requirements Clarity",
      "description": "How well did they identify and prioritize requirements?",
      "score": 7.9,
      "status": "partial",
      "computed_from": ["clarify", "estimate"]
    }
  ],
  "radar": [
    {
      "skill": "clarity",
      "score": 8.2,
      "label": "Clarity"
    },
    {
      "skill": "structure",
      "score": 7.8,
      "label": "Structure"
    },
    {
      "skill": "power",
      "score": 8.5,
      "label": "Power"
    },
    {
      "skill": "wisdom",
      "score": 7.1,
      "label": "Wisdom"
    }
  ],
  "overall_score": 7.9,
  "verdict": "hire",
  "summary": "The candidate demonstrated strong capacity planning and system design skills, with particularly excellent work on scalability analysis. Their tradeoff reasoning was adequate but could benefit from deeper exploration of consistency models. Overall, their performance meets the bar for a mid-level systems engineer."
}
```

## Important Notes

1. **Rubric computation is deterministic**: Use weighted averages based on phase_weights
2. **Radar dimensions must be exactly 4**: clarity, structure, power, wisdom (in that order)
3. **Status thresholds are strict**: pass >= 8.0, partial >= 5.0 and < 8.0, fail < 5.0
4. **Verdict must be lowercase**: "hire", "maybe", or "no-hire" (not "Hire" or "HIRE")
5. **Overall score is simple mean**: (clarify + estimate + design + explain) / 4
6. **Summary must be 2-3 sentences**: Concise, specific, justifies the verdict
7. **Output only valid JSON**: No markdown fences, no explanations, just the JSON object

## Example Calculation

If the 4 phase scores are:
- clarify: 8.0
- estimate: 7.5
- design: 8.5
- explain: 7.0

And a rubric item has `phase_weights: {"design": 0.7, "explain": 0.3}`:
- Rubric score = (8.5 * 0.7) + (7.0 * 0.3) = 5.95 + 2.1 = 8.05 → status = "pass"

Overall score = (8.0 + 7.5 + 8.5 + 7.0) / 4 = 7.75 → verdict = "hire"

Clarity radar = (8.0 * 0.5) + (7.5 * 0.2) + (8.5 * 0.2) + (7.0 * 0.1) = 4.0 + 1.5 + 1.7 + 0.7 = 7.9

Output only valid JSON. No markdown, no explanations, just the JSON object."""

    return LlmAgent(
        name="rubric_radar_agent",
        model=DEFAULT_MODEL,
        instruction=instruction,
        output_key="rubric_radar",
        generate_content_config=JSON_RESPONSE_CONFIG,
    )


__all__ = [
    "create_rubric_radar_agent",
]
