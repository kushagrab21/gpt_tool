"""
Sample API requests for testing the CA Super Tool.
These can be used to test the API endpoints.
"""

# Sample request for gst_reconcile_3b_books (runnable example)
SAMPLE_GST_RECONCILE_3B_BOOKS_REQUEST = {
    "task": "gst_reconcile_3b_books",
    "data": {
        "period": "2024-01",
        "gstin": "29ABCDE1234F1Z5",
        "books_data": {
            "total_sales": 1000000.00,
            "total_purchases": 500000.00,
            "output_tax": 180000.00,
            "input_tax": 90000.00
        },
        "gstr3b_data": {
            "total_turnover": 1000000.00,
            "output_tax": 180000.00,
            "input_tax_credit": 90000.00
        }
    },
    "settings": {
        "strict_mode": False,
        "tolerance": 0.01
    }
}

# Sample request for sales_invoice_prepare
SAMPLE_SALES_INVOICE_REQUEST = {
    "task": "sales_invoice_prepare",
    "data": {
        "customer": {
            "name": "ABC Pvt Ltd",
            "gstin": "07AAAAA0000A1Z5",
            "state_code": "07",
            "place_of_supply": "07",
            "billing_address": "123 Main St, Delhi",
            "shipping_address": "123 Main St, Delhi"
        },
        "seller": {
            "gstin": "09BBBBB0000B1Z6",
            "state_code": "09",
            "legal_name": "XYZ Traders"
        },
        "lines": [
            {
                "sku": "ITEM001",
                "description": "Widget",
                "quantity": 10,
                "unit_price": 100.0,
                "discount": 0.0,
                "hsn": "8409",
                "tax_rate": 18.0,
                "is_exempt": False
            },
            {
                "sku": "ITEM002",
                "description": "Gadget",
                "quantity": 5,
                "unit_price": 200.0,
                "discount": 50.0,
                "hsn": "8410",
                "tax_rate": 18.0,
                "is_exempt": False
            }
        ],
        "config": {
            "default_tax_rate": 18.0,
            "rounding_mode": "NEAREST",
            "invoice_prefix": "INV",
            "default_currency": "INR",
            "invoice_date": "2024-04-30",
            "invoice_number_seed": 1
        }
    },
    "settings": {}
}


