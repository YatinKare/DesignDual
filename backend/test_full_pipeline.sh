#!/bin/bash
# Test script for full grading pipeline (Task 5.6)
# Polls SQLite database directly since GET /api/submissions/{id} isn't implemented yet.

set -e

echo "======================================"
echo "Full Grading Pipeline Test (Task 5.6)"
echo "======================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_BASE="http://localhost:8000"
BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMP_DIR="$BACKEND_DIR/temp"
DB_PATH="$BACKEND_DIR/data/designdual.db"

# ── Step 1: Create test canvas images ────────────────────────────────
echo -e "${YELLOW}Step 1: Creating test canvas images...${NC}"
mkdir -p "$TEMP_DIR"

for phase in clarify estimate design explain; do
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$TEMP_DIR/canvas_${phase}.png"
    echo "  Created canvas_${phase}.png"
done

# ── Step 2: Kill old server, start fresh ─────────────────────────────
echo ""
echo -e "${YELLOW}Step 2: Starting fresh FastAPI server...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 2

cd "$BACKEND_DIR"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$TEMP_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo "  Server PID: $SERVER_PID"

echo "  Waiting for server to start..."
for i in {1..30}; do
    if curl -s "$API_BASE/api/problems" > /dev/null 2>&1; then
        echo -e "${GREEN}  Server ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}  Server failed to start. Logs:${NC}"
        cat "$TEMP_DIR/server.log"
        exit 1
    fi
done

# Verify the API key is loaded (check via env in server process)
echo "  Verifying GOOGLE_API_KEY is loaded..."
KEY_CHECK=$(uv run python -c "
from pathlib import Path
from dotenv import load_dotenv
import os
project_root = Path('$BACKEND_DIR').parent
load_dotenv(project_root / '.env')
key = os.getenv('GOOGLE_API_KEY', '')
if key and key != 'your-google-api-key':
    print('VALID')
else:
    print('INVALID')
")
if [ "$KEY_CHECK" != "VALID" ]; then
    echo -e "${RED}  GOOGLE_API_KEY is missing or placeholder in root .env${NC}"
    echo "  Ensure the project root .env has a real key."
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}  API key verified${NC}"

# ── Step 3: Fetch problems ───────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 3: Fetching available problems...${NC}"
PROBLEMS=$(curl -s "$API_BASE/api/problems")
echo "$PROBLEMS" | python3 -m json.tool
PROBLEM_ID=$(echo "$PROBLEMS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null || echo "")

if [ -z "$PROBLEM_ID" ]; then
    echo -e "${RED}  No problems found in database${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}  Using problem: $PROBLEM_ID${NC}"

# ── Step 4: Submit grading request ───────────────────────────────────
echo ""
echo -e "${YELLOW}Step 4: Submitting grading request...${NC}"

RESPONSE=$(curl -s -X POST "$API_BASE/api/submissions" \
  -F "problem_id=$PROBLEM_ID" \
  -F "canvas_clarify=@$TEMP_DIR/canvas_clarify.png" \
  -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
  -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
  -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
  -F 'phase_times={"clarify":180,"estimate":240,"design":480,"explain":300}')

echo "$RESPONSE" | python3 -m json.tool

SUBMISSION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['submission_id'])" 2>/dev/null || echo "")

if [ -z "$SUBMISSION_ID" ]; then
    echo -e "${RED}  Failed to get submission_id from response${NC}"
    echo "  Response was: $RESPONSE"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}  Submission ID: $SUBMISSION_ID${NC}"

# ── Step 5: Poll DB for grading completion ───────────────────────────
echo ""
echo -e "${YELLOW}Step 5: Monitoring grading progress (polling SQLite)...${NC}"
echo "  This may take 2-7 minutes for the ADK agents to run."
echo ""

