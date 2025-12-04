"""
Demo script to show what the CA Super Tool does with readable outputs.
"""

from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_schedule3_classification():
    """Demo: Classify ledger items into Schedule III categories."""
    print_section("DEMO 1: Schedule III Classification")
    print("\n📋 What it does: Classifies accounting ledger items into Schedule III")
    print("   categories for financial statement preparation.\n")
    
    payload = {
        "task": "schedule3_classification",
        "data": {
            "items": [
                {"ledger": "Unsecured Loan from Director", "amount": 400000},
                {"ledger": "Bank Current Account", "amount": 50000},
                {"ledger": "Office Rent", "amount": 120000}
            ]
        },
        "settings": {}
    }
    
    print("📤 Request:")
    print(json.dumps(payload, indent=2))
    
    response = client.post("/api/ca_super_tool", json=payload)
    result = response.json()
    
    print("\n📥 Response:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        classified = result['result']['result'].get('classified', {})
        summary = result['result']['result'].get('summary', {})
        
        print("\n✅ Classification Results:")
        for category, items in classified.items():
            print(f"\n  📁 Category: {category}")
            total = summary.get(category, {}).get('total', 0)
            print(f"     Total Amount: ₹{total:,.2f}")
            for item in items:
                print(f"     • {item['ledger']}: ₹{item['amount']:,.2f}")

def demo_tds_classification():
    """Demo: Classify TDS section based on payment description."""
    print_section("DEMO 2: TDS Section Classification")
    print("\n📋 What it does: Determines which TDS section applies to a payment")
    print("   based on the nature of payment (e.g., Professional Fees → Section 194J)\n")
    
    payload = {
        "task": "tds_section_classification",
        "data": {
            "invoice_amount": 125000,
            "description": "Professional Fees to CA"
        },
        "settings": {}
    }
    
    print("📤 Request:")
    print(json.dumps(payload, indent=2))
    
    response = client.post("/api/ca_super_tool", json=payload)
    result = response.json()
    
    print("\n📥 Response:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        output = result['result']['result']
        print("\n✅ TDS Classification:")
        print(f"  Section: {output.get('section', 'N/A')}")
        print(f"  Description: {output.get('description', 'N/A')}")
        print(f"  Amount: ₹{output.get('invoice_amount', 0):,.2f}")
        if 'tds_rate' in output:
            print(f"  TDS Rate: {output.get('tds_rate')}%")
            tds_amount = output.get('invoice_amount', 0) * (output.get('tds_rate', 0) / 100)
            print(f"  TDS Amount: ₹{tds_amount:,.2f}")

def demo_gst_reconciliation():
    """Demo: GST 3B vs 2B reconciliation."""
    print_section("DEMO 3: GST 3B vs 2B Reconciliation")
    print("\n📋 What it does: Reconciles ITC (Input Tax Credit) between GSTR-3B")
    print("   and GSTR-2B to identify mismatches and missing invoices.\n")
    
    payload = {
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
    
    print("📤 Request:")
    print(json.dumps(payload, indent=2))
    
    response = client.post("/api/ca_super_tool", json=payload)
    result = response.json()
    
    print("\n📥 Response:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        output = result['result']['result']
        print("\n✅ Reconciliation Results:")
        print(f"  ITC in 3B: ₹{output.get('itc_3b', 0):,.2f}")
        print(f"  ITC in 2B: ₹{output.get('itc_2b', 0):,.2f}")
        difference = output.get('itc_3b', 0) - output.get('itc_2b', 0)
        print(f"  Difference: ₹{difference:,.2f}")
        if difference > 0:
            print(f"  ⚠️  Warning: ITC claimed in 3B but not available in 2B")

def demo_auto_journal_suggestion():
    """Demo: Auto journal entry suggestion."""
    print_section("DEMO 4: Auto Journal Entry Suggestion")
    print("\n📋 What it does: Automatically suggests journal entries based on")
    print("   transaction descriptions (e.g., 'Paid rent' → Debit Rent, Credit Bank)\n")
    
    payload = {
        "task": "auto_journal_suggestion",
        "data": {
            "transaction": "Paid rent of 360000 to landlord"
        },
        "settings": {}
    }
    
    print("📤 Request:")
    print(json.dumps(payload, indent=2))
    
    response = client.post("/api/ca_super_tool", json=payload)
    result = response.json()
    
    print("\n📥 Response:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        output = result['result']['result']
        print("\n✅ Suggested Journal Entry:")
        if 'entries' in output:
            for entry in output.get('entries', []):
                print(f"\n  Entry ID: {entry.get('entry_id', 'N/A')}")
                print(f"  Date: {entry.get('date', 'N/A')}")
                print(f"  Debit: {entry.get('debit_account', 'N/A')} - ₹{entry.get('amount', 0):,.2f}")
                print(f"  Credit: {entry.get('credit_account', 'N/A')} - ₹{entry.get('amount', 0):,.2f}")
                print(f"  Narration: {entry.get('narration', 'N/A')}")

def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  CA SUPER TOOL - DEMONSTRATION")
    print("="*70)
    print("\nThis tool is a Unified Accounting Reasoning Engine (UARE) that")
    print("provides various accounting and tax-related automation tasks.")
    print("\nSupported capabilities:")
    print("  • Schedule III classification for financial statements")
    print("  • TDS section classification and liability calculation")
    print("  • GST reconciliation (3B vs 2B, 3B vs Books, etc.)")
    print("  • Auto journal entry generation")
    print("  • Sales invoice preparation with GST")
    print("  • Tax audit automation")
    print("  • Bank reconciliation")
    print("  • Financial statement mapping")
    print("  • And many more...")
    
    try:
        demo_schedule3_classification()
        demo_tds_classification()
        demo_gst_reconciliation()
        demo_auto_journal_suggestion()
        
        print_section("SUMMARY")
        print("\n✅ All demos completed successfully!")
        print("\nThe CA Super Tool processes accounting tasks through a pipeline:")
        print("  1. Normalize input data")
        print("  2. Fractal expansion (micro/meso/macro structure)")
        print("  3. Invariant enforcement (data validation)")
        print("  4. Dispatch to specialized engine")
        print("  5. Return structured response with audit capsule")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

