"""
Comprehensive Backend Test Suite for CA Super Tool
Tests multiple payload types and generates a detailed Markdown report.
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import traceback
import os

# Try to use FastAPI TestClient first (no server needed)
try:
    from fastapi.testclient import TestClient
    from main import app
    USE_TEST_CLIENT = True
    test_client = TestClient(app)
except ImportError:
    USE_TEST_CLIENT = False
    test_client = None

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")  # Change to Render URL if testing production
API_ENDPOINT = f"{BASE_URL}/api/ca_super_tool"

# Test results storage
test_results: List[Dict[str, Any]] = []


def run_test(test_name: str, payload: Dict[str, Any], expected_status: int = 200) -> Dict[str, Any]:
    """
    Run a single test against the API endpoint.
    
    Args:
        test_name: Name of the test
        payload: Request payload
        expected_status: Expected HTTP status code
        
    Returns:
        Test result dictionary
    """
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    result = {
        "test_name": test_name,
        "payload": payload,
        "timestamp": datetime.now().isoformat(),
        "status_code": None,
        "response": None,
        "error": None,
        "error_trace": None,
        "passed": False,
        "expected_status": expected_status
    }
    
    try:
        # Use TestClient if available (no server needed), otherwise use requests
        if USE_TEST_CLIENT:
            response = test_client.post("/api/ca_super_tool", json=payload)
        else:
            response = requests.post(API_ENDPOINT, json=payload, timeout=10)
        
        result["status_code"] = response.status_code
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = {"raw": response.text if hasattr(response, 'text') else str(response)}
        
        # Check if test passed
        if response.status_code == expected_status:
            result["passed"] = True
            print(f"✓ PASSED - Status: {response.status_code}")
        else:
            result["passed"] = False
            print(f"✗ FAILED - Expected {expected_status}, got {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        result["error"] = "ConnectionError: Could not connect to server"
        result["error_trace"] = "Server may not be running. Start with: uvicorn main:app --reload"
        result["passed"] = False
        print(f"✗ FAILED - Connection error")
        
    except requests.exceptions.Timeout:
        result["error"] = "Timeout: Request took too long"
        result["passed"] = False
        print(f"✗ FAILED - Timeout")
        
    except Exception as e:
        result["error"] = str(e)
        result["error_trace"] = traceback.format_exc()
        result["passed"] = False
        print(f"✗ FAILED - Exception: {e}")
    
    test_results.append(result)
    return result


def generate_markdown_report() -> str:
    """
    Generate a comprehensive Markdown report from test results.
    
    Returns:
        Markdown report as string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate summary
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["passed"])
    failed_tests = total_tests - passed_tests
    
    report = f"""# CA Super Tool Backend Test Report

**Generated:** {timestamp}  
**API Endpoint:** {API_ENDPOINT}  
**Total Tests:** {total_tests}  
**Passed:** {passed_tests}  
**Failed:** {failed_tests}

---

## Summary Table

| Test # | Test Name | Status | HTTP Code | Result |
|--------|-----------|--------|-----------|--------|
"""
    
    for idx, result in enumerate(test_results, 1):
        status_icon = "✅ PASS" if result["passed"] else "❌ FAIL"
        status_code = result["status_code"] or "N/A"
        result["test_number"] = idx
        report += f"| {idx} | {result['test_name']} | {status_icon} | {status_code} | {'Accepted' if result['passed'] else 'Rejected/Error'} |\n"
    
    report += "\n---\n\n## Detailed Test Results\n\n"
    
    # Detailed results for each test
    for idx, result in enumerate(test_results, 1):
        report += f"### Test {idx}: {result['test_name']}\n\n"
        report += f"**Status:** {'✅ PASSED' if result['passed'] else '❌ FAILED'}\n\n"
        report += f"**Timestamp:** {result['timestamp']}\n\n"
        
        report += "**Request Payload:**\n```json\n"
        report += json.dumps(result["payload"], indent=2)
        report += "\n```\n\n"
        
        if result["status_code"]:
            report += f"**HTTP Status Code:** {result['status_code']}\n\n"
        
        if result["response"]:
            report += "**Response:**\n```json\n"
            # Truncate very long responses
            response_str = json.dumps(result["response"], indent=2)
            if len(response_str) > 2000:
                response_str = response_str[:2000] + "\n... (truncated)"
            report += response_str
            report += "\n```\n\n"
        
        if result["error"]:
            report += f"**Error:** {result['error']}\n\n"
        
        if result["error_trace"]:
            report += "**Error Trace:**\n```\n"
            report += result["error_trace"][:1000]  # Truncate long traces
            if len(result["error_trace"]) > 1000:
                report += "\n... (truncated)"
            report += "\n```\n\n"
        
        # Analysis
        if not result["passed"]:
            if result["status_code"] == 422:
                report += "**Analysis:** Validation error - Check payload structure matches Pydantic model.\n\n"
            elif result["status_code"] == 404:
                report += "**Analysis:** Endpoint not found - Check API route configuration.\n\n"
            elif result["status_code"] and 400 <= result["status_code"] < 500:
                report += "**Analysis:** Client error - Check request format and task name.\n\n"
            elif result["status_code"] and 500 <= result["status_code"] < 600:
                report += "**Analysis:** Server error - Check backend logs for exceptions.\n\n"
            elif result["error"] and "Connection" in result["error"]:
                report += "**Analysis:** Server not running - Start the FastAPI server.\n\n"
            else:
                report += "**Analysis:** Unexpected error - Review error details above.\n\n"
        
        report += "---\n\n"
    
    # Conclusion section
    report += "## Conclusion\n\n"
    
    if failed_tests == 0:
        report += "✅ **All tests passed!** The backend is correctly accepting and processing all payload types.\n\n"
    else:
        report += f"⚠️ **{failed_tests} test(s) failed.** Review the detailed results above.\n\n"
    
    report += "### Recommendations\n\n"
    
    # Generate recommendations based on failures
    recommendations = []
    
    connection_errors = [r for r in test_results if r["error"] and "Connection" in str(r["error"])]
    if connection_errors:
        recommendations.append("- **Server Connection:** Ensure the FastAPI server is running with `uvicorn main:app --reload`")
    
    validation_errors = [r for r in test_results if r["status_code"] == 422]
    if validation_errors:
        recommendations.append("- **Validation Errors:** Verify that the Pydantic model `SuperToolRequest` accepts all required fields (`task`, `data`, `settings`)")
    
    task_errors = [r for r in test_results if r["status_code"] == 200 and r["response"] and "error" in str(r["response"]).lower() and "unknown task" in str(r["response"]).lower()]
    if task_errors:
        recommendations.append("- **Unknown Tasks:** Some tasks are not registered in the dispatcher. Add them to `engine/dispatcher.py` or handle them gracefully")
    
    status_errors = [r for r in test_results if r["status_code"] and r["status_code"] != r["expected_status"] and r["status_code"] != 200]
    if status_errors:
        recommendations.append("- **Status Code Mismatches:** Review endpoint error handling to ensure appropriate HTTP status codes")
    
    if not recommendations:
        recommendations.append("- ✅ No issues detected. Backend is functioning correctly.")
    
    for rec in recommendations:
        report += f"{rec}\n"
    
    report += "\n### Next Steps\n\n"
    
    if failed_tests > 0:
        report += "1. Review failed test details above\n"
        report += "2. Fix identified issues in the backend code\n"
        report += "3. Re-run this test suite to verify fixes\n"
        report += "4. Update ChatGPT Custom GPT action configuration if needed\n"
    else:
        report += "1. ✅ Backend is ready for ChatGPT Custom GPT integration\n"
        report += "2. Deploy to Render (if not already deployed)\n"
        report += "3. Update Custom GPT action URL to point to deployed endpoint\n"
        report += "4. Test end-to-end with ChatGPT\n"
    
    report += "\n---\n\n"
    report += f"*Report generated by CA Super Tool Test Suite*\n"
    
    return report


