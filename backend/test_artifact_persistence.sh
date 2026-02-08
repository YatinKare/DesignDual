#!/bin/bash

# Test script to verify artifact persistence with submission_artifacts table

set -e

echo "🧪 Testing artifact persistence (task 6.5)"
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Create temp test images
TEMP_DIR="temp/test_artifacts_$(date +%s)"
mkdir -p "$TEMP_DIR"
echo "Creating test images in $TEMP_DIR..."

# Create 1x1 PNG files for testing (valid PNG header + data)
for phase in clarify estimate design explain; do
    # Create a valid minimal PNG file (1x1 transparent pixel)
    printf '\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0a\x49\x44\x41\x54\x78\x9c\x63\x00\x01\x00\x00\x05\x00\x01\x0d\x0a\x2d\xb4\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82' > "$TEMP_DIR/canvas_${phase}.png"
done

echo "✓ Created test PNG files"
echo ""

# Start FastAPI server in background
echo "Starting FastAPI server..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Load environment from project root .env
export $(cat ../.env | grep -v '^#' | xargs)

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$TEMP_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo "✓ Server started (PID: $SERVER_PID)"
sleep 3

# Test: Submit with all 4 canvas files
echo ""
echo "Test: Creating submission with 4 canvas files..."
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/submissions \
  -F "problem_id=url-shortener" \
  -F "canvas_clarify=@$TEMP_DIR/canvas_clarify.png" \
  -F "canvas_estimate=@$TEMP_DIR/canvas_estimate.png" \
  -F "canvas_design=@$TEMP_DIR/canvas_design.png" \
  -F "canvas_explain=@$TEMP_DIR/canvas_explain.png" \
  -F 'phase_times={"clarify": 300, "estimate": 200, "design": 400, "explain": 250}')

echo "Response: $RESPONSE"

# Extract submission_id
SUBMISSION_ID=$(echo "$RESPONSE" | grep -o '"submission_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SUBMISSION_ID" ]; then
    echo "✗ Failed to create submission"
    kill $SERVER_PID
    exit 1
fi

echo "✓ Created submission: $SUBMISSION_ID"
echo ""

# Wait a moment for background processing
sleep 2

# Query database to verify artifacts were persisted
echo "Verifying artifacts in database..."
QUERY_RESULT=$(uv run python -c "
import asyncio
import sqlite3
from pathlib import Path

db_path = Path('data/designdual.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute('''
    SELECT phase, canvas_url, audio_url, canvas_mime_type, audio_mime_type
    FROM submission_artifacts
    WHERE submission_id = ?
    ORDER BY
        CASE phase
            WHEN 'clarify' THEN 1
            WHEN 'estimate' THEN 2
            WHEN 'design' THEN 3
            WHEN 'explain' THEN 4
        END
''', ('$SUBMISSION_ID',))

artifacts = cursor.fetchall()
conn.close()

print(f'Found {len(artifacts)} artifact records:')
for phase, canvas_url, audio_url, canvas_mime, audio_mime in artifacts:
    print(f'  {phase}: canvas_url={canvas_url}, audio_url={audio_url}')
    print(f'           canvas_mime={canvas_mime}, audio_mime={audio_mime}')

# Verify we have exactly 4 records
if len(artifacts) != 4:
    print(f'ERROR: Expected 4 artifacts, found {len(artifacts)}')
    exit(1)

# Verify all phases are present
phases = {row[0] for row in artifacts}
expected_phases = {'clarify', 'estimate', 'design', 'explain'}
if phases != expected_phases:
    print(f'ERROR: Missing phases: {expected_phases - phases}')
    exit(1)

# Verify all canvas URLs are not None
for phase, canvas_url, _, _, _ in artifacts:
    if canvas_url is None:
        print(f'ERROR: Canvas URL is None for phase {phase}')
        exit(1)
    if not canvas_url.startswith('/uploads/'):
        print(f'ERROR: Invalid canvas URL format: {canvas_url}')
        exit(1)

print('')
print('✓ All validations passed!')
")

echo "$QUERY_RESULT"

# Check exit code
if [ $? -ne 0 ]; then
    echo "✗ Database validation failed"
    kill $SERVER_PID
    exit 1
fi

echo ""
echo "✓ Artifact persistence test PASSED"
echo ""

# Stop server
kill $SERVER_PID 2>/dev/null || true

# Cleanup
rm -rf "$TEMP_DIR"

echo "Test completed successfully!"
