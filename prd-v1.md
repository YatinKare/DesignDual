# Product Requirements Document: DesignDuel

## 🧙‍♂️ *"Where System Design Meets Magic"*

Scope: For a hackathon where we are trying to get the: Best Use of Gemini API award.

---

## 1. Overview

**DesignDuel** is a "LeetCode for System Design" that simulates a real system design interview. Users progress through **timed phases** — scoping the problem, estimating scale, designing the architecture, and explaining their choices — using an **Excalidraw whiteboard and voice** throughout. A panel of Gemini-powered agents then grades the full interview.

---

## 4. Core Features

### 4.1 Problem Browser

Curated system design problems:

- **Prompt** (e.g., "Design a music streaming service like Spotify")
- **Difficulty**: Apprentice 🧹 → Sorcerer 🔮 → Archmage 🧙
- **Focus tags**: scalability, caching, consistency, etc.
- **Estimated time**: 30 / 45 min

### 4.2 Phased Interview Flow

The interview is broken into **4 timed phases** that mirror a real interview. Every phase uses the **same workspace** — an Excalidraw canvas and an optional voice recorder. The only things that change between phases are the instructions and the timer.

A persistent top bar shows phase progress:

```
[● Clarify - 4:32] [ Estimate ] [ Design ] [ Explain ]
```

Phases auto-advance on timer expiry. Users can manually advance early. **Phases are soft** — the canvas persists across all phases (users build on their previous work), and users can go back if needed.

---

#### Phase 1: Clarification (5 min)

> *"Use these 5 minutes to clarify any questions you have. Talk through your assumptions and scope the problem — what are the key features? What scale are we talking about? Use the whiteboard to jot down notes if it helps."*

The user talks out loud and/or writes on the whiteboard to scope the problem:
- What features are in scope?
- How many users?
- Read vs. write ratio?
- Geographic distribution?
- Any specific constraints?

The canvas and voice are both available. Some users will just talk. Some will jot bullet points on the canvas. Both are fine.

**At phase transition**: The system captures a canvas snapshot (PNG) and the voice recording from this phase.

---

#### Phase 2: Estimation (5 min)

> *"Use these 5 minutes to do back-of-envelope calculations. Estimate storage, throughput, bandwidth — whatever matters for this problem. Work through the math out loud and/or on the whiteboard."*

The user does napkin math:
- 100M songs × 5MB = 500TB
- 3× replication = 1.5PB
- 100M DAU × 10 songs/day = ~12K streams/sec

Again — talk, write on the whiteboard, or both. The canvas is the same one from Phase 1, so any notes from clarification are still there.

**At phase transition**: Canvas snapshot + voice recording captured.

---

#### Phase 3: Design (20 min)

> *"This is the main event. Draw your system architecture on the whiteboard. Use the component library to drag in common building blocks. Label your connections and data flows."*

The user draws their architecture on Excalidraw:
- Drag components from the pre-loaded system design library (Load Balancer, DB, Cache, Queue, CDN, etc.)
- Draw arrows and label connections (HTTP, gRPC, WebSocket, etc.)
- Organize the diagram clearly

The problem prompt and any notes from earlier phases are visible on the canvas. Voice is available throughout if the user wants to narrate while drawing.

**At phase transition**: Canvas snapshot + voice recording captured.

---

#### Phase 4: Explain (Optional, max 5 min)

> *"Walk through your design. Explain your key decisions, tradeoffs, and what you'd improve with more time. This phase is optional — skip it if your diagram speaks for itself."*

The user talks through their finished design. This is the "sell" phase — justifying choices, acknowledging tradeoffs, identifying bottlenecks.

- **Explicitly optional** — "Skip & Submit" is prominently shown
- Max 5 minutes with visible countdown
- The canvas is still interactive (users might annotate while explaining)

**At submission**: Final canvas snapshot + voice recording (if any) captured.

---

#### What Gets Captured Per Phase

At each phase transition, the system automatically snapshots:

| Phase | Canvas Snapshot (PNG) | Voice Recording |
|-------|-----------------------|-----------------|
| Clarify | Notes, scoping jots | Assumptions, scope discussion |
| Estimate | Math, calculations | Verbal estimation walkthrough |
| Design | Full architecture diagram | Narration while drawing (if any) |
| Explain | Final annotated diagram | Design walkthrough (optional) |

