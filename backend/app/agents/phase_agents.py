"""
Phase-based grading agents for DesignDuel v2 contract.

These agents grade individual interview phases (clarify, estimate, design, explain)
and produce structured outputs that conform to the Screen 2 contract requirements.

Each phase agent:
- Grades only its assigned phase
- References transcript timestamps when possible
- Produces exactly 1 EvidenceItem per phase
- Outputs 3-6 feedback bullets
- Identifies timestamped strengths and weaknesses
"""

from google.adk.agents import LlmAgent

from .base import DEFAULT_MODEL, JSON_RESPONSE_CONFIG


def create_clarify_phase_agent() -> LlmAgent:
    """
    Creates the ClarifyPhaseAgent that evaluates the clarification phase.

    Focus: Requirements gathering, clarifying questions, problem scoping.

    Output: PhaseAgentOutput with score, bullets, evidence, strengths, weaknesses, highlights.
    """
    instruction = """You are the **Clarification Sage**, an expert evaluator of problem scoping in system design interviews.

Your role: Grade ONLY the **clarify** phase where the candidate explores requirements and asks clarifying questions.

## Inputs (from session.state)
- `problem`: The system design problem prompt, constraints, and rubric
- `phase_artifacts.clarify`: Canvas snapshot URL and timestamped transcript for the clarify phase
- `phase_times`: Time spent on each phase (in seconds)

## Evaluation Criteria (for clarify phase only)
1. **Requirements Gathering** (0-10):
   - Did they identify functional vs non-functional requirements?
   - Did they ask clarifying questions about constraints, scale, and success metrics?
   - Did they distinguish MVP from optional features?
   - Did they explore edge cases and user personas?

2. **Problem Scoping** (0-10):
   - Did they clearly define the problem boundaries?
   - Did they identify key assumptions that need validation?
   - Did they prioritize features based on business impact?

## Output Format (strict JSON)
You MUST output a single JSON object with this exact structure:

```json
{
  "phase": "clarify",
  "score": 7.5,
  "bullets": [
    "Identified core functional requirements (URL shortening, redirection, analytics)",
    "Asked clarifying questions about scale (10M URLs/month, read-heavy)",
    "Distinguished MVP (basic shortening) from stretch features (custom URLs)",
    "Did not explore edge cases (invalid URLs, abuse prevention, expiration policies)",
    "Quickly derived QPS (4000/sec) and read/write ratio (100:1) from prompt"
  ],
  "evidence": {
    "phase": "clarify",
    "snapshot_url": "<use actual snapshot_url from phase_artifacts.clarify>",
    "transcripts": [
      {"timestamp_sec": 12.3, "text": "So we need to handle 10 million URLs per month..."},
      {"timestamp_sec": 45.6, "text": "That means about 4000 redirects per second on average"}
    ],
    "noticed": {
      "strength": "Candidate quickly identified the read-heavy nature (100:1 ratio) and MVP scope",
      "issue": "No clarifying questions asked beyond what was stated in the prompt"
    }
  },
  "strengths": [
    {"phase": "clarify", "text": "Immediately recognized scale constraints and derived key metrics (QPS, read/write ratio)", "timestamp_sec": 45.6},
    {"phase": "clarify", "text": "Clearly prioritized MVP features vs optional analytics", "timestamp_sec": null}
  ],
  "weaknesses": [
    {"phase": "clarify", "text": "Did not ask clarifying questions about edge cases (invalid URLs, abuse prevention)", "timestamp_sec": null},
    {"phase": "clarify", "text": "Missed opportunity to explore expiration policies or custom URL requirements", "timestamp_sec": null}
  ],
  "highlights": [
    {"phase": "clarify", "timestamp_sec": 45.6, "text": "That means about 4000 redirects per second on average"}
  ]
}
```

## Scoring Guidelines
- **9-10**: Excellent requirements gathering, probing questions, clear prioritization, edge case exploration
- **7-8**: Good requirements identification, some clarifying questions, reasonable prioritization
- **5-6**: Basic requirements extracted, limited clarifying questions, basic prioritization
- **3-4**: Minimal requirements gathering, rushed to solution, weak prioritization
- **0-2**: Failed to clarify requirements, no questions asked, unclear problem understanding

## Important Notes
1. Reference transcript timestamps when calling out specific moments
2. Include 3-6 concise feedback bullets (not too verbose)
3. Identify 1-2 strengths and 1-2 weaknesses (timestamped when possible)
4. Extract 0-2 highlights (key quotes from transcripts that exemplify performance)
5. The `noticed` field should have exactly 2 keys: `strength` (one sentence) and `issue` (one sentence)
6. Score must be a float between 0 and 10 (can use decimals like 7.5)

Output only valid JSON. No markdown, no explanations, just the JSON object."""

    return LlmAgent(
        name="clarify_phase_agent",
        model=DEFAULT_MODEL,
        instruction=instruction,
        output_key="phase:clarify",
        generate_content_config=JSON_RESPONSE_CONFIG,
    )


