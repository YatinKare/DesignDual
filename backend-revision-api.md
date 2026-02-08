Below is a **v2 agentic backend system** that keeps your original “4 specialists + synthesizer” vibe, but **fully conforms to the new Screen 2 contract** (types, SSE statuses, 4× phase cards, 4× evidence items, rubric breakdown, radar, next attempt plan, transcript highlights, etc.).

I’m keeping it **hackathon-simple** (still mostly ADK workflow agents + state) while adding just enough structure so your `/api/submissions/{id}` payload is always valid.

---

## DesignDuel Backend Agent Architecture v2 (Screen 2 compliant)

### Model selection (unchanged, but now explicit)

Use `gemini-2.5-flash` everywhere (multimodal, fast, cheap). The official stable model id is `gemini-2.5-flash`, and it supports **audio + images** as input. ([Google AI for Developers][1])

---

## 1) Core idea: shift from “dimension-only grading” → “Phase-first grading”

Your new UI contract is explicitly phase-shaped:

* `phase_scores`: exactly **4 entries** (clarify/estimate/design/explain)
* `evidence`: exactly **4 entries**, each containing snapshot URL + timestamped transcript snippets
* `rubric`: multiple rubric labels computed from **phase weights**
* `radar`: aggregate skills (clarity/structure/power/wisdom + optional speed/security)

So the new system should have **phase agents** as first-class citizens, and then a **rubric/radar synthesizer** that composes phase outputs.

---

## 2) Updated ADK orchestration (v2)