This gives the grading agents **temporal context** — they can see how the design evolved across phases, not just the final state.

### 4.3 AI Grading System (The Magic ✨)

A multi-agent pipeline built on Google ADK. Because every phase uses the same canvas + voice modality, the agents receive a **sequence of snapshots and transcripts** that tell the story of the full interview.

Refer to prd-agents-v1.md for the full architecture.

#### Grading Output

Each submission receives:

- **Overall score**: 1–10 mapped to interview outcomes (Strong No Hire → Strong Hire)
- **Dimension scores**: 4 specialist scores on a radar chart
- **Visible rubric**:
  ```
  ✓ Problem scoping & clarification     8/10
  ✓ Back-of-envelope estimation          7/10
  ✓ Architecture & diagram quality       6/10
  ✓ Scalability awareness                7/10
  ✓ Tradeoff reasoning                   5/10
  ```
- **Strengths & weaknesses**: Specific references to what was drawn/said in each phase
- **Top 3 improvements**: Ranked by impact
- **Sample solution outline**: Brief reference for the weakest areas

### 4.4 Results Dashboard

- Score history over time (line chart)
- Dimension radar chart
- Problem completion tracker
- Per-problem best scores

---

## 5. Technical Architecture

### 5.1 Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | SvelteKit | SSR + client-side interactivity, great DX |
| **Canvas** | Excalidraw (React, iframe) | Industry-standard whiteboard, exports PNG + JSON |
| **Audio** | MediaRecorder API | Browser-native, produces webm |
| **Backend** | FastAPI (Python) | Native Google ADK ecosystem, async |
| **AI/Agents** | Google ADK + Gemini 2.0 Flash | Multi-agent orchestration, multimodal input |
| **Transcription** | Gemini API (audio input) | Keeps everything in Gemini ecosystem |
| **Python Tooling** | `uv` | Fast deps and venv |
| **Database** | SQLite (`aiosqlite`) | Lightweight for hackathon |
| **Styling** | Tailwind CSS | Rapid UI dev |

### 5.2 API Endpoints

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

### 5.3 End-to-End Data Flow

```
Phase 1–4: User draws + talks on the same persistent canvas
  └── At each phase transition: snapshot PNG + save audio clip
        │
        ▼
User clicks "Submit for Grading"
        │
        ▼
Frontend bundles:
  • 4 canvas snapshots (PNG per phase)
  • Up to 4 audio clips (webm, any may be null)
  • Final Excalidraw JSON
  • Phase timing data
        │
        ▼
POST /api/submissions (multipart)
        │
        ▼
FastAPI:
  ├── Save all artifacts
  ├── Transcribe each audio clip via Gemini API (parallel)
  ├── Store submission in SQLite
  └── Trigger ADK orchestrator with full bundle
        │
        ▼
Orchestrator → 4 specialist agents (parallel)
  Each receives: all snapshots + all transcripts + problem context
  Each focuses on its relevant phases
        │
        ▼
Results → Feedback Synthesis Agent → unified report
        │
        ▼
Report saved → SSE pushes completion → SvelteKit renders results
```

---

## 6. UGAHacks "Magic" Theme — Full Creative Direction

The magic theme isn't a skin — it's the narrative frame for the entire product experience. The concept: **you are an aspiring wizard submitting your architectural spells to the Archmage Council for evaluation.** System design *is* spellcraft — you're combining components (ingredients), managing data flows (energy channels), and handling failure modes (counterspells). The metaphor maps naturally.

### Visual Identity

- **Color palette**: Deep indigo (`#1a1135`) background, gold accents (`#d4a843`), purple highlights (`#8b5cf6`), parchment cream for text panels (`#f5f0e8`)
- **Typography**: A serif display font for headings (e.g., Playfair Display) paired with a clean sans-serif for body (Inter). Evokes "ancient tome meets modern interface"
- **Texture**: Subtle noise/grain overlay on the background. Faint constellation pattern. No heavy gradients — keep it elegant, not gaudy
- **Iconography**: Minimal line icons with a magical twist — a wand for the cursor, a crystal ball for the timer, a scroll for the problem prompt