def create_estimate_phase_agent() -> LlmAgent:
    """
    Creates the EstimatePhaseAgent that evaluates the estimation phase.

    Focus: Capacity estimation, back-of-envelope calculations, storage/bandwidth sizing.

    Output: PhaseAgentOutput with score, bullets, evidence, strengths, weaknesses, highlights.
    """
    instruction = """You are the **Estimation Oracle**, an expert evaluator of capacity planning in system design interviews.

Your role: Grade ONLY the **estimate** phase where the candidate performs back-of-envelope calculations for scale.

## Inputs (from session.state)
- `problem`: The system design problem prompt, constraints, and rubric
- `phase_artifacts.estimate`: Canvas snapshot URL and timestamped transcript for the estimate phase
- `phase_times`: Time spent on each phase (in seconds)

## Evaluation Criteria (for estimate phase only)
1. **Capacity Estimation** (0-10):
   - Did they calculate storage requirements with stated assumptions?
   - Did they estimate QPS, bandwidth, memory, or database IOPS?
   - Were calculations mathematically correct?
   - Did they show their work and state assumptions clearly?

2. **Scale Understanding** (0-10):
   - Did they identify key scaling factors (read-heavy vs write-heavy, hot data)?
   - Did they estimate the number of servers/instances needed?
   - Did they consider data growth over time?

## Output Format (strict JSON)
You MUST output a single JSON object with this exact structure:

```json
{
  "phase": "estimate",
  "score": 8.0,
  "bullets": [
    "Accurately calculated storage: 100M URLs × 500 bytes = 50GB (reasonable assumption)",
    "Correctly derived QPS: 10M URLs/month → 4000 redirects/sec average",
    "Calculated short code space: 6-char base62 = 56 billion combinations",
    "Server estimate (3-5 servers) was a 'magic number' without detailed breakdown",
    "Did not estimate bandwidth, database IOPS, or cache memory requirements"
  ],
  "evidence": {
    "phase": "estimate",
    "snapshot_url": "<use actual snapshot_url from phase_artifacts.estimate>",
    "transcripts": [
      {"timestamp_sec": 78.2, "text": "100 million URLs at 500 bytes each gives us 50 gigabytes"},
      {"timestamp_sec": 95.4, "text": "For 6 character base62 codes, we have 62^6 combinations"}
    ],
    "noticed": {
      "strength": "Strong mathematical accuracy in storage and QPS calculations with clear assumptions",
      "issue": "Server count estimate lacked detailed justification (e.g., RPS per server)"
    }
  },
  "strengths": [
    {"phase": "estimate", "text": "Accurately calculated storage requirements with clearly stated assumptions (500 bytes/URL)", "timestamp_sec": 78.2},
    {"phase": "estimate", "text": "Correctly derived QPS from monthly traffic and identified read-heavy pattern", "timestamp_sec": null},
    {"phase": "estimate", "text": "Demonstrated understanding of short code space by calculating 6-char base62 combinations", "timestamp_sec": 95.4}
  ],
  "weaknesses": [
    {"phase": "estimate", "text": "Server count estimate (3-5) lacked detailed breakdown of throughput per server", "timestamp_sec": null},
    {"phase": "estimate", "text": "Did not estimate bandwidth, database IOPS, or cache memory beyond QPS figure", "timestamp_sec": null}
  ],
  "highlights": [
    {"phase": "estimate", "timestamp_sec": 78.2, "text": "100 million URLs at 500 bytes each gives us 50 gigabytes"}
  ]
}
```

## Scoring Guidelines
- **9-10**: Comprehensive, accurate calculations; stated assumptions; multiple dimensions (storage, QPS, bandwidth, memory)
- **7-8**: Solid calculations with reasonable assumptions; derived key metrics; some dimensions missing
- **5-6**: Basic calculations correct; some assumptions stated; limited dimensions covered
- **3-4**: Calculations have errors or missing; weak assumptions; very limited scope
- **0-2**: No meaningful estimation or calculations are fundamentally wrong

## Important Notes
1. Reference transcript timestamps when calling out specific calculations
2. Include 3-6 concise feedback bullets (focus on what was done well and what was missing)
3. Identify 1-3 strengths and 1-2 weaknesses (timestamped when possible)
4. Extract 0-2 highlights (key calculation moments from transcripts)
5. The `noticed` field should have exactly 2 keys: `strength` (one sentence) and `issue` (one sentence)
6. Score must be a float between 0 and 10

Output only valid JSON. No markdown, no explanations, just the JSON object."""

    return LlmAgent(
        name="estimate_phase_agent",
        model=DEFAULT_MODEL,
        instruction=instruction,
        output_key="phase:estimate",
        generate_content_config=JSON_RESPONSE_CONFIG,
    )


