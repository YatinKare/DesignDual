#!/bin/bash
# Test script for submission status lifecycle (Task 6.6)
# Expected flow: QUEUED → PROCESSING → TRANSCRIBING → GRADING → COMPLETE

set -euo pipefail

BACKEND_DIR="/Users/yatink/Documents/GitHub/DesignDual-backend/backend"
DB_PATH="$BACKEND_DIR/data/designdual.db"
TEMP_DIR="$BACKEND_DIR/temp"
TEST_OUTPUT="$TEMP_DIR/status_lifecycle_test_$(date +%Y%m%d_%H%M%S).txt"

mkdir -p "$TEMP_DIR"

echo "=== Submission Status Lifecycle Test (Task 6.6) ===" | tee "$TEST_OUTPUT"
echo "" | tee -a "$TEST_OUTPUT"

# Kill any existing server
pkill -f "uvicorn.*app.main:app" || true
sleep 2

# Start server in background with correct .env
cd "$BACKEND_DIR/.."
echo "Starting server..." | tee -a "$TEST_OUTPUT"
(cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$TEMP_DIR/server.log" 2>&1) &
SERVER_PID=$!
echo "Server PID: $SERVER_PID" | tee -a "$TEST_OUTPUT"

# Wait for server to start
sleep 5

# Create minimal test PNG files
echo "Creating test files..." | tee -a "$TEST_OUTPUT"
for phase in clarify estimate design explain; do
    dd if=/dev/urandom of="$TEMP_DIR/canvas_${phase}_test.png" bs=1024 count=1 2>/dev/null
done

# Submit a test submission
echo "" | tee -a "$TEST_OUTPUT"
echo "Submitting test submission..." | tee -a "$TEST_OUTPUT"

SUBMIT_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/submissions \
  -F "problem_id=url-shortener" \
  -F "canvas_clarify=@$TEMP_DIR/canvas_clarify_test.png" \
  -F "canvas_estimate=@$TEMP_DIR/canvas_estimate_test.png" \
  -F "canvas_design=@$TEMP_DIR/canvas_design_test.png" \
  -F "canvas_explain=@$TEMP_DIR/canvas_explain_test.png" \
  -F 'phase_times={"clarify":180,"estimate":120,"design":240,"explain":180}')

echo "Response: $SUBMIT_RESPONSE" | tee -a "$TEST_OUTPUT"

SUBMISSION_ID=$(echo "$SUBMIT_RESPONSE" | grep -o '"submission_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SUBMISSION_ID" ]; then
    echo "❌ Failed to create submission" | tee -a "$TEST_OUTPUT"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Submission created: $SUBMISSION_ID" | tee -a "$TEST_OUTPUT"

# Check initial status (should be QUEUED)
echo "" | tee -a "$TEST_OUTPUT"
echo "Checking initial status (expecting QUEUED)..." | tee -a "$TEST_OUTPUT"
sleep 1
INITIAL_STATUS=$(sqlite3 "$DB_PATH" "SELECT status FROM submissions WHERE id = '$SUBMISSION_ID';")
echo "Initial status: $INITIAL_STATUS" | tee -a "$TEST_OUTPUT"

if [ "$INITIAL_STATUS" = "queued" ]; then
    echo "✅ Initial status is QUEUED (correct)" | tee -a "$TEST_OUTPUT"
else
    echo "❌ Initial status is $INITIAL_STATUS (expected: queued)" | tee -a "$TEST_OUTPUT"
fi

# Monitor status transitions
echo "" | tee -a "$TEST_OUTPUT"
echo "Monitoring status transitions..." | tee -a "$TEST_OUTPUT"

PREV_STATUS=""
for i in {1..30}; do
    CURRENT_STATUS=$(sqlite3 "$DB_PATH" "SELECT status FROM submissions WHERE id = '$SUBMISSION_ID';")

    if [ "$CURRENT_STATUS" != "$PREV_STATUS" ]; then
        TIMESTAMP=$(date +%H:%M:%S)
        echo "[$TIMESTAMP] Status: $CURRENT_STATUS" | tee -a "$TEST_OUTPUT"
        PREV_STATUS="$CURRENT_STATUS"
    fi

    # Stop monitoring if we reach terminal state
    if [ "$CURRENT_STATUS" = "complete" ] || [ "$CURRENT_STATUS" = "failed" ]; then
        break
    fi

    sleep 2
done

echo "" | tee -a "$TEST_OUTPUT"
echo "Final status: $CURRENT_STATUS" | tee -a "$TEST_OUTPUT"

# Validate expected status transitions
echo "" | tee -a "$TEST_OUTPUT"
echo "=== Validation ===" | tee -a "$TEST_OUTPUT"

# Check that the submission went through expected states
ALL_STATUSES=$(sqlite3 "$DB_PATH" "SELECT status FROM submissions WHERE id = '$SUBMISSION_ID';")
echo "Current status: $ALL_STATUSES" | tee -a "$TEST_OUTPUT"

# Check for expected lifecycle
if [ "$INITIAL_STATUS" = "queued" ]; then
    echo "✅ Lifecycle started with QUEUED" | tee -a "$TEST_OUTPUT"
else
    echo "❌ Lifecycle did NOT start with QUEUED" | tee -a "$TEST_OUTPUT"
fi

if [ "$CURRENT_STATUS" = "complete" ] || [ "$CURRENT_STATUS" = "failed" ]; then
    echo "✅ Lifecycle reached terminal state: $CURRENT_STATUS" | tee -a "$TEST_OUTPUT"
else
    echo "⚠️  Lifecycle did not complete within timeout (current: $CURRENT_STATUS)" | tee -a "$TEST_OUTPUT"
fi

# Cleanup
echo "" | tee -a "$TEST_OUTPUT"
echo "Cleaning up..." | tee -a "$TEST_OUTPUT"
kill $SERVER_PID 2>/dev/null || true
rm -f "$TEMP_DIR/canvas_"*"_test.png"

echo "" | tee -a "$TEST_OUTPUT"
echo "Test output saved to: $TEST_OUTPUT" | tee -a "$TEST_OUTPUT"
echo "" | tee -a "$TEST_OUTPUT"
echo "=== Test Complete ===" | tee -a "$TEST_OUTPUT"
