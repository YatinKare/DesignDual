## DesignDuel Backend Agent Architecture

### Model Selection

**Use `gemini-2.5-flash` everywhere** — it's fast, multimodal (handles images + text), and cost-effective for a hackathon.

---

### Agent Orchestration Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SequentialAgent: "GradingPipeline"                  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                  ParallelAgent: "EvaluatorPanel"                    │   │
│   │                                                                     │   │
│   │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │   │
│   │   │   Scoping   │ │   Design    │ │    Scale    │ │   Tradeoff   │  │   │
│   │   │   Agent     │ │   Agent     │ │    Agent    │ │    Agent     │  │   │
│   │   │             │ │             │ │             │ │              │  │   │
│   │   │ output_key: │ │ output_key: │ │ output_key: │ │ output_key:  │  │   │
│   │   │ "scoping"   │ │ "design"    │ │ "scale"     │ │ "tradeoff"   │  │   │
│   │   └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │              LlmAgent: "SynthesisAgent"                             │   │
│   │                                                                     │   │
│   │   Reads: {scoping}, {design}, {scale}, {tradeoff} from state        │   │
│   │   Outputs: Final grading report JSON                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Agent Responsibilities

| Agent | Focus Phases | Input | Output Key | Evaluates |
|-------|-------------|-------|------------|-----------|
| **ScopingAgent** | Phase 1 (Clarify) + Phase 2 (Estimate) | Canvas snapshots 1-2, transcripts 1-2 | `scoping_result` | Problem scoping, clarifying questions, estimation accuracy |
| **DesignAgent** | Phase 3 (Design) | Canvas snapshot 3, transcript 3 | `design_result` | Architecture soundness, component selection, diagram clarity |
| **ScaleAgent** | All phases (cross-cutting) | All 4 snapshots + transcripts | `scale_result` | Does design match estimates? Bottlenecks? Caching/partitioning? |
| **TradeoffAgent** | Phase 4 (Explain) + Phase 3 context | Snapshots 3-4, transcripts 3-4 | `tradeoff_result` | Justification of choices, CAP reasoning, improvements mentioned |
| **SynthesisAgent** | — | All 4 agent outputs from state | Final JSON report | Combines scores, generates overall verdict |

---

### API Routes (Minimal for Hackathon)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Routes                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  GET   /api/problems                    → List all problems                │
│  GET   /api/problems/{id}               → Problem details + rubric         │
│                                                                            │
│  POST  /api/submissions                 → Submit interview for grading     │
│        Content-Type: multipart/form-data                                   │
│        Body:                                                               │
│          - problem_id: string                                              │
│          - canvas_clarify: file (PNG)                                      │
│          - canvas_estimate: file (PNG)                                     │
│          - canvas_design: file (PNG)                                       │
│          - canvas_explain: file (PNG)                                      │
│          - audio_clarify: file (webm) | null                               │
│          - audio_estimate: file (webm) | null                              │
│          - audio_design: file (webm) | null                                │
│          - audio_explain: file (webm) | null                               │
│          - phase_times: JSON string                                        │
│        Returns: { submission_id: string }                                  │
│                                                                            │
│  GET   /api/submissions/{id}/stream     → SSE for grading progress         │
│        Returns: Server-Sent Events                                         │
│          data: { status: "scoping" | "design" | "scale" | "tradeoff" |     │
│                          "synthesizing" | "complete",                      │
│                  message: string,                                          │
│                  result?: GradingReport }                                  │
│                                                                            │
│  GET   /api/submissions/{id}            → Get final grading result         │
│                                                                            │
│  GET   /api/dashboard                   → User's score history (stretch)   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

### Data Flow Diagram

```
┌─────────────────────┐
│      Frontend       │
│  (SvelteKit)        │
└─────────┬───────────┘
          │
          │ POST /api/submissions
          │ (4 PNGs + 4 audio files)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
│                                                                  │
│  1. Save files to disk/memory                                    │
│  2. Transcribe audio → text (Gemini API, parallel)               │
│  3. Store submission in SQLite                                   │
│  4. Return submission_id immediately                             │
│                                                                  │
│  Background Task:                                                │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  5. Build submission bundle:                               │  │
│  │     {                                                      │  │
│  │       problem: { prompt, constraints, rubric_hints },      │  │
│  │       phases: [                                            │  │
│  │         { phase: "clarify", canvas: <base64>, transcript } │  │
│  │         { phase: "estimate", canvas: <base64>, transcript }│  │
│  │         { phase: "design", canvas: <base64>, transcript }  │  │
│  │         { phase: "explain", canvas: <base64>, transcript } │  │
│  │       ]                                                    │  │
│  │     }                                                      │  │
│  │                                                            │  │
│  │  6. Set bundle in ADK session state                        │  │
│  │                                                            │  │
│  │  7. Run ADK GradingPipeline agent                          │  │
│  │     └── ParallelAgent (4 evaluators)                       │  │
│  │         └── SynthesisAgent                                 │  │
│  │                                                            │  │
│  │  8. Stream events via SSE to frontend                      │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
          │
          │ SSE: /api/submissions/{id}/stream
          ▼
┌─────────────────────┐
│      Frontend       │
│  Grading animation  │
│  Score reveal       │
└─────────────────────┘
```

