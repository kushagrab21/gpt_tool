"""
Test script for POST /api/ca_super_tool endpoint.
This demonstrates how to send valid requests to the endpoint.
"""

import requests
import json

# Base URL - change this to your deployed URL
BASE_URL = "http://localhost:8000"  # For local testing
# BASE_URL = "https://your-service-name.onrender.com"  # For production

def test_schedule3_classification():
    """Test the exact payload structure from the user."""
    url = f"{BASE_URL}/api/ca_super_tool"
    
    payload = {
        "task": "schedule3_classification",
        "data": {
            "items": [
                {"ledger": "Unsecured Loan from Director", "amount": 400000}
            ]
        },
        "settings": {}
    }
    
    print("Testing POST /api/ca_super_tool")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Request accepted successfully!")
            print(f"\nResponse:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to server.")
        print("Make sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_tds_liability():
    """Test with a known task (TDS liability)."""
    url = f"{BASE_URL}/api/ca_super_tool"
    
    payload = {
        "task": "tds_liability",
        "data": {
            "transactions": [
                {
                    "txn_id": "TXN001",
                    "date": "2024-04-15",
                    "party_name": "ABC Services",
                    "party_pan": "ABCDE1234F",
                    "party_type": "RESIDENT",
                    "nature_of_payment": "PROFESSIONAL_FEES",
                    "amount": 50000.0,
                    "is_pan_available": True,
                    "is_individual_or_huf": False,
                    "fy": "2024-25"
                }
            ]
        },
        "settings": {
            "default_fy": "2024-25"
        }
    }
    
    print("\n" + "="*60)
    print("Testing with TDS liability task")
    print("="*60)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Request accepted successfully!")
            print(f"Status: {result.get('status')}")
            print(f"Capsule: {result.get('capsule', '')[:50]}...")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    # Test with the exact payload from the user
    test_schedule3_classification()
    
    # Test with a known task
    test_tds_liability()