### Phase Theming

Each phase has a distinct magical identity, reinforced by a small icon, color accent, and flavor text:

| Phase | Magic Name | Icon | Accent Color | Flavor |
|-------|-----------|------|-------------|--------|
| Clarify | **Scrying** | 🔮 Crystal ball | Soft blue | *"Peer into the mist. What do you see?"* |
| Estimate | **Divination** | ✦ Star chart | Silver | *"Read the numbers. What do the stars foretell?"* |
| Design | **Conjuration** | ⚡ Lightning | Purple | *"Shape your creation. Bring it to life."* |
| Explain | **Incantation** | 🗣️ Sound wave | Gold | *"Speak the words of power. Or let your work speak for itself."* |

The phase bar transitions smoothly between these color accents as the user advances.

### Grading Experience

The grading wait (while agents process) is the **highest-impact moment** for theme immersion:

**SSE status messages cycle through:**
1. *"Your spell has been submitted to the Council..."* (initial)
2. *"The Scoping Oracle examines your preparations..."* (Scoping Agent working)
3. *"The Architecture Archmage studies your conjuration..."* (Design Agent working)
4. *"The Scale Sorcerer tests your spell under immense pressure..."* (Scale Agent working)
5. *"The Wisdom Keeper weighs your reasoning..."* (Tradeoff Agent working)
6. *"The Council deliberates..."* (Feedback Synthesis working)
7. *"The verdict is ready."* (Complete)

Each message appears with a fade-in and a subtle glow animation. A looping particle effect (floating embers/sparks) plays during the wait.

**Score reveal**: The overall score appears with a dramatic number counter animation (0 → final score), accompanied by a burst of particles. The color of the burst maps to the score tier:
- 1–3: Red mist (No Hire)
- 4–5: Orange flame (Lean No Hire)
- 6–7: Blue sparks (Lean Hire)
- 8–9: Purple lightning (Hire)
- 10: Gold explosion (Strong Hire)

### Radar Chart

The 4 dimensions on the radar chart are labeled with their magical names:

- **Clarity** (Scoping Agent score) — top
- **Structure** (Design Agent score) — right
- **Power** (Scale Agent score) — bottom
- **Wisdom** (Tradeoff Agent score) — left

The chart renders with a glowing fill effect — the area expands from center with an easing animation on page load.

### Problem Cards

Each problem card in the browser has:
- A difficulty badge styled as a magical rank insignia (Apprentice 🧹 = simple badge, Archmage 🧙 = ornate with glow)
- A subtle animated shimmer on hover
- Tags displayed as "spell components" (e.g., `⚗️ caching`, `🔗 consistency`, `📡 CDN`)

### Sound Design (Stretch Goal)

If time allows, subtle audio cues:
- Soft chime on phase transition
- Low hum during grading wait
- Satisfying "ding" on score reveal

### Landing Page

Hero section:
> **"Every great system was once a sketch on a whiteboard."**
> *Practice system design interviews with AI-powered grading. Draw your architecture, speak your reasoning, and let the Archmage Council judge your spell.*
>
> [Begin Your Trial →]

Below: 3-step visual — "Draw → Speak → Get Graded" with themed illustrations.

---

## 7. Seed Problems (MVP)

| # | Problem | Difficulty | Key Estimation | Key Components |
|---|---------|-----------|---------------|----------------|
| 1 | URL Shortener | Apprentice | QPS, storage for URLs | API, DB, cache, hash service |
| 2 | Rate Limiter | Apprentice | Request rates, memory for counters | API gateway, Redis, sliding window |
| 3 | Spotify | Sorcerer | 500TB audio, 12K streams/sec | CDN, S3, metadata DB, cache, streaming service |
| 4 | Chat System | Sorcerer | Messages/sec, connection count | WebSocket, message queue, presence, storage |
| 5 | YouTube | Archmage | Video storage, transcoding pipeline | Upload service, CDN, transcoder, recommendation |
| 6 | Google Docs | Archmage | Operations/sec, conflict rate | CRDT/OT service, WebSocket, storage layers |

