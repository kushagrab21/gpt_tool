from .utils import call_api
import json
import time


def pretty(x):
    print(json.dumps(x, indent=2))


TESTS = [
    ("schedule3_classification",
     {"items":[{"ledger":"Unsecured Loan from Director","amount":400000}]}),

    ("gst_3b_2b_reconciliation",
     {"itc_3b":250000, "itc_2b":190000, "invoices_not_in_2b":[{"gstin":"X", "amount":10000}]}),

    ("tds_section_classification",
     {"invoice_amount":145000, "description":"professional fees"}),

    ("auto_journal_suggestion",
     {"transaction":"Paid rent of 75000 to landlord"}),

    ("bs_auto_classification",
     {"items":[
         {"ledger":"Share Capital","amount":1000000},
         {"ledger":"Trade Payables","amount":110000}
     ]}),

    ("cashflow_auto_mapping",
     {"items":[{"ledger":"Sale of goods","amount":500000}]}),

    ("bank_reco_matching",
     {"books":[{"desc":"NEFT from A","amount":50000, "date":"2025-03-01"}],
      "bank":[{"desc":"NEFT-CR A","amount":50000, "date":"2025-03-02"}]}),

    ("generic_rule_expansion",
     {"rule":"classify unsecured loan",
      "context":{"ledger":"unsecured loan","amount":400000},
     })
]


def run_tests():
    start_time = time.time()
    total = len(TESTS)
    passed = 0
    failed = 0
    failed_tests = []
    
    for task, data in TESTS:
        print("\n=======================")
        print("Running:", task)
        print("=======================")

        try:
            result = call_api(task, data)
            pretty(result)
            passed += 1
        except Exception as e:
            failed += 1
            failed_tests.append(task)
            print(f"ERROR: {task} failed with exception: {str(e)}")
    
    duration_sec = time.time() - start_time
    status = "pass" if failed == 0 else "fail"
    
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "failed_tests": failed_tests,
        "duration_sec": round(duration_sec, 2),
        "status": status
    }
    
    print(json.dumps(summary))


if __name__ == "__main__":
    run_tests()

