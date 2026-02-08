# DesignDual Backend API Documentation

**Base URL**: `http://localhost:8000`
**Content-Type**: `application/json` (unless otherwise noted)

---

## Problems

### GET /api/problems

List all available system design problems.

**Response**: `200 OK`
```json
[
  {
    "id": "url-shortener",
    "title": "URL Shortener",
    "slug": "url-shortener",
    "difficulty": "apprentice",
    "focus_tags": ["hashing", "database", "caching"],
    "estimated_time_minutes": 35
  },
  {
    "id": "rate-limiter",
    "title": "Rate Limiter",
    "slug": "rate-limiter",
    "difficulty": "apprentice",
    "focus_tags": ["distributed-systems", "algorithms"],
    "estimated_time_minutes": 35
  }
]
```

**Example**:
```bash
curl http://localhost:8000/api/problems
```

---

### GET /api/problems/{id}

Get detailed information about a specific problem.

**Path Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `id` | string | Problem ID (e.g., "url-shortener") |

**Response**: `200 OK`
```json
{
  "id": "url-shortener",
  "title": "URL Shortener",
  "slug": "url-shortener",
  "difficulty": "apprentice",
  "prompt": "Design a URL shortening service like bit.ly...",
  "constraints": [
    "Handle 100M new URLs per month",
    "99.9% availability SLA"
  ],
  "focus_tags": ["hashing", "database", "caching"],
  "estimated_time_minutes": 35,
  "rubric_hints": ["Consider hash collisions", "Think about read:write ratio"],
  "time_allocation": {
    "clarify": 5,
    "estimate": 5,
    "design": 15,
    "explain": 10
  },
  "rubric_definition": [
    {
      "label": "Requirements Clarity",
      "description": "Did the candidate ask good clarifying questions?",
      "phase_weights": {"clarify": 0.7, "estimate": 0.3}
    },
    {
      "label": "System Design",
      "description": "Is the architecture sound and well-reasoned?",
      "phase_weights": {"design": 0.8, "explain": 0.2}
    }
  ]
}
```

**Errors**:
- `404 Not Found`: Problem with given ID does not exist

**Example**:
```bash
curl http://localhost:8000/api/problems/url-shortener
```

---

## Submissions

### POST /api/submissions

Submit a system design interview for grading.

**Content-Type**: `multipart/form-data`

**Form Fields**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `problem_id` | string | Yes | ID of the problem being solved |
| `canvas_clarify` | file (PNG) | Yes | Canvas snapshot from clarify phase |
| `canvas_estimate` | file (PNG) | Yes | Canvas snapshot from estimate phase |
| `canvas_design` | file (PNG) | Yes | Canvas snapshot from design phase |
| `canvas_explain` | file (PNG) | Yes | Canvas snapshot from explain phase |
| `audio_clarify` | file (webm) | No | Audio recording from clarify phase |
| `audio_estimate` | file (webm) | No | Audio recording from estimate phase |
| `audio_design` | file (webm) | No | Audio recording from design phase |
| `audio_explain` | file (webm) | No | Audio recording from explain phase |
| `phase_times` | string (JSON) | Yes | Time spent per phase in seconds |

**phase_times format**:
```json
{"clarify": 300, "estimate": 180, "design": 900, "explain": 420}
```

**Response**: `200 OK`
```json
{
  "submission_id": "b5bd9825-5c43-497c-885d-7903e63b502b"
}
```

**Errors**:
- `404 Not Found`: Invalid problem_id
- `400 Bad Request`: Missing required phases in phase_times
- `400 Bad Request`: Empty canvas file
- `400 Bad Request`: Invalid file type (must be image/png or image/jpeg)

**Example**:
```bash
curl -X POST http://localhost:8000/api/submissions \
  -F "problem_id=url-shortener" \
  -F "canvas_clarify=@./clarify.png" \
  -F "canvas_estimate=@./estimate.png" \
  -F "canvas_design=@./design.png" \
  -F "canvas_explain=@./explain.png" \
  -F "audio_clarify=@./clarify.webm" \
  -F 'phase_times={"clarify":300,"estimate":180,"design":900,"explain":420}'
```

---

### GET /api/submissions/{id}

Retrieve the complete grading result for a submission.

**Path Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `id` | string | Submission UUID |

**Response**: `200 OK` — Returns a `SubmissionResultV2` payload

```json
{
  "result_version": 2,
  "submission_id": "b5bd9825-5c43-497c-885d-7903e63b502b",
  "problem": {
    "id": "url-shortener",
    "name": "URL Shortener",
    "difficulty": "apprentice"
  },
  "overall_score": 8.4,
  "verdict": "hire",
  "summary": "Strong overall performance with solid design fundamentals...",
  "phase_scores": [
    {
      "phase": "clarify",
      "score": 9.0,
      "bullets": [
        "Asked about read:write ratio early",
        "Clarified availability requirements",
        "Could explore geo-distribution needs"
      ]
    },
    {
      "phase": "estimate",
      "score": 8.0,
      "bullets": ["Accurate QPS calculations", "Considered storage growth"]
    },
    {
      "phase": "design",
      "score": 8.0,
      "bullets": ["Clean component separation", "Good use of caching layer"]
    },
    {
      "phase": "explain",
      "score": 8.7,
      "bullets": ["Explained CAP tradeoffs", "Identified bottlenecks"]
    }
  ],
  "evidence": [
    {
      "phase": "clarify",
      "snapshot_url": "/uploads/b5bd9825.../canvas_clarify.png",
      "transcripts": []
    }
  ],
  "rubric": [
    {
      "label": "Requirements Clarity",
      "description": "Did the candidate ask good clarifying questions?",
      "computed_from": ["clarify", "estimate"],
      "score": 8.5,
      "status": "pass"
    }
  ],
  "radar": [
    {"dimension": "clarity", "score": 9.0},
    {"dimension": "structure", "score": 8.0},
    {"dimension": "power", "score": 8.0},
    {"dimension": "wisdom", "score": 8.7}
  ],
  "strengths": [
    {"observation": "Strong problem scoping", "timestamp": "0:45"}
  ],
  "weaknesses": [
    {"observation": "Could discuss failover", "timestamp": "12:30"}
  ],
  "next_attempt_plan": [
    {"priority": 1, "area": "Caching", "action": "Discuss cache invalidation strategies"}
  ],
  "follow_up_questions": [
    "How would you handle hot keys in the cache?",
    "What happens if the hash function produces collisions?"
  ],
  "reference_outline": {
    "title": "URL Shortener Reference Design",
    "sections": [
      {"heading": "Key Components", "bullets": ["API Gateway", "Hash Service", "Database"]}
    ]
  },
  "submitted_at": "2026-02-07T21:56:53.000Z",
  "graded_at": "2026-02-07T21:58:10.000Z"
}
```