Each problem's seed data includes: prompt, constraints, expected components, rubric hints per phase, phase time allocation, and a sample solution outline.

---

## 8. What We Cut (and Why)

| Feature | Why Cut |
|---------|---------|
| Coded clarification Q&A forms | Voice + whiteboard handles this naturally — no forms to build |
| Scratchpad textarea for estimation | Users write math on the canvas or talk it through — same whiteboard |
| Interviewer interruptions (timed pop-ups) | Requires real-time agent interaction during phases — too complex |
| Real-time common mistakes detector | Would need continuous diagram analysis while drawing |
| Progressive hint unlocking | Adds significant problem-authoring complexity |
| Diagram annotation in feedback | Generating annotated overlay on original image is hard to get right |
| Technology decision bank | Heavy UI work for marginal demo impact |

**Post-hackathon candidates** (by impact): interviewer interruptions, annotated diagram feedback, technology comparison overlays.

---

## 9. Hackathon Milestones (30 hours)

| Time | Milestone | Deliverable |
|------|-----------|------------|
| **0–3h** | Scaffolding | SvelteKit + FastAPI + uv running, SQLite schema, seed 3 problems |
| **3–7h** | Core workspace | Excalidraw iframe + postMessage, voice recorder, phase bar + timer — the single unified workspace |
| **7–10h** | Phase transitions | Snapshot capture at transitions, audio clip splitting, phase state management |
| **10–15h** | Agents | All 5 agent prompts written + tested with sample canvas snapshots and transcripts |
| **15–19h** | Integration | Full pipeline: submit → transcribe → grade → SSE → results |
| **19–23h** | Results UI | Score reveal, radar chart, rubric breakdown, feedback display |
| **23–27h** | Theme polish | Color palette, phase accents, grading animations, particle effects, landing page |
| **27–30h** | Demo prep | End-to-end testing, record video, devpost, practice pitch |

---

## 10. Demo Script (2–4 minutes)

1. **Hook** (15s): "System design interviews happen on whiteboards with phases — clarify, estimate, draw, explain. But every practice tool is just a blank text editor. DesignDuel simulates the real thing."
2. **Start** (10s): Pick "Design Spotify" → Phase 1 begins. The oracle speaks: *"Peer into the mist..."*
3. **Clarify** (15s): Talk — "I'll focus on streaming playback for 1 billion users globally, read-heavy workload." Jot a few notes on the canvas.
4. **Estimate** (15s): Advance to Phase 2. Write on the canvas — "100M songs × 5MB = 500TB." Talk — "At 100M DAU, that's about 12K streams per second."
5. **Design** (30s): Advance to Phase 3. Drag components from the library — CDN, S3, load balancer, metadata DB, cache, streaming service. Draw arrows, label connections.
6. **Explain** (15s): Phase 4 — "I separated blob storage from metadata because audio files are immutable, while metadata needs relational queries. The CDN handles the hot-song problem."
7. **Submit** (20s): "Submit to the Council." Watch SSE — "The Architecture Archmage studies your conjuration... The Scale Sorcerer tests under pressure..."
8. **Results** (30s): Score reveal animation — gold particles, 8/10. Radar chart fills in. Rubric: "9/10 scoping, 7/10 estimation, 8/10 architecture, 6/10 tradeoffs — you didn't discuss consistency models for playlist data."
9. **Tech close** (15s): "Five Gemini agents via Google ADK. Each receives canvas snapshots from every phase plus voice transcripts. Multimodal, multi-phase, multi-agent."
10. **One-liner** (5s): "DesignDuel — practice system design the way it's actually interviewed."

---

## 11. Success Metrics

| Criteria | Evidence |
|----------|---------|
| **Functional demo** | Full phased interview → grading works live |
| **Realistic format** | Phases, whiteboard, voice — matches how real interviews work |
| **AI feedback quality** | Grading references specific things drawn and said in specific phases |
| **Creative Gemini usage** | Multimodal (images + audio) × multi-phase (4 snapshots) × multi-agent (5 agents via ADK) |
| **Theme** | Magic narrative is cohesive from landing page through grading reveal |
| **"WHOA" factor** | Drawing on a whiteboard, talking through your design, and getting AI-graded like a real interview panel |
