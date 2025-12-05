#!/usr/bin/env python3
"""
Parse test output and generate structured test report.
"""

import sys
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any


def parse_test_output(test_output_path: str) -> Dict[str, Any]:
    """
    Parse test output log and extract test results.
    Finds the last valid JSON summary object printed by the test suite.
    
    Returns:
        Dictionary with keys: total, passed, failed, failed_tests, duration_sec, status
    """
    try:
        with open(test_output_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "failed_tests": [],
            "duration_sec": 0.0,
            "status": "error",
            "error": "Test output file not found"
        }
    
    # Find the last valid JSON object (summary from test suite)
    summary_json = None
    
    # Scan lines from end to beginning to find the last JSON object
    for line in reversed(lines):
        line = line.strip()
        # Look for lines that start with '{' and end with '}'
        if line.startswith('{') and line.endswith('}'):
            try:
                parsed = json.loads(line)
                # Check if it has the expected summary structure
                if isinstance(parsed, dict) and "total" in parsed and "passed" in parsed and "failed" in parsed:
                    summary_json = parsed
                    break
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, continue searching
                continue
    
    # If no valid summary JSON found, return error
    if summary_json is None:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "failed_tests": [],
            "duration_sec": 0.0,
            "status": "error",
            "error": "No valid JSON summary found in test output"
        }
    
    # Extract values from summary JSON
    total = summary_json.get("total", 0)
    passed = summary_json.get("passed", 0)
    failed = summary_json.get("failed", 0)
    failed_tests = summary_json.get("failed_tests", [])
    duration_sec = summary_json.get("duration_sec", 0.0)
    status = summary_json.get("status", "fail" if failed > 0 else "pass")
    
    # Ensure failed_tests is a list
    if not isinstance(failed_tests, list):
        failed_tests = []
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "failed_tests": failed_tests,
        "duration_sec": round(duration_sec, 2),
        "status": status
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_results.py <test_output.log> [report.json]", file=sys.stderr)
        sys.exit(1)
    
    test_output_path = sys.argv[1]
    report_output_path = sys.argv[2] if len(sys.argv) > 2 else "test_report.json"
    
    report = parse_test_output(test_output_path)
    
    # If no valid JSON summary found, exit with nonzero code
    if report.get("status") == "error" and "error" in report:
        print(f"Error: {report.get('error')}", file=sys.stderr)
        sys.exit(1)
    
    # Write JSON report
    try:
        with open(report_output_path, 'w') as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()

