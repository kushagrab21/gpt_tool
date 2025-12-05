"""
Test script to verify fractal structure is exposed at top level.
Tests that micro/meso/macro are accessible directly from result.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/ca_super_tool"

def test_fractal_structure(task: str, payload: dict, test_name: str):
    """Test that fractal structure is properly exposed."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Task: {task}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(API_ENDPOINT, json={
            "task": task,
            "data": payload,
            "settings": {}
        }, timeout=10)
        
        if response.status_code != 200:
            print(f"✗ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        # Check response structure
        if "result" not in result:
            print("✗ Error: 'result' key missing in response")
            return False
        
        result_data = result["result"]
        
        # Check for fractal structure at top level
        print("\nChecking fractal structure...")
        
        micro = result_data.get("micro")
        meso = result_data.get("meso")
        macro = result_data.get("macro")
        summary = result_data.get("summary")
        reasoning_tree = result_data.get("reasoning_tree")
        metadata = result_data.get("metadata")
        
        # Report findings
        print(f"\n✓ Micro keys: {list(micro.keys()) if micro and isinstance(micro, dict) else 'None or not dict'}")
        print(f"✓ Meso keys: {list(meso.keys()) if meso and isinstance(meso, dict) else 'None or not dict'}")
        print(f"✓ Macro keys: {list(macro.keys()) if macro and isinstance(macro, dict) else 'None or not dict'}")
        print(f"✓ Summary: {'Present' if summary else 'Missing'}")
        print(f"✓ Reasoning tree: {'Present' if reasoning_tree else 'Missing'}")
        print(f"✓ Metadata: {'Present' if metadata else 'Missing'}")
        
        # Verify structure
        success = True
        if not micro:
            print("✗ ERROR: 'micro' is missing or empty")
            success = False
        if not meso:
            print("✗ ERROR: 'meso' is missing or empty")
            success = False
        if not macro:
            print("✗ ERROR: 'macro' is missing or empty")
            success = False
        if not metadata:
            print("✗ ERROR: 'metadata' is missing")
            success = False
        
        if success:
            print("\n✓ All fractal structure keys are present at top level!")
        
        # Show sample structure
        print(f"\nSample structure:")
        print(f"  result.micro: {type(micro).__name__}")
        print(f"  result.meso: {type(meso).__name__}")
        print(f"  result.macro: {type(macro).__name__}")
        if summary:
            print(f"  result.summary: {type(summary).__name__}")
        if reasoning_tree:
            print(f"  result.reasoning_tree: {type(reasoning_tree).__name__}")
        
        return success
        
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to server.")
        print("Make sure the server is running:")
        print("  uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Testing Fractal Structure Exposure")
    print("="*60)
    
    # Test 1: Generic rule expansion (should have reasoning_tree)
    test1_success = test_fractal_structure(
        task="generic_rule_expansion",
        payload={
            "rule_section": "schedule_iii_engine",
            "rule_key": "schedule_iii_mapping_rules",
            "input_data": {"ledger": "Trade Payables", "amount": 100000}
        },
        test_name="Generic Rule Expansion"
    )
    
    # Test 2: BS Classification
    test2_success = test_fractal_structure(
        task="bs_auto_classification",
        payload={
            "items": [
                {"ledger": "Trade Payables", "amount": 100000, "balance_type": "credit"},
                {"ledger": "Share Capital", "amount": 500000, "balance_type": "credit"}
            ]
        },
        test_name="BS Auto Classification"
    )
    
    # Test 3: Cashflow mapping
    test3_success = test_fractal_structure(
        task="cashflow_auto_mapping",
        payload={
            "items": [
                {"ledger": "Purchase of Machinery", "amount": 500000, "date": "2024-01-15"}
            ]
        },
        test_name="Cashflow Auto Mapping"
    )
    
    # Test 4: Schedule III Classification
    test4_success = test_fractal_structure(
        task="schedule3_classification",
        payload={
            "items": [
                {"ledger": "Unsecured Loan from Director", "amount": 400000}
            ]
        },
        test_name="Schedule III Classification"
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Generic Rule Expansion: {'✓ PASS' if test1_success else '✗ FAIL'}")
    print(f"BS Auto Classification: {'✓ PASS' if test2_success else '✗ FAIL'}")
    print(f"Cashflow Auto Mapping: {'✓ PASS' if test3_success else '✗ FAIL'}")
    print(f"Schedule III Classification: {'✓ PASS' if test4_success else '✗ FAIL'}")
    
    all_passed = all([test1_success, test2_success, test3_success, test4_success])
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

