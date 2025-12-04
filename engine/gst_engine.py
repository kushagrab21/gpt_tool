"""
GST Engine for CA Super Tool.
Handles GST ITC classification, reconciliation, and vendor-level compliance.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_section


def reconcile_3b_2b(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconcile GSTR-3B with GSTR-2B for ITC.
    
    Args:
        data: Dictionary containing ITC amounts and invoice lists
        
    Returns:
        Dictionary with reconciliation results
    """
    rulebook_section = get_section("gst_itc_engine") or {}
    reconciliation_rules = rulebook_section.get("gstr_3b_vs_2b_reconciliation", {})
    mismatch_categories = reconciliation_rules.get("mismatch_categories", {})
    
    # Fallback if YAML not loaded
    if not mismatch_categories:
        mismatch_categories = {
            "claimed_not_in_2b": {"description": "ITC claimed in 3B but invoice not in 2B"},
            "in_2b_not_claimed": {"description": "Eligible ITC from 2B not claimed in 3B"},
            "excess_claim": {"description": "Claimed > 2B reflection; verify eligibility"}
        }
    
    itc_3b = float(data.get("itc_3b", 0) or 0)
    itc_2b = float(data.get("itc_2b", 0) or 0)
    invoices_not_in_2b = data.get("invoices_not_in_2b", [])
    
    difference = itc_3b - itc_2b
    
    # Classify mismatch
    mismatch_type = None
    if difference > 0:
        if invoices_not_in_2b:
            mismatch_type = "claimed_not_in_2b"
        else:
            mismatch_type = "excess_claim"
    elif difference < 0:
        mismatch_type = "in_2b_not_claimed"
    
    result = {
        "itc_3b": itc_3b,
        "itc_2b": itc_2b,
        "difference": difference,
        "mismatch_type": mismatch_type,
        "mismatch_category": mismatch_categories.get(mismatch_type, {}).get("description", "") if mismatch_type else None,
        "invoices_not_in_2b": invoices_not_in_2b,
        "invoices_not_in_2b_count": len(invoices_not_in_2b),
        "requires_action": abs(difference) > 0.01
    }
    
    return result


def classify_itc(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify ITC as allowed, blocked, or conditional.
    
    Args:
        data: Dictionary containing invoice/transaction details
        
    Returns:
        Dictionary with ITC classification
    """
    rulebook_section = get_section("gst_itc_engine")
    
    itc_allowed = rulebook_section.get("itc_allowed", {})
    itc_blocked = rulebook_section.get("itc_blocked", {})
    itc_conditional = rulebook_section.get("itc_conditional", {})
    
    invoice_type = data.get("invoice_type", "").lower()
    description = data.get("description", "").lower()
    amount = float(data.get("amount", 0) or 0)
    
    classification = "allowed"
    reason = ""
    
    # Check blocked categories
    blocked_section = itc_blocked.get("blocked_under_section_17_5", {})
    
    if "motor vehicle" in description or "car" in description:
        classification = "blocked"
        reason = blocked_section.get("motor_vehicles", {}).get("rule", "Blocked under Section 17(5)")
    elif "food" in description or "beverage" in description:
        classification = "blocked"
        reason = blocked_section.get("food_beverages", {}).get("rule", "Blocked under Section 17(5)")
    elif "club" in description or "membership" in description:
        classification = "blocked"
        reason = blocked_section.get("club_membership", {}).get("rule", "Always blocked")
    elif "personal" in description:
        classification = "blocked"
        reason = blocked_section.get("personal_consumption", {}).get("rule", "Blocked always")
    
    # Check conditional
    if classification == "allowed":
        conditional_rules = itc_conditional.get("rules", {})
        if "mixed" in description or "partial" in description:
            classification = "conditional"
            reason = conditional_rules.get("partial_blocking_due_to_mixed_use", {}).get("rule", "Proportionate ITC allowed")
    
    return {
        "classification": classification,
        "reason": reason,
        "amount": amount,
        "invoice_type": invoice_type,
        "description": description
    }


def detect_itc_mismatch(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect ITC mismatches and flag issues.
    
    Args:
        data: Dictionary containing ITC comparison data
        
    Returns:
        Dictionary with mismatch detection results
    """
    rulebook_section = get_section("gst_itc_engine")
    reconciliation_rules = rulebook_section.get("gstr_3b_vs_2b_reconciliation", {})
    
    mismatches = []
    
    itc_3b = float(data.get("itc_3b", 0) or 0)
    itc_2b = float(data.get("itc_2b", 0) or 0)
    
    if abs(itc_3b - itc_2b) > 0.01:
        mismatches.append({
            "type": "amount_mismatch",
            "difference": itc_3b - itc_2b,
            "severity": "high" if abs(itc_3b - itc_2b) > 10000 else "medium"
        })
    
    invoices_not_in_2b = data.get("invoices_not_in_2b", [])
    if invoices_not_in_2b:
        mismatches.append({
            "type": "missing_invoices",
            "count": len(invoices_not_in_2b),
            "total_amount": sum(float(inv.get("amount", 0) or 0) for inv in invoices_not_in_2b),
            "severity": "high"
        })
    
    return {
        "mismatches": mismatches,
        "mismatch_count": len(mismatches),
        "requires_review": len(mismatches) > 0
    }


def vendor_level_itc(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze ITC at vendor level for compliance.
    
    Args:
        data: Dictionary containing vendor-level ITC data
        
    Returns:
        Dictionary with vendor-level analysis
    """
    vendors = data.get("vendors", [])
    rulebook_section = get_section("gst_itc_engine")
    
    vendor_analysis = []
    
    for vendor in vendors:
        gstin = vendor.get("gstin", "")
        itc_amount = float(vendor.get("itc_amount", 0) or 0)
        invoices_count = vendor.get("invoices_count", 0)
        compliant = vendor.get("compliant", True)
        
        analysis = {
            "gstin": gstin,
            "itc_amount": itc_amount,
            "invoices_count": invoices_count,
            "compliant": compliant,
            "flags": []
        }
        
        if not compliant:
            analysis["flags"].append("Supplier non-compliant - ITC may be blocked")
        
        if itc_amount > 100000 and not compliant:
            analysis["flags"].append("High-value non-compliant vendor - urgent review required")
        
        vendor_analysis.append(analysis)
    
    return {
        "vendor_analysis": vendor_analysis,
        "total_vendors": len(vendors),
        "non_compliant_count": sum(1 for v in vendor_analysis if not v["compliant"]),
        "total_itc": sum(v["itc_amount"] for v in vendor_analysis)
    }


def check_gst_errors(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for common GST errors and compliance issues.
    
    Args:
        data: Dictionary containing GST data to check
        
    Returns:
        Dictionary with error detection results
    """
    errors = []
    warnings = []
    
    # Check ITC eligibility
    itc_3b = float(data.get("itc_3b", 0) or 0)
    itc_2b = float(data.get("itc_2b", 0) or 0)
    
    if itc_3b > itc_2b * 1.1:  # More than 10% difference
        errors.append({
            "type": "excess_itc_claim",
            "message": f"ITC claimed ({itc_3b}) significantly exceeds 2B reflection ({itc_2b})",
            "severity": "high"
        })
    
    # Check for missing invoices
    invoices_not_in_2b = data.get("invoices_not_in_2b", [])
    if invoices_not_in_2b:
        warnings.append({
            "type": "missing_invoices_2b",
            "message": f"{len(invoices_not_in_2b)} invoices not found in GSTR-2B",
            "severity": "medium"
        })
    
    return {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "requires_action": len(errors) > 0 or len(warnings) > 0
    }

