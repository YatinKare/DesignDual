#!/bin/bash
# Test script for full grading pipeline (Task 5.6)

set -e  # Exit on error

echo "======================================"
echo "Full Grading Pipeline Test (Task 5.6)"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000"
BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMP_DIR="$BACKEND_DIR/temp"
STORAGE_DIR="$BACKEND_DIR/storage"

# Create temp test files
echo -e "${YELLOW}Step 1: Creating test canvas images...${NC}"
mkdir -p "$TEMP_DIR"

# Create 4 simple PNG test images (1x1 pixel PNGs)
for phase in clarify estimate design explain; do
    # Create a 1x1 PNG using base64 (smallest valid PNG)
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$TEMP_DIR/canvas_${phase}.png"
    echo "  Created canvas_${phase}.png"
done

# Use existing sample audio file if available
AUDIO_FILE="$TEMP_DIR/Sample Video To Practice Transcribing.m4a"
if [ -f "$AUDIO_FILE" ]; then
    echo -e "${GREEN}  Found existing sample audio file${NC}"
else
    echo -e "${YELLOW}  No audio file found - will test without audio${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Starting FastAPI server...${NC}"

# Check if server is already running
if curl -s "$API_BASE/api/problems" > /dev/null 2>&1; then
    echo -e "${GREEN}  Server already running${NC}"
else
    echo "  Starting server in background..."
    cd "$BACKEND_DIR"
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$TEMP_DIR/server.log" 2>&1 &
    SERVER_PID=$!
    echo "  Server PID: $SERVER_PID"

    # Wait for server to be ready
    echo "  Waiting for server to start..."
    for i in {1..30}; do
        if curl -s "$API_BASE/api/problems" > /dev/null 2>&1; then
            echo -e "${GREEN}  Server ready!${NC}"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${RED}  Server failed to start${NC}"
            cat "$TEMP_DIR/server.log"
            exit 1
        fi
    done
fi

echo ""
echo -e "${YELLOW}Step 3: Fetching available problems...${NC}"
PROBLEMS=$(curl -s "$API_BASE/api/problems")
echo "$PROBLEMS" | python3 -m json.tool
PROBLEM_ID=$(echo "$PROBLEMS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null || echo "")

if [ -z "$PROBLEM_ID" ]; then
    echo -e "${RED}  No problems found in database${NC}"
    echo "  Run: uv run python -m app.db.init_db"
    exit 1
fi

echo -e "${GREEN}  Using problem: $PROBLEM_ID${NC}"

echo ""
echo -e "${YELLOW}Step 4: Submitting grading request...${NC}"

# Build curl command (without audio for now - validation expects webm)
CURL_CMD="curl -X POST $API_BASE/api/submissions \
  -F \"problem_id=$PROBLEM_ID\" \
  -F \"canvas_clarify=@$TEMP_DIR/canvas_clarify.png\" \
  -F \"canvas_estimate=@$TEMP_DIR/canvas_estimate.png\" \
  -F \"canvas_design=@$TEMP_DIR/canvas_design.png\" \
  -F \"canvas_explain=@$TEMP_DIR/canvas_explain.png\" \
  -F 'phase_times={\"clarify\":180,\"estimate\":240,\"design\":480,\"explain\":300}'"

# Note: Skipping audio files - grading pipeline handles missing audio gracefully

# Execute submission
echo "  Executing submission..."
RESPONSE=$(eval "$CURL_CMD -s")
echo "$RESPONSE" | python3 -m json.tool

SUBMISSION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['submission_id'])" 2>/dev/null || echo "")

if [ -z "$SUBMISSION_ID" ]; then
    echo -e "${RED}  Failed to get submission_id${NC}"
    exit 1
fi

echo -e "${GREEN}  Submission ID: $SUBMISSION_ID${NC}"

echo ""
echo -e "${YELLOW}Step 5: Monitoring grading progress...${NC}"
echo "  Waiting for background grading to complete..."
echo "  (This may take 2-7 minutes depending on transcription + agent execution)"
echo ""

# Poll submission status
MAX_WAIT=600  # 10 minutes max
ELAPSED=0
LAST_STATUS=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep 5
    ELAPSED=$((ELAPSED + 5))

    # Fetch current submission status
    STATUS_RESPONSE=$(curl -s "$API_BASE/api/submissions/$SUBMISSION_ID" || echo "{}")
    CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")

    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
        echo "  [$(date +%H:%M:%S)] Status: $CURRENT_STATUS (${ELAPSED}s elapsed)"
        LAST_STATUS=$CURRENT_STATUS
    fi

    # Check if complete or failed
    if [ "$CURRENT_STATUS" = "complete" ]; then
        echo -e "${GREEN}  Grading completed successfully!${NC}"
        break
    elif [ "$CURRENT_STATUS" = "failed" ]; then
        echo -e "${RED}  Grading failed!${NC}"
        echo ""
        echo "Full response:"
        echo "$STATUS_RESPONSE" | python3 -m json.tool
        exit 1
    fi
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}  Timeout waiting for grading to complete${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 6: Fetching final grading result...${NC}"

FINAL_RESULT=$(curl -s "$API_BASE/api/submissions/$SUBMISSION_ID")
echo "$FINAL_RESULT" | python3 -m json.tool

# Extract key metrics
OVERALL_SCORE=$(echo "$FINAL_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('grading_result', {}).get('overall_score', 'N/A'))" 2>/dev/null || echo "N/A")
VERDICT=$(echo "$FINAL_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('grading_result', {}).get('verdict_display', 'N/A'))" 2>/dev/null || echo "N/A")

echo ""
echo "======================================"
echo -e "${GREEN}TEST RESULTS${NC}"
echo "======================================"
echo "Submission ID: $SUBMISSION_ID"
echo "Overall Score: $OVERALL_SCORE / 10"
echo "Verdict: $VERDICT"
echo ""
echo -e "${GREEN}✅ Full pipeline test PASSED${NC}"
echo ""

# Save results for reference
RESULTS_FILE="$TEMP_DIR/pipeline_test_result_$(date +%Y%m%d_%H%M%S).json"
echo "$FINAL_RESULT" > "$RESULTS_FILE"
echo "Full results saved to: $RESULTS_FILE"

echo ""
echo "======================================"
echo "Cleanup"
echo "======================================"
echo "Test canvas files are in: $TEMP_DIR"
echo "Submission artifacts are in: $STORAGE_DIR/submissions/$SUBMISSION_ID/"
echo ""
echo "To cleanup test files:"
echo "  rm -rf $TEMP_DIR/canvas_*.png"
echo ""

exit 0