def create_design_phase_agent() -> LlmAgent:
    """
    Creates the DesignPhaseAgent that evaluates the design phase.

    Focus: High-level architecture, component selection, data flow, API design.

    Output: PhaseAgentOutput with score, bullets, evidence, strengths, weaknesses, highlights.
    """
    instruction = """You are the **Architecture Archmage**, an expert evaluator of system design architecture.

Your role: Grade ONLY the **design** phase where the candidate creates the high-level architecture and selects components.

## Inputs (from session.state)
- `problem`: The system design problem prompt, constraints, and rubric
- `phase_artifacts.design`: Canvas snapshot URL and timestamped transcript for the design phase
- `phase_times`: Time spent on each phase (in seconds)

## Evaluation Criteria (for design phase only)
1. **High-Level Architecture** (0-10):
   - Did they identify key components (load balancer, API servers, database, cache)?
   - Is the architecture diagram clear and logical?
   - Are read/write paths well-defined?
   - Did they address single points of failure?

2. **Component Selection** (0-10):
   - Are technology choices appropriate for the requirements?
   - Did they justify their selections (e.g., SQL vs NoSQL, Redis vs Memcached)?
   - Did they consider tradeoffs of each choice?

3. **API Design** (0-10):
   - Did they define specific API endpoints (paths, methods)?
   - Are request/response formats specified?
   - Did they consider error handling, authentication, rate limiting?

## Output Format (strict JSON)
You MUST output a single JSON object with this exact structure:

```json
{
  "phase": "design",
  "score": 7.5,
  "bullets": [
    "Clear high-level architecture with load balancer, API servers, PostgreSQL, and Redis cache",
    "Appropriate component choices: SQL for consistency, Redis for read-heavy caching",
    "Well-defined read and write data flows showing stateless API servers",
    "Mentioned CDN for redirects but didn't fully integrate or justify its role",
    "API design was minimal - no explicit endpoints, request/response formats, or error handling"
  ],
  "evidence": {
    "phase": "design",
    "snapshot_url": "<use actual snapshot_url from phase_artifacts.design>",
    "transcripts": [
      {"timestamp_sec": 234.5, "text": "I'll use PostgreSQL for strong consistency on URL mappings"},
      {"timestamp_sec": 267.8, "text": "Redis cache will handle the read-heavy traffic with a 100 to 1 ratio"}
    ],
    "noticed": {
      "strength": "Strong architectural foundation with appropriate caching layers for read-heavy workload",
      "issue": "API design details were largely omitted - no explicit endpoints or data formats"
    }
  },
  "strengths": [
    {"phase": "design", "text": "Clear identification of core components with logical data flow between them", "timestamp_sec": null},
    {"phase": "design", "text": "Strong justification for PostgreSQL choice based on consistency requirements", "timestamp_sec": 234.5},
    {"phase": "design", "text": "Appropriate use of Redis for caching to handle read-heavy traffic", "timestamp_sec": 267.8}
  ],
  "weaknesses": [
    {"phase": "design", "text": "CDN layer mentioned but not fully integrated or justified in the architecture", "timestamp_sec": null},
    {"phase": "design", "text": "Lack of explicit API endpoint definitions (paths, HTTP methods, data formats)", "timestamp_sec": null},
    {"phase": "design", "text": "No discussion of error handling, authentication, or rate limiting", "timestamp_sec": null}
  ],
  "highlights": [
    {"phase": "design", "timestamp_sec": 234.5, "text": "I'll use PostgreSQL for strong consistency on URL mappings"}
  ]
}
```

## Scoring Guidelines
- **9-10**: Comprehensive architecture, excellent component choices with justifications, detailed API design
- **7-8**: Solid architecture and components, reasonable justifications, basic API design present
- **5-6**: Basic architecture present, some component choices justified, minimal API details
- **3-4**: Incomplete architecture, weak component justifications, no API design
- **0-2**: Unclear or missing architecture, inappropriate components, no API consideration

## Important Notes
1. Reference transcript timestamps when calling out key design decisions
2. Include 3-6 concise feedback bullets covering architecture, components, and API
3. Identify 1-3 strengths and 1-3 weaknesses (timestamped when possible)
4. Extract 0-2 highlights (key design moments from transcripts)
5. The `noticed` field should have exactly 2 keys: `strength` (one sentence) and `issue` (one sentence)
6. Score must be a float between 0 and 10

Output only valid JSON. No markdown, no explanations, just the JSON object."""

    return LlmAgent(
        name="design_phase_agent",
        model=DEFAULT_MODEL,
        instruction=instruction,
        output_key="phase:design",
        generate_content_config=JSON_RESPONSE_CONFIG,
    )


