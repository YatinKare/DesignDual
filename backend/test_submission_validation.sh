#!/bin/bash
# Test script for POST /api/submissions validation

set -e  # Exit on error

# Configuration
BASE_URL="http://127.0.0.1:8000"
TEMP_DIR="backend/temp/validation_test"
TEST_RESULTS="backend/temp/validation_test_results.txt"

# Create temp directory
mkdir -p "$TEMP_DIR"

# Start server in background if not running
if ! curl -s "$BASE_URL/api/problems" > /dev/null 2>&1; then
    echo "Starting FastAPI server..."
    cd backend
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    SERVER_PID=$!
    cd ..
    sleep 3
    echo "Server started (PID: $SERVER_PID)"
else
    echo "Server already running"
    SERVER_PID=""
fi

# Initialize results file
echo "=== Submission Validation Tests ===" > "$TEST_RESULTS"
echo "Test run: $(date)" >> "$TEST_RESULTS"
echo "" >> "$TEST_RESULTS"

# Create a tiny valid PNG (1x1 pixel)
create_tiny_png() {
    local filename=$1
    # Base64 encoded 1x1 PNG
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" | base64 -d > "$filename"
}

# Create valid test files
create_tiny_png "$TEMP_DIR/canvas_clarify.png"
create_tiny_png "$TEMP_DIR/canvas_estimate.png"
create_tiny_png "$TEMP_DIR/canvas_design.png"
create_tiny_png "$TEMP_DIR/canvas_explain.png"

# Create empty PNG for testing
touch "$TEMP_DIR/empty.png"

echo "=== Test files created ===" >> "$TEST_RESULTS"
echo "" >> "$TEST_RESULTS"

# Test 1: Invalid problem_id
echo "Test 1: Invalid problem_id (should fail with 404)" | tee -a "$TEST_RESULTS"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/api/submissions" \
    -F "problem_id=nonexistent-problem" \
    -F "canvas_clarify=@$TEMP_DIR/canvas_clarify.png" \
    -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
    -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
    -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
    -F 'phase_times={"clarify":100,"estimate":200,"design":300,"explain":150}')
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
echo "Response code: $http_code" | tee -a "$TEST_RESULTS"
if [ "$http_code" = "404" ]; then
    echo "✅ PASS: Got expected 404 error for invalid problem_id" | tee -a "$TEST_RESULTS"
else
    echo "❌ FAIL: Expected 404, got $http_code" | tee -a "$TEST_RESULTS"
fi
echo "" >> "$TEST_RESULTS"

# Test 2: Missing phase_times key
echo "Test 2: Missing phase in phase_times (should fail with 400)" | tee -a "$TEST_RESULTS"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/api/submissions" \
    -F "problem_id=url-shortener" \
    -F "canvas_clarify=@$TEMP_DIR/canvas_clarify.png" \
    -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
    -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
    -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
    -F 'phase_times={"clarify":100,"estimate":200,"design":300}')
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
echo "Response code: $http_code" | tee -a "$TEST_RESULTS"
if [ "$http_code" = "400" ]; then
    echo "✅ PASS: Got expected 400 error for missing phase" | tee -a "$TEST_RESULTS"
else
    echo "❌ FAIL: Expected 400, got $http_code" | tee -a "$TEST_RESULTS"
fi
echo "" >> "$TEST_RESULTS"

# Test 3: Extra phase_times key
echo "Test 3: Extra phase in phase_times (should fail with 400)" | tee -a "$TEST_RESULTS"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/api/submissions" \
    -F "problem_id=url-shortener" \
    -F "canvas_clarify=@$TEMP_DIR/canvas_clarify.png" \
    -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
    -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
    -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
    -F 'phase_times={"clarify":100,"estimate":200,"design":300,"explain":150,"extra":50}')
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
echo "Response code: $http_code" | tee -a "$TEST_RESULTS"
if [ "$http_code" = "400" ]; then
    echo "✅ PASS: Got expected 400 error for extra phase" | tee -a "$TEST_RESULTS"
else
    echo "❌ FAIL: Expected 400, got $http_code" | tee -a "$TEST_RESULTS"
fi
echo "" >> "$TEST_RESULTS"

# Test 4: Empty canvas file
echo "Test 4: Empty canvas file (should fail with 400)" | tee -a "$TEST_RESULTS"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/api/submissions" \
    -F "problem_id=url-shortener" \
    -F "canvas_clarify=@$TEMP_DIR/empty.png" \
    -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
    -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
    -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
    -F 'phase_times={"clarify":100,"estimate":200,"design":300,"explain":150}')
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
echo "Response code: $http_code" | tee -a "$TEST_RESULTS"
if [ "$http_code" = "400" ]; then
    echo "✅ PASS: Got expected 400 error for empty canvas" | tee -a "$TEST_RESULTS"
else
    echo "❌ FAIL: Expected 400, got $http_code" | tee -a "$TEST_RESULTS"
fi
echo "" >> "$TEST_RESULTS"

# Test 5: Valid submission (should succeed)
echo "Test 5: Valid submission with all required fields (should succeed with 200)" | tee -a "$TEST_RESULTS"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/api/submissions" \
    -F "problem_id=url-shortener" \
    -F "canvas_clarify=@$TEMP_DIR/canvas_clarify.png" \
    -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
    -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
    -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
    -F 'phase_times={"clarify":100,"estimate":200,"design":300,"explain":150}')
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
echo "Response code: $http_code" | tee -a "$TEST_RESULTS"
if [ "$http_code" = "200" ]; then
    echo "✅ PASS: Valid submission accepted" | tee -a "$TEST_RESULTS"
    submission_id=$(echo "$response" | head -n -1 | grep -o '"submission_id":"[^"]*"' | cut -d'"' -f4)
    echo "Created submission: $submission_id" | tee -a "$TEST_RESULTS"
else
    echo "❌ FAIL: Expected 200, got $http_code" | tee -a "$TEST_RESULTS"
fi
echo "" >> "$TEST_RESULTS"

# Cleanup
echo "=== Cleaning up ===" | tee -a "$TEST_RESULTS"
rm -rf "$TEMP_DIR"
if [ -n "$SERVER_PID" ]; then
    echo "Stopping server (PID: $SERVER_PID)"
    kill $SERVER_PID 2>/dev/null || true
fi

echo "" >> "$TEST_RESULTS"
echo "=== Test Summary ===" | tee -a "$TEST_RESULTS"
echo "Results saved to: $TEST_RESULTS"
echo "All validation tests completed!"