### Orchestration diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SequentialAgent: "GradingPipelineV2"                      │
│                                                                              │
│  Step 0 (non-LLM): FastAPI intake → persist → build bundle in session.state  │
│                                                                              │
│  Step 1: ParallelAgent "PhasePanelV2"                                        │
│     ├─ LlmAgent "ClarifyPhaseAgent"   output_key="phase:clarify"             │
│     ├─ LlmAgent "EstimatePhaseAgent"  output_key="phase:estimate"            │
│     ├─ LlmAgent "DesignPhaseAgent"    output_key="phase:design"              │
│     └─ LlmAgent "ExplainPhaseAgent"   output_key="phase:explain"             │
│                                                                              │
│  Step 2: LlmAgent "RubricRadarAgent"   output_key="rubric_radar"             │
│                                                                              │
│  Step 3: LlmAgent "PlanOutlineAgent"   output_key="plan_outline"             │
│                                                                              │
│  Step 4: LlmAgent "FinalAssemblerV2"   output_key="final_report_v2"          │
│                                                                              │
│  Step 5: (optional but recommended) "ContractGuardAgent"                     │
│        validates + fixes counts/schema → output_key="final_report_v2"        │
└──────────────────────────────────────────────────────────────────────────────┘
```

This uses ADK’s **SequentialAgent** and **ParallelAgent** the way the docs intend: sequential orchestration + concurrent sub-tasks. ([Google GitHub][2])

---

## 3) Canonical data contracts (what every agent writes)

### Phase agent output (internal contract)

Each phase agent must output a *single* JSON object like:

```json
{
  "phase": "clarify",
  "score": 0,
  "bullets": ["..."],
  "evidence": {
    "phase": "clarify",
    "snapshot_url": "https://...",
    "transcripts": [{ "timestamp_sec": 12.3, "text": "..." }],
    "noticed": { "strength": "...", "issue": "..." }
  },
  "strengths": [{ "phase": "clarify", "text": "...", "timestamp_sec": 12.3 }],
  "weaknesses": [{ "phase": "clarify", "text": "...", "timestamp_sec": null }],
  "highlights": [{ "phase": "clarify", "timestamp_sec": 12.3, "text": "..." }]
}
```

### Why this matters

If you guarantee this shape from the phase agents, then your `FinalAssemblerV2` can deterministically produce:

* `phase_scores` = [4 items]
* `evidence` = [4 items]
* `strengths/weaknesses/highlights` = merged lists

…and you’ll never fail the “exactly 4 cards” acceptance checks.

---

## 4) Agent responsibilities (v2)

### A) Phase agents (4x, run in parallel)

**Inputs (read from `session.state`):**

* `problem` (prompt + difficulty + rubric_definition)
* `phase_artifacts[phase]` → `{ snapshot_url, transcripts[] }`
* `phase_times`

**Outputs (write via `output_key="phase:<phase>"`):**

* `score` 0..10
* `bullets` (3–6 concise bullets)
* `evidence` (exactly 1 EvidenceItem)
* a few `strengths`, `weaknesses`, and `highlights` (timestamped when possible)

**Prompt pattern (same for each, phase-specific focus):**

* Must grade only that phase
* Must reference transcript timestamps when calling something out
* Must produce JSON only (structured output)

### B) `RubricRadarAgent` (1x)

**Goal:** Compute Screen 2’s rubric + radar in a way that’s explainable.

**Inputs:**

* the 4 phase outputs (`phase:clarify`, `phase:estimate`, `phase:design`, `phase:explain`)
* `problem.rubric_definition` (label + phase_weights)

**Outputs:**

* `rubric[]`: for each rubric label

  * `score` 0..10
  * `status` in {pass, partial, fail}
  * `computed_from` phases (derived from phase_weights keys)
* `radar`: clarity/structure/power/wisdom (+ optional speed/security)
* `overall_score` and `verdict` + a one-paragraph `summary`

**Deterministic scoring recommendation (simple + robust):**

* rubric score = weighted average of relevant phase scores
* status thresholds:

  * `pass` ≥ 8
  * `partial` ≥ 5 and < 8
  * `fail` < 5

(You can tweak thresholds later, but this gives stable UI.)

### C) `PlanOutlineAgent` (1x)

**Goal:** Generate:

* `next_attempt_plan` (top 3 fixes with why + “do_next_time” steps)
* `follow_up_questions` (≥ 3)
* `reference_outline` (sections + bullets)

Inputs: phases + rubric + radar.

### D) `FinalAssemblerV2` (1x)

**Goal:** Produce the exact `SubmissionResultV2` shape.

**Hard requirements enforced here:**

* `phase_scores` has **exactly 4 entries** (one per phase, in fixed order)
* `evidence` has **exactly 4 entries** (one per phase, in fixed order)
* if a phase has no audio: `transcripts: []` and **do not error**
* adds `created_at`, `completed_at`, `submission_id`, `problem`, `phase_times`
* sets `"result_version": 2` for compatibility

### E) `ContractGuardAgent` (optional but worth it)

This is your “never ship invalid JSON” safety net:

* checks counts, missing fields, wrong enum values
* fixes by regenerating only the missing pieces (or normalizing values)

This leverages ADK’s state-first composition model (write to `session.state` keys using output keys). ([Google GitHub][3])

---

## 5) Updated session.state shape (v2)

```json
{
  "problem": {
    "id": "url-shortener",
    "name": "Design a URL Shortener",
    "difficulty": "Easy",
    "prompt": "...",
    "rubric_definition": [
      { "label": "Scalability Plan", "description": "...", "phase_weights": { "design": 0.7, "explain": 0.3 } }
    ]
  },

  "phase_times": { "clarify": 458, "estimate": 524, "design": 910, "explain": 438 },

  "phase_artifacts": {
    "clarify": { "snapshot_url": "...", "transcripts": [ { "timestamp_sec": 0, "text": "..." } ] },
    "estimate": { "snapshot_url": "...", "transcripts": [] },
    "design":   { "snapshot_url": "...", "transcripts": [ ... ] },
    "explain":  { "snapshot_url": "...", "transcripts": [ ... ] }
  },

  "phase:clarify":  { ...PhaseAgentOutput... },
  "phase:estimate": { ...PhaseAgentOutput... },
  "phase:design":   { ...PhaseAgentOutput... },
  "phase:explain":  { ...PhaseAgentOutput... },

  "rubric_radar": { "rubric": [ ... ], "radar": { ... }, "overall_score": 8.0, "verdict": "...", "summary": "..." },

  "plan_outline": { "next_attempt_plan": [ ... ], "follow_up_questions": [ ... ], "reference_outline": { ... } },

  "final_report_v2": { ...SubmissionResultV2..., "result_version": 2 }
}
```

---

## 6) Route integration changes (how FastAPI + ADK cooperate)

### `POST /api/submissions` (intake)

What changes:

1. Validate `problem_id` exists
2. Validate 4 PNGs, non-empty
3. Parse + validate `phase_times` has exactly the 4 keys
4. Persist artifacts → generate `snapshot_url`s (public or signed)
5. Create submission row with `status = queued` then `processing`
6. Return `submission_id` immediately

No ADK changes required here—this is pure backend hygiene.

### Timestamped transcripts (practical hackathon approach)

Your contract expects `[{timestamp_sec, text}]`. If you don’t have Speech-to-Text timestamps:

* split audio into small chunks (e.g., 10–15s)
* transcribe each chunk
* assign the chunk start time as `timestamp_sec`

This gives “good enough” timestamps for UI highlights without adding a whole STT dependency.

---

## 7) SSE v2 (status mapping + persistence)

ADK streams **Events** as the agent runs. Your SSE should map them to your canonical `StreamStatus`. ADK’s event system is explicitly designed for streaming execution progress. ([Google GitHub][4])

### Recommended status sequence

* `queued`
* `processing`
* `clarify`
* `estimate`
* `design`
* `explain`
* `synthesizing`
* `complete` (includes lightweight `{submission_id}` or the full result)
* `failed`

### Implementation pattern (robust + replayable)

* Every time you emit an SSE event, **also insert into `grading_events`**
* When a client reconnects:

  * replay events from DB
  * then continue streaming live

This matches your new “SSE replay/recovery” requirement without complexity.

---

## 8) Storage changes (minimal schema that fits v2 perfectly)

Use exactly what your spec lists; it aligns cleanly with the v2 output:

* `submissions`: `id, problem_id, status, phase_times_json, result_json, created_at, completed_at`
* `submission_artifacts`: `submission_id, phase, canvas_url, audio_url, mime_type`
* `submission_transcripts`: `submission_id, phase, timestamp_sec, text, is_highlight`
* `grading_events`: `submission_id, status, message, created_at`

Your `GET /api/submissions/{id}` should primarily serve `result_json` (the already-assembled `SubmissionResultV2`) and only “re-hydrate” if you choose not to store full result JSON.

---

## 9) Compatibility plan (keep old clients alive)

Do exactly what your spec proposes:

* map old stream statuses:

  * `scoping -> clarify`
  * `tradeoff -> explain`
  * `scale -> estimate` (pick one consistently and stick to it)

And version the payload:

```json
{
  "result_version": 2,
  ...
}
```

---

## 10) What you actually need to rewrite in your original agent prompts

Your old agents were “dimension graders.” Convert them to “phase graders”:

* **ScopingAgent → ClarifyPhaseAgent**
* **ScaleAgent → EstimatePhaseAgent** *(or split scale logic: estimate+design; but keep simple for now)*
* **DesignAgent → DesignPhaseAgent**
* **TradeoffAgent → ExplainPhaseAgent**
* **SynthesisAgent → (RubricRadarAgent + PlanOutlineAgent + FinalAssemblerV2)**

Keep the same magic flavor in SSE messages; it’s purely presentation.

---

If you want, paste your current ADK agent code (even just the agent constructors / prompts), and I’ll rewrite them into **v2 prompt blocks** that enforce:

* strict JSON output
* correct enum values
* guaranteed 4 evidence items / 4 phase cards
* rubric computed_from correctness

[1]: https://ai.google.dev/gemini-api/docs/models "Gemini models  |  Gemini API  |  Google AI for Developers"
[2]: https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/?utm_source=chatgpt.com "Sequential agents - Agent Development Kit"
[3]: https://google.github.io/adk-docs/sessions/state/?utm_source=chatgpt.com "State - Agent Development Kit"
[4]: https://google.github.io/adk-docs/events/?utm_source=chatgpt.com "Events - Agent Development Kit"
