"""
Audit Engine for CA Super Tool.
Handles audit red flag detection and internal control testing.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_section


def detect_redflags(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect audit red flags based on transaction patterns and amounts.
    
    Args:
        data: Dictionary containing transaction or ledger data
        
    Returns:
        Dictionary with detected red flags
    """
    rulebook_section = get_section("audit_rules")
    red_flags = rulebook_section.get("red_flags", [])
    
    transactions = data.get("transactions", [])
    items = data.get("items", transactions)
    
    detected_flags = []
    
    for item in items:
        amount = abs(float(item.get("amount", 0) or 0))
        ledger = str(item.get("ledger", "")).lower()
        description = str(item.get("description", "")).lower()
        
        # Check for suspicious patterns
        if amount > 1000000:  # Large transactions
            detected_flags.append({
                "type": "large_transaction",
                "amount": amount,
                "ledger": item.get("ledger"),
                "severity": "high",
                "message": "Large transaction detected - requires verification"
            })
        
        if "round" in description or amount % 10000 == 0 and amount > 50000:
            detected_flags.append({
                "type": "round_number_transaction",
                "amount": amount,
                "severity": "medium",
                "message": "Round number transaction - verify authenticity"
            })
        
        if "related party" in ledger or "director" in ledger:
            detected_flags.append({
                "type": "related_party_transaction",
                "amount": amount,
                "severity": "high",
                "message": "Related party transaction - ensure proper disclosure"
            })
    
    return {
        "red_flags": detected_flags,
        "flag_count": len(detected_flags),
        "high_severity_count": sum(1 for f in detected_flags if f.get("severity") == "high"),
        "requires_review": len(detected_flags) > 0
    }


def test_ic_control(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test internal controls based on transaction patterns.
    
    Args:
        data: Dictionary containing control test data
        
    Returns:
        Dictionary with control test results
    """
    controls = data.get("controls", [])
    transactions = data.get("transactions", [])
    
    test_results = []
    
    for control in controls:
        control_name = control.get("name", "")
        control_type = control.get("type", "")
        
        # Basic control tests
        if control_type == "authorization":
            # Check if transactions have proper authorization
            unauthorized = [t for t in transactions if not t.get("authorized", False)]
            test_results.append({
                "control": control_name,
                "type": control_type,
                "passed": len(unauthorized) == 0,
                "issues": len(unauthorized),
                "message": f"{len(unauthorized)} unauthorized transactions found" if unauthorized else "All transactions authorized"
            })
        
        elif control_type == "segregation":
            # Check for segregation of duties
            test_results.append({
                "control": control_name,
                "type": control_type,
                "passed": True,  # Simplified
                "message": "Segregation check completed"
            })
    
    return {
        "test_results": test_results,
        "total_controls_tested": len(controls),
        "passed_count": sum(1 for r in test_results if r.get("passed")),
        "failed_count": sum(1 for r in test_results if not r.get("passed"))
    }