def main():
    """Run all tests and generate report."""
    print("="*60)
    print("CA Super Tool Backend Test Suite")
    print("="*60)
    print(f"Testing endpoint: {API_ENDPOINT}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Schedule III Classification
    run_test(
        "Schedule III Classification",
        {
            "task": "schedule3_classification",
            "data": {
                "items": [
                    {"ledger": "Unsecured Loan from Director", "amount": 400000}
                ]
            },
            "settings": {}
        }
    )
    
    # Test 2: GST 3B vs 2B Reconciliation
    run_test(
        "GST 3B vs 2B Reconciliation",
        {
            "task": "gst_3b_2b_reconciliation",
            "data": {
                "itc_3b": 180000,
                "itc_2b": 160000,
                "invoices_not_in_2b": [
                    {"gstin": "24AAAAA1111A1Z5", "amount": 12000},
                    {"gstin": "07BBBBB2222B1Z1", "amount": 8000}
                ]
            },
            "settings": {}
        }
    )
    
    # Test 3: TDS Section Classification
    run_test(
        "TDS Section Classification",
        {
            "task": "tds_section_classification",
            "data": {
                "invoice_amount": 125000,
                "description": "Professional Fees to CA"
            },
            "settings": {}
        }
    )
    
    # Test 4: Auto Journal Suggestion
    run_test(
        "Auto Journal Suggestion",
        {
            "task": "auto_journal_suggestion",
            "data": {
                "transaction": "Paid rent of 360000 to landlord"
            },
            "settings": {}
        }
    )
    
    # Test 5: Negative Test - Unsupported Task
    run_test(
        "Negative Test - Unsupported Task",
        {
            "task": "structured_reasoning",
            "data": {},
            "settings": {}
        },
        expected_status=200  # Backend returns 200 with error in response body
    )
    
    # Generate and save report
    print("\n" + "="*60)
    print("Generating Markdown Report...")
    print("="*60)
    
    report = generate_markdown_report()
    
    # Save to file
    report_path = "backend_test_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ Report generated successfully!")
    print(f"📄 File saved to: {report_path}")
    print(f"📊 Summary: {sum(1 for r in test_results if r['passed'])}/{len(test_results)} tests passed")
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for result in test_results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} - {result['test_name']}")
    
    return report_path


if __name__ == "__main__":
    try:
        report_path = main()
        print(f"\n📁 Full report available at: {report_path}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        traceback.print_exc()