**Errors**:
- `404 Not Found`: Submission not found or not yet graded

**Example**:
```bash
curl http://localhost:8000/api/submissions/b5bd9825-5c43-497c-885d-7903e63b502b
```

---

### GET /api/submissions/{id}/stream

Stream grading progress events via Server-Sent Events (SSE).

**Path Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `id` | string | Submission UUID |

**Response**: `200 OK` with `Content-Type: text/event-stream`

**Event Sequence**:
```
data: {"status": "processing", "message": "Your spell has been submitted...", "progress": 0.0}

data: {"status": "processing", "message": "Deciphering your incantations...", "progress": 0.1}

data: {"status": "processing", "message": "Transcription complete...", "progress": 0.2}

data: {"status": "clarify", "phase": "clarify", "message": "The Clarification Sage examines...", "progress": 0.3}

data: {"status": "estimate", "phase": "estimate", "message": "The Estimation Oracle calculates...", "progress": 0.4}

data: {"status": "design", "phase": "design", "message": "The Architecture Archmage studies...", "progress": 0.5}

data: {"status": "explain", "phase": "explain", "message": "The Wisdom Keeper weighs...", "progress": 0.6}

data: {"status": "synthesizing", "message": "The Council deliberates...", "progress": 0.85}

data: {"status": "complete", "message": "The verdict is sealed.", "progress": 1.0, "result": {...}}
```

**Status Values**:
- `queued` — Waiting for processing
- `processing` — Preparing submission
- `clarify` — Evaluating clarify phase
- `estimate` — Evaluating estimate phase
- `design` — Evaluating design phase
- `explain` — Evaluating explain phase
- `synthesizing` — Combining agent outputs
- `complete` — Grading finished (includes full result)
- `failed` — Error occurred

**Example**:
```bash
curl -N http://localhost:8000/api/submissions/b5bd9825.../stream
```

---

## Dashboard

### GET /api/dashboard

Get the user's score history and performance summary.

**Query Parameters**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | int | 50 | Max history entries (1-100) |

**Response**: `200 OK`
```json
{
  "summary": {
    "total_submissions": 4,
    "average_score": 8.31,
    "best_score": 8.62,
    "worst_score": 7.94,
    "verdict_breakdown": {
      "hire": 4,
      "no_hire": 0,
      "strong_hire": 0
    }
  },
  "history": [
    {
      "submission_id": "b5bd9825...",
      "problem_id": "url-shortener",
      "problem_title": "URL Shortener",
      "difficulty": "apprentice",
      "overall_score": 8.4,
      "verdict": "hire",
      "submitted_at": "2026-02-07T21:56:53.000Z",
      "graded_at": "2026-02-07T21:58:10.000Z"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/dashboard
```

---

### GET /api/dashboard/history

Get only the score history (without summary).

**Query Parameters**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | int | 50 | Max entries (1-100) |

**Response**: `200 OK`
```json
[
  {
    "submission_id": "b5bd9825...",
    "problem_id": "url-shortener",
    "problem_title": "URL Shortener",
    "difficulty": "apprentice",
    "overall_score": 8.4,
    "verdict": "hire",
    "submitted_at": "2026-02-07T21:56:53.000Z",
    "graded_at": "2026-02-07T21:58:10.000Z"
  }
]
```

**Example**:
```bash
curl "http://localhost:8000/api/dashboard/history?limit=10"
```

---

### GET /api/dashboard/summary

Get only the performance summary (without history).

**Response**: `200 OK`
```json
{
  "total_submissions": 4,
  "average_score": 8.31,
  "best_score": 8.62,
  "worst_score": 7.94,
  "verdict_breakdown": {
    "hire": 4,
    "no_hire": 0,
    "strong_hire": 0
  }
}
```

**Example**:
```bash
curl http://localhost:8000/api/dashboard/summary
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes**:
| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad Request — Invalid input |
| `404` | Not Found — Resource doesn't exist |
| `500` | Internal Server Error — Server-side failure |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `DATABASE_PATH` | No | `./data/designdual.db` | SQLite database path |
| `FRONTEND_ORIGIN` | No | `http://localhost:5173` | CORS allowed origin |
| `UPLOAD_DIR` | No | `./storage` | File upload directory |
| `MAX_UPLOAD_SIZE_MB` | No | `50` | Maximum file upload size |

---

## Running the Server

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
