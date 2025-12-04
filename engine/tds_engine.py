"""
TDS Engine for CA Super Tool.
Handles TDS section classification, ledger tagging, and default detection.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_section


def classify_section(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify payment into appropriate TDS section.
    
    Args:
        data: Dictionary containing invoice/payment details
        
    Returns:
        Dictionary with TDS section classification
    """
    rulebook_section = get_section("tds_tcs_engine") or {}
    tds_sections = rulebook_section.get("tds_sections", {})
    
    # Fallback if YAML not loaded
    if not tds_sections:
        tds_sections = {
            "section_194J": {
                "threshold": 30000,
                "rate": {"professional_services": 0.10}
            },
            "section_194C": {
                "threshold_aggregate": 100000,
                "rate": {"others": 0.02}
            },
            "section_194I": {
                "threshold": 240000,
                "rate": {"land_building_furniture_fittings": 0.10}
            },
            "section_194Q": {
                "threshold": 5000000,
                "rate": 0.01
            }
        }
    
    amount = float(data.get("invoice_amount", data.get("amount", 0)) or 0)
    description = str(data.get("description", "")).lower()
    
    # Match description to section
    matched_section = None
    rate = None
    threshold = None
    
    # Check section 194J (Professional Fees)
    section_194j = tds_sections.get("section_194J", {})
    if any(keyword in description for keyword in ["professional", "fees", "ca", "legal", "medical", "engineering"]):
        matched_section = "194J"
        rate = section_194j.get("rate", {}).get("professional_services", 0.10)
        threshold = section_194j.get("threshold", 30000)
    
    # Check section 194C (Contract)
    elif any(keyword in description for keyword in ["contract", "contractor", "work", "labour"]):
        section_194c = tds_sections.get("section_194C", {})
        matched_section = "194C"
        rate = section_194c.get("rate", {}).get("others", 0.02)
        threshold = section_194c.get("threshold_aggregate", 100000)
    
    # Check section 194I (Rent)
    elif any(keyword in description for keyword in ["rent", "rental", "lease"]):
        section_194i = tds_sections.get("section_194I", {})
        matched_section = "194I"
        rate = section_194i.get("rate", {}).get("land_building_furniture_fittings", 0.10)
        threshold = section_194i.get("threshold", 240000)
    
    # Check section 194Q (Purchase of Goods)
    elif any(keyword in description for keyword in ["purchase", "goods", "material"]):
        section_194q = tds_sections.get("section_194Q", {})
        if section_194q:
            matched_section = "194Q"
            rate = section_194q.get("rate", 0.01)
            threshold = section_194q.get("threshold", 5000000)
    
    # Default to 194C if no match
    if not matched_section:
        section_194c = tds_sections.get("section_194C", {})
        matched_section = "194C"
        rate = section_194c.get("rate", {}).get("others", 0.02)
        threshold = section_194c.get("threshold_aggregate", 100000)
    
    # Check if threshold exceeded
    threshold_exceeded = amount > threshold if threshold else False
    tds_amount = amount * rate if threshold_exceeded else 0.0
    
    return {
        "section": matched_section,
        "rate": rate,
        "threshold": threshold,
        "amount": amount,
        "threshold_exceeded": threshold_exceeded,
        "tds_amount": tds_amount,
        "net_amount": amount - tds_amount,
        "description": description
    }


def tag_ledger(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tag ledger entries with appropriate TDS section and rates.
    
    Args:
        data: Dictionary containing ledger entries
        
    Returns:
        Dictionary with tagged ledger entries
    """
    entries = data.get("entries", [])
    tagged_entries = []
    
    for entry in entries:
        classification = classify_section({
            "invoice_amount": entry.get("amount", 0),
            "description": entry.get("description", entry.get("ledger", ""))
        })
        
        tagged_entry = {
            **entry,
            "tds_section": classification["section"],
            "tds_rate": classification["rate"],
            "tds_applicable": classification["threshold_exceeded"],
            "tds_amount": classification["tds_amount"]
        }
        tagged_entries.append(tagged_entry)
    
    return {
        "tagged_entries": tagged_entries,
        "total_entries": len(tagged_entries),
        "sections_found": list(set(e["tds_section"] for e in tagged_entries))
    }


def detect_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect TDS defaults (non-deduction, under-deduction, late payment).
    
    Args:
        data: Dictionary containing TDS payment and deduction data
        
    Returns:
        Dictionary with default detection results
    """
    defaults = []
    
    required_tds = float(data.get("required_tds", 0) or 0)
    deducted_tds = float(data.get("deducted_tds", 0) or 0)
    paid_tds = float(data.get("paid_tds", 0) or 0)
    due_date = data.get("due_date", "")
    payment_date = data.get("payment_date", "")
    
    # Non-deduction
    if required_tds > 0 and deducted_tds == 0:
        defaults.append({
            "type": "non_deduction",
            "amount": required_tds,
            "severity": "high",
            "message": "TDS not deducted when required"
        })
    
    # Under-deduction
    elif required_tds > deducted_tds:
        defaults.append({
            "type": "under_deduction",
            "amount": required_tds - deducted_tds,
            "severity": "medium",
            "message": f"TDS under-deducted by {required_tds - deducted_tds}"
        })
    
    # Late payment (simplified check)
    if due_date and payment_date and payment_date > due_date:
        defaults.append({
            "type": "late_payment",
            "severity": "high",
            "message": f"TDS paid after due date {due_date}"
        })
    
    return {
        "defaults": defaults,
        "default_count": len(defaults),
        "requires_action": len(defaults) > 0
    }