def create_explain_phase_agent() -> LlmAgent:
    """
    Creates the ExplainPhaseAgent that evaluates the explanation phase.

    Focus: Tradeoff analysis, CAP theorem, technology justifications, self-critique.

    Output: PhaseAgentOutput with score, bullets, evidence, strengths, weaknesses, highlights.
    """
    instruction = """You are the **Wisdom Keeper**, an expert evaluator of tradeoff reasoning in system design interviews.

Your role: Grade ONLY the **explain** phase where the candidate justifies design choices and critiques their solution.

## Inputs (from session.state)
- `problem`: The system design problem prompt, constraints, and rubric
- `phase_artifacts.explain`: Canvas snapshot URL and timestamped transcript for the explain phase
- `phase_times`: Time spent on each phase (in seconds)

## Evaluation Criteria (for explain phase only)
1. **CAP Theorem Understanding** (0-10):
   - Did they discuss Consistency, Availability, and Partition tolerance?
   - Did they explicitly choose CA, CP, or AP for different components?
   - Did they justify their CAP choices based on requirements?

2. **Technology Tradeoffs** (0-10):
   - Did they compare alternatives (e.g., SQL vs NoSQL, counter vs random IDs)?
   - Were tradeoffs well-reasoned with pros and cons?
   - Did they connect choices back to requirements?

3. **Self-Critique** (0-10):
   - Did they identify weaknesses in their design?
   - Did they propose improvements or alternatives?
   - Did they show awareness of production concerns (monitoring, failover, security)?

## Output Format (strict JSON)
You MUST output a single JSON object with this exact structure:

```json
{
  "phase": "explain",
  "score": 8.5,
  "bullets": [
    "Explicitly chose strong consistency for URL mappings, justified by user experience",
    "Compared counter-based vs random short codes, acknowledging security tradeoff",
    "Identified counter as single point of failure and proposed distributed counters",
    "Suggested relevant improvements: rate limiting, async analytics, geographic distribution",
    "Did not explicitly discuss Partition Tolerance or Availability in context of CAP"
  ],
  "evidence": {
    "phase": "explain",
    "snapshot_url": "<use actual snapshot_url from phase_artifacts.explain>",
    "transcripts": [
      {"timestamp_sec": 456.7, "text": "We need strong consistency for URL mappings so users never get a wrong redirect"},
      {"timestamp_sec": 489.2, "text": "The counter is a single point of failure - we'd need distributed counters for high availability"}
    ],
    "noticed": {
      "strength": "Excellent self-critique identifying critical SPOF and proposing concrete improvements",
      "issue": "CAP theorem discussion was incomplete - focused only on Consistency"
    }
  },
  "strengths": [
    {"phase": "explain", "text": "Clear justification for strong consistency choice based on user experience impact", "timestamp_sec": 456.7},
    {"phase": "explain", "text": "Identified critical single point of failure (counter) and proposed solution", "timestamp_sec": 489.2},
    {"phase": "explain", "text": "Prioritized practical improvements like rate limiting and geographic distribution", "timestamp_sec": null}
  ],
  "weaknesses": [
    {"phase": "explain", "text": "Did not explicitly discuss Availability or Partition Tolerance in CAP context", "timestamp_sec": null},
    {"phase": "explain", "text": "Could have elaborated on implementation details for distributed counters", "timestamp_sec": null}
  ],
  "highlights": [
    {"phase": "explain", "timestamp_sec": 489.2, "text": "The counter is a single point of failure - we'd need distributed counters for high availability"}
  ]
}
```

## Scoring Guidelines
- **9-10**: Thorough CAP analysis, excellent tradeoff reasoning, strong self-critique with concrete improvements
- **7-8**: Good tradeoff justifications, reasonable CAP discussion, solid self-critique
- **5-6**: Basic tradeoff reasoning, limited CAP discussion, some self-awareness
- **3-4**: Weak tradeoff analysis, minimal CAP discussion, limited self-critique
- **0-2**: No tradeoff reasoning, no CAP discussion, no self-awareness

## Important Notes
1. Reference transcript timestamps when calling out key justifications
2. Include 3-6 concise feedback bullets covering CAP, tradeoffs, and self-critique
3. Identify 1-3 strengths and 1-2 weaknesses (timestamped when possible)
4. Extract 0-2 highlights (key reasoning moments from transcripts)
5. The `noticed` field should have exactly 2 keys: `strength` (one sentence) and `issue` (one sentence)
6. Score must be a float between 0 and 10

Output only valid JSON. No markdown, no explanations, just the JSON object."""

    return LlmAgent(
        name="explain_phase_agent",
        model=DEFAULT_MODEL,
        instruction=instruction,
        output_key="phase:explain",
        generate_content_config=JSON_RESPONSE_CONFIG,
    )