def sample_sales_invoice_request():
    """
    Build a minimal JSON matching the micro structure for sales invoice preparation.
    Demonstrates a POST to /api/ca_super_tool with task="sales_invoice_prepare".
    """
    import requests
    import json
    
    url = "http://localhost:8000/api/ca_super_tool"
    
    print("\n" + "=" * 60)
    print("Testing sales_invoice_prepare endpoint...")
    print("=" * 60)
    print(f"Request: {json.dumps(SAMPLE_SALES_INVOICE_REQUEST, indent=2)}")
    print("\nSending POST request...")
    
    try:
        response = requests.post(url, json=SAMPLE_SALES_INVOICE_REQUEST)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Invoice generated successfully!")
            print(f"\nResponse: {json.dumps(result, indent=2)}")
            
            # Extract invoice from nested structure
            invoice = result.get("result", {}).get("result", {}).get("invoice", {})
            flags = result.get("result", {}).get("result", {}).get("flags", [])
            
            if invoice:
                print(f"\nInvoice Summary:")
                print(f"  Invoice Number: {invoice.get('invoice_number')}")
                print(f"  Invoice Date: {invoice.get('invoice_date')}")
                print(f"  Supply Type: {invoice.get('supply_type')}")
                print(f"  Invoice Type: {invoice.get('invoice_type')}")
                print(f"  Total Taxable: ₹{invoice.get('totals', {}).get('total_taxable', 0):,.2f}")
                print(f"  Total IGST: ₹{invoice.get('totals', {}).get('total_igst', 0):,.2f}")
                print(f"  Total CGST: ₹{invoice.get('totals', {}).get('total_cgst', 0):,.2f}")
                print(f"  Total SGST: ₹{invoice.get('totals', {}).get('total_sgst', 0):,.2f}")
                print(f"  Invoice Value: ₹{invoice.get('totals', {}).get('invoice_value', 0):,.2f}")
                
                if flags:
                    print(f"\nFlags: {flags}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"Error: {e}")

# Sample request for auto_gst_fetch_and_map
SAMPLE_GST_FETCH_REQUEST = {
    "task": "auto_gst_fetch_and_map",
    "data": {
        "period": "2024-01",
        "gstin": "29ABCDE1234F1Z5"
    },
    "settings": {}
}

# Sample request for tds_liability
SAMPLE_TDS_REQUEST = {
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
            },
            {
                "txn_id": "TXN002",
                "date": "2024-04-20",
                "party_name": "XYZ Contractors",
                "party_pan": "XYZAB5678G",
                "party_type": "RESIDENT",
                "nature_of_payment": "CONTRACT",
                "amount": 150000.0,
                "is_pan_available": True,
                "is_individual_or_huf": True,
                "fy": "2024-25"
            },
            {
                "txn_id": "TXN003",
                "date": "2024-05-10",
                "party_name": "Property Owner",
                "party_pan": "PROPERTY123",
                "party_type": "RESIDENT",
                "nature_of_payment": "RENT",
                "amount": 300000.0,
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


def sample_tds_liability_request():
    """
    Build a minimal JSON matching the micro structure for TDS liability.
    Demonstrates a POST to /api/ca_super_tool with task="tds_liability".
    """
    import requests
    import json
    
    url = "http://localhost:8000/api/ca_super_tool"
    
    print("Testing tds_liability endpoint...")
    print(f"Request: {json.dumps(SAMPLE_TDS_REQUEST, indent=2)}")
    print("\nSending POST request...")
    
    try:
        response = requests.post(url, json=SAMPLE_TDS_REQUEST)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"Error: {e}")

# Sample request for gst_reconcile_2b_3b
SAMPLE_GST_RECONCILE_2B_3B_REQUEST = {
    "task": "gst_reconcile_2b_3b",
    "data": {
        "period": "2024-01",
        "gstin": "29ABCDE1234F1Z5"
    },
    "settings": {}
}

# Example usage - POST to localhost:8000/api/ca_super_tool
if __name__ == "__main__":
    import requests
    import json
    
    # Example: Test gst_reconcile_3b_books
    url = "http://localhost:8000/api/ca_super_tool"
    
    print("=" * 60)
    print("Testing gst_reconcile_3b_books endpoint...")
    print("=" * 60)
    print(f"Request: {json.dumps(SAMPLE_GST_RECONCILE_3B_BOOKS_REQUEST, indent=2)}")
    print("\nSending POST request...")
    
    try:
        response = requests.post(url, json=SAMPLE_GST_RECONCILE_3B_BOOKS_REQUEST)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Testing tds_liability endpoint...")
    print("=" * 60)
    sample_tds_liability_request()
    
    # Test auto entries workflow
    sample_auto_entries_from_tds()
    
    # Test sales invoice
    sample_sales_invoice_request()


def sample_auto_entries_from_tds():
    """
    Demonstrates the workflow:
    1. Call TDS engine to get liability calculations
    2. Feed that output into auto_entries to generate journal entries
    
    This simulates the payload instead of making real HTTP calls.
    """
    import requests
    import json
    
    url = "http://localhost:8000/api/ca_super_tool"
    
    print("\n" + "=" * 60)
    print("Workflow: TDS Liability → Auto Journal Entries")
    print("=" * 60)
    
    # Step 1: Call TDS engine
    print("\nStep 1: Calling TDS liability engine...")
    tds_request = SAMPLE_TDS_REQUEST.copy()
    
    try:
        tds_response = requests.post(url, json=tds_request)
        if tds_response.status_code == 200:
            tds_result = tds_response.json()
            print("✓ TDS calculation completed")
            
            # Extract the result from the response structure
            # The actual result is in result.result (nested structure from UARE pipeline)
            tds_payload = tds_result.get("result", {}).get("result", {})
            
            # Step 2: Feed TDS result into auto_entries
            print("\nStep 2: Generating journal entries from TDS result...")
            
            auto_entries_request = {
                "task": "auto_entries",
                "data": {
                    "source": "tds_liability",
                    "payload": tds_payload,
                    "config": {
                        "tds_payable_ledger": "TDS Payable",
                        "tds_expense_ledger": "TDS Expense",
                        "default_date": "2024-04-30",
                        "entry_prefix": "AUTO"
                    }
                },
                "settings": {}
            }
            
            print(f"Auto Entries Request: {json.dumps(auto_entries_request, indent=2)}")
            
            auto_entries_response = requests.post(url, json=auto_entries_request)
            if auto_entries_response.status_code == 200:
                auto_entries_result = auto_entries_response.json()
                print("\n✓ Journal entries generated successfully!")
                print(f"\nResponse: {json.dumps(auto_entries_result, indent=2)}")
                
                # Extract entries
                entries = auto_entries_result.get("result", {}).get("result", {}).get("entries", [])
                summary = auto_entries_result.get("result", {}).get("result", {}).get("summary", {})
                
                print(f"\nSummary:")
                print(f"  Total entries: {summary.get('total_entries', 0)}")
                print(f"  Total amount: ₹{summary.get('total_amount', 0):,.2f}")
                
                if entries:
                    print(f"\nSample Entry:")
                    print(f"  Entry ID: {entries[0].get('entry_id')}")
                    print(f"  Date: {entries[0].get('date')}")
                    print(f"  Debit: {entries[0].get('debit_account')} - ₹{entries[0].get('amount'):,.2f}")
                    print(f"  Credit: {entries[0].get('credit_account')} - ₹{entries[0].get('amount'):,.2f}")
                    print(f"  Narration: {entries[0].get('narration')}")
                    print(f"  Tags: {entries[0].get('tags')}")
            else:
                print(f"Error generating entries: {auto_entries_response.status_code}")
                print(auto_entries_response.text)
        else:
            print(f"Error calculating TDS: {tds_response.status_code}")
            print(tds_response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running:")
        print("  uvicorn main:app --reload")
        print("\nSimulating workflow with mock data...")
        
        # Simulate with mock TDS payload
        mock_tds_payload = {
            "micro": {
                "transactions": [
                    {
                        "txn_id": "TXN001",
                        "fy": "2024-25",
                        "section": "194J",
                        "party_pan": "ABCDE1234F",
                        "party_name": "ABC Services",
                        "gross_amount": 50000.0,
                        "tds_amount": 5000.0
                    }
                ]
            },
            "meso": {
                "by_party": [
                    {
                        "fy": "2024-25",
                        "section": "194J",
                        "party_pan": "ABCDE1234F",
                        "party_name": "ABC Services",
                        "total_gross": 50000.0,
                        "total_tds": 5000.0,
                        "txn_count": 1
                    }
                ]
            },
            "macro": {
                "summary": {
                    "total_tds_all": 5000.0
                }
            }
        }
        
        auto_entries_request = {
            "task": "auto_entries",
            "data": {
                "source": "tds_liability",
                "payload": mock_tds_payload,
                "config": {
                    "tds_payable_ledger": "TDS Payable",
                    "tds_expense_ledger": "TDS Expense",
                    "default_date": "2024-04-30",
                    "entry_prefix": "AUTO"
                }
            },
            "settings": {}
        }
        
        print(f"\nMock Auto Entries Request: {json.dumps(auto_entries_request, indent=2)}")
        print("\n(To test with real API, start the server and run this function)")
        
    except Exception as e:
        print(f"Error: {e}")


# Sample request for auto_entries (direct example)
SAMPLE_AUTO_ENTRIES_REQUEST = {
    "task": "auto_entries",
    "data": {
        "source": "tds_liability",
        "payload": {
            "micro": {
                "transactions": [
                    {
                        "txn_id": "TXN001",
                        "fy": "2024-25",
                        "section": "194J",
                        "party_pan": "ABCDE1234F",
                        "party_name": "ABC Services",
                        "gross_amount": 50000.0,
                        "tds_amount": 5000.0
                    }
                ]
            },
            "meso": {
                "by_party": [
                    {
                        "fy": "2024-25",
                        "section": "194J",
                        "party_pan": "ABCDE1234F",
                        "party_name": "ABC Services",
                        "total_gross": 50000.0,
                        "total_tds": 5000.0,
                        "txn_count": 1
                    }
                ]
            },
            "macro": {
                "summary": {
                    "total_tds_all": 5000.0
                }
            }
        },
        "config": {
            "tds_payable_ledger": "TDS Payable",
            "tds_expense_ledger": "TDS Expense",
            "default_date": "2024-04-30",
            "entry_prefix": "AUTO"
        }
    },
    "settings": {}
}