---

### SSE Event Sequence (for magic theme)

```
Event 1: { status: "started",     message: "Your spell has been submitted to the Council..." }
Event 2: { status: "scoping",     message: "The Scoping Oracle examines your preparations..." }
Event 3: { status: "design",      message: "The Architecture Archmage studies your conjuration..." }
Event 4: { status: "scale",       message: "The Scale Sorcerer tests under immense pressure..." }
Event 5: { status: "tradeoff",    message: "The Wisdom Keeper weighs your reasoning..." }
Event 6: { status: "synthesizing", message: "The Council deliberates..." }
Event 7: { status: "complete",    message: "The verdict is ready.", result: {...} }
```

---

### Grading Report Structure (Output)

```
{
  "overall_score": 7.5,
  "verdict": "Hire",
  "dimensions": {
    "scoping": { "score": 8, "feedback": "...", "strengths": [...], "weaknesses": [...] },
    "design":  { "score": 7, "feedback": "...", "strengths": [...], "weaknesses": [...] },
    "scale":   { "score": 7, "feedback": "...", "strengths": [...], "weaknesses": [...] },
    "tradeoff": { "score": 6, "feedback": "...", "strengths": [...], "weaknesses": [...] }
  },
  "top_improvements": [
    "Add a caching layer for hot data",
    "Discuss consistency model for playlist metadata",
    "Include failover strategy for CDN"
  ],
  "phase_observations": {
    "clarify": "Good scoping of read-heavy workload...",
    "estimate": "Calculations were in the right ballpark...",
    "design": "Clean separation of concerns...",
    "explain": "Limited discussion of tradeoffs..."
  }
}
```

---

### Key Simplifications for Hackathon

| What we simplified | Why |
|--------------------|-----|
| **No separate orchestrator agent** | ADK's `ParallelAgent` + `SequentialAgent` handles orchestration automatically |
| **Single model everywhere** | `gemini-2.5-flash` is fast enough and multimodal |
| **State-based communication** | Agents write to `output_key`, synthesis reads from state — no complex message passing |
| **SQLite for storage** | Zero setup, file-based, perfect for demo |
| **Transcription via Gemini** | Stay in one ecosystem, Gemini handles audio natively |
| **No real-time diagram analysis** | Only grade at submission time, not while drawing |

---

### ADK Session State Shape

```
{
  // Input (set by FastAPI before running agent)
  "problem": { ... },
  "phases": [ ... ],
  "phase_times": { ... },
  
  // Output (set by agents via output_key)
  "scoping_result": { score, feedback, ... },
  "design_result": { score, feedback, ... },
  "scale_result": { score, feedback, ... },
  "tradeoff_result": { score, feedback, ... },
  
  // Final (set by SynthesisAgent)
  "final_report": { overall_score, verdict, dimensions, ... }
}
```

---

### Integration Pattern: FastAPI + ADK
Architecture rule: routes delegate all business/data logic to services (routes stay thin).

Instead of using ADK's built-in API server, wrap ADK's `Runner` in your own FastAPI app for more control:

```
FastAPI App
├── /api/problems/* (your routes, SQLite queries)
├── /api/submissions (your routes, file handling)
└── /api/submissions/{id}/stream
    └── Creates ADK Runner
    └── Creates Session with input state
    └── Iterates runner.run_async() events
    └── Yields SSE events to client
```

This gives you control over file uploads, transcription, and SSE formatting while letting ADK handle the multi-agent orchestration.

---

### Summary

**What makes this "Best Use of Gemini API" worthy:**

1. **Multi-agent via ADK** — 4 parallel specialists + 1 synthesizer
2. **Multimodal input** — Images (canvas PNGs) + Audio transcripts per phase
3. **Temporal context** — Agents see the *evolution* across 4 phases, not just final state
4. **Parallel evaluation** — All 4 specialists run concurrently via `ParallelAgent`
5. **Structured output** — Rubric-based scoring with specific feedback