MAX_WAIT=600
ELAPSED=0
LAST_STATUS=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep 5
    ELAPSED=$((ELAPSED + 5))

    CURRENT_STATUS=$(uv run python -c "
import sqlite3, sys
conn = sqlite3.connect('$DB_PATH')
cur = conn.execute('SELECT status FROM submissions WHERE id = ?', ('$SUBMISSION_ID',))
row = cur.fetchone()
conn.close()
print(row[0] if row else 'not_found')
" 2>/dev/null || echo "error")

    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
        echo "  [$(date +%H:%M:%S)] Status: $CURRENT_STATUS (${ELAPSED}s elapsed)"
        LAST_STATUS="$CURRENT_STATUS"
    fi

    if [ "$CURRENT_STATUS" = "complete" ]; then
        echo -e "${GREEN}  Grading completed successfully!${NC}"
        break
    elif [ "$CURRENT_STATUS" = "failed" ]; then
        echo -e "${RED}  Grading failed!${NC}"
        echo ""
        echo "  Server logs (last 40 lines):"
        tail -40 "$TEMP_DIR/server.log"
        kill $SERVER_PID 2>/dev/null
        exit 1
    fi
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}  Timeout after ${MAX_WAIT}s waiting for grading${NC}"
    tail -40 "$TEMP_DIR/server.log"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# ── Step 6: Fetch grading result from DB ─────────────────────────────
echo ""
echo -e "${YELLOW}Step 6: Fetching grading result from database...${NC}"

RESULT_JSON=$(uv run python -c "
import sqlite3, json, sys

conn = sqlite3.connect('$DB_PATH')
conn.row_factory = sqlite3.Row

# Submission data
sub = conn.execute('SELECT * FROM submissions WHERE id = ?', ('$SUBMISSION_ID',)).fetchone()
if not sub:
    print(json.dumps({'error': 'Submission not found'}))
    sys.exit(0)

# Grading result
gr = conn.execute('SELECT * FROM grading_results WHERE submission_id = ?', ('$SUBMISSION_ID',)).fetchone()
conn.close()

output = {
    'submission': {
        'id': sub['id'],
        'problem_id': sub['problem_id'],
        'status': sub['status'],
        'created_at': sub['created_at'],
    }
}

if gr:
    output['grading_result'] = {
        'overall_score': gr['overall_score'],
        'verdict': gr['verdict'],
        'verdict_display': gr['verdict_display'],
        'dimensions': json.loads(gr['dimensions']) if gr['dimensions'] else None,
        'top_improvements': json.loads(gr['top_improvements']) if gr['top_improvements'] else None,
        'phase_observations': json.loads(gr['phase_observations']) if gr['phase_observations'] else None,
    }
else:
    output['grading_result'] = None

print(json.dumps(output, indent=2))
")

echo "$RESULT_JSON" | python3 -m json.tool

OVERALL_SCORE=$(echo "$RESULT_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('grading_result',{}).get('overall_score','N/A'))" 2>/dev/null || echo "N/A")
VERDICT=$(echo "$RESULT_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('grading_result',{}).get('verdict_display','N/A'))" 2>/dev/null || echo "N/A")

echo ""
echo "======================================"
echo -e "${GREEN}TEST RESULTS${NC}"
echo "======================================"
echo "Submission ID: $SUBMISSION_ID"
echo "Overall Score: $OVERALL_SCORE / 10"
echo "Verdict:       $VERDICT"

if [ "$OVERALL_SCORE" = "N/A" ] || [ "$OVERALL_SCORE" = "None" ]; then
    echo ""
    echo -e "${RED}  No grading result found even though status=complete${NC}"
    tail -40 "$TEMP_DIR/server.log"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo -e "${GREEN}Full pipeline test PASSED${NC}"

# Save results
RESULTS_FILE="$TEMP_DIR/pipeline_test_result_$(date +%Y%m%d_%H%M%S).json"
echo "$RESULT_JSON" > "$RESULTS_FILE"
echo "Results saved to: $RESULTS_FILE"

# Cleanup
echo ""
echo "Stopping test server..."
kill $SERVER_PID 2>/dev/null || true

echo "Done."
exit 0
