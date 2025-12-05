#!/bin/bash

# Unified Test Runner for CA Super Tool
# Starts server, runs tests, generates report, and shuts down server

set -e  # Exit on error

# Check dependencies
if ! command -v curl &> /dev/null; then
    echo "ERROR: curl is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required but not installed"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Log files
SERVER_LOG="$SCRIPT_DIR/server.log"
TEST_OUTPUT="$SCRIPT_DIR/test_output.log"
REPORT_OUTPUT="$SCRIPT_DIR/test_report.json"

# Clean up old logs
rm -f "$SERVER_LOG" "$TEST_OUTPUT" "$REPORT_OUTPUT"

echo "=========================================="
echo "CA Super Tool - Unified Test Runner"
echo "=========================================="
echo ""

# Step 0: Clean up old server processes
echo "[0/6] Cleaning old server processes..."

set +e
lsof -ti :8000 | xargs -r kill -9 2>/dev/null
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "uvicorn.*port 8000" 2>/dev/null
set -e

# Step 1: Start server in background
echo "[1/6] Starting server..."
cd "$PROJECT_ROOT"
"$SCRIPT_DIR/run_server.sh" > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!

# Function to cleanup server on exit
cleanup() {
    echo ""
    echo "[5/6] Shutting down server (PID: $SERVER_PID)..."

    # Temporarily disable exit-on-error
    set +e

    if [ ! -z "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null
        sleep 0.5
        kill -9 "$SERVER_PID" 2>/dev/null
    fi

    # Re-enable exit-on-error
    set -e
}

# Ensure cleanup on script exit
trap cleanup EXIT

# Step 2: Wait for server to be ready
echo "[2/6] Waiting for server to be ready..."
MAX_ATTEMPTS=67  # 20 seconds / 0.3 seconds ≈ 67 attempts
WAIT_INTERVAL=0.3
READY=0
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        READY=1
        break
    fi
    sleep $WAIT_INTERVAL
    ATTEMPT=$((ATTEMPT + 1))
    printf "."
done

echo ""

if [ $READY -eq 0 ]; then
    MAX_WAIT_SECONDS=20
    echo "ERROR: Server failed to start within ${MAX_WAIT_SECONDS} seconds"
    echo "Server log (last 20 lines):"
    tail -20 "$SERVER_LOG"
    exit 1
fi

echo "✓ Server is ready on http://localhost:8000"

# Step 3: Run tests
echo "[3/6] Running test suite..."
"$SCRIPT_DIR/run_tests.sh" > "$TEST_OUTPUT" 2>&1
TEST_EXIT_CODE=$?

# Step 4: Parse results and generate report
echo "[4/6] Generating test report..."
python3 "$SCRIPT_DIR/parse_results.py" "$TEST_OUTPUT" "$REPORT_OUTPUT"
PARSE_EXIT_CODE=$?

if [ $PARSE_EXIT_CODE -ne 0 ]; then
    echo "WARNING: Failed to parse test results"
fi

# Step 5: Display report
echo ""
if [ -f "$REPORT_OUTPUT" ]; then
    python3 -c "
import json, sys
try:
    with open('$REPORT_OUTPUT') as f:
        report = json.load(f)
    print('=' * 44)
    print(' LOCAL TEST REPORT '.center(44, '='))
    print('=' * 44)
    print(f\"Total Tests: {report.get('total', 0)}\")
    print(f\"Passed: {report.get('passed', 0)}\")
    print(f\"Failed: {report.get('failed', 0)}\")
    if report.get('failed_tests'):
        print('Failed Tests:')
        for test in report['failed_tests']:
            print(f\"  - {test}\")
    print(f\"Duration: {report.get('duration_sec', 0):.2f} s\")
    print(f\"Status: {report.get('status', 'UNKNOWN').upper()}\")
    print('=' * 44)
    sys.exit(0 if report.get('status') == 'pass' else 1)
except Exception as e:
    print(f'Error displaying report: {e}')
    sys.exit(1)
"
    FINAL_EXIT_CODE=$?
else
    echo "ERROR: Report file not generated"
    FINAL_EXIT_CODE=1
fi

# Exit with appropriate code
exit $FINAL_EXIT_CODE

