"""
Journal Engine for CA Super Tool.
Handles automatic journal entry suggestions based on transactions.
Fully integrated with rulebook for TDS, GST, and generic journaling.
"""

from typing import Dict, Any, List, Optional
from engine.rulebook_loader import get_section
import re
from datetime import datetime


def extract_amount(text: str) -> Optional[float]:
    """
    Extract amount from text using regex patterns.
    
    Args:
        text: Text containing amount
        
    Returns:
        Extracted amount or None
    """
    # Patterns: ₹1234.56, 1234.56, Rs 1234, etc.
    patterns = [
        r'[₹Rs]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:rupees|rs|₹)',
        r'amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                # Remove commas and convert
                amount_str = matches[0].replace(',', '')
                return float(amount_str)
            except (ValueError, AttributeError):
                continue
    
    return None


def extract_tds_hints(text: str) -> Dict[str, Any]:
    """
    Extract TDS-related hints from transaction text.
    
    Args:
        text: Transaction description
        
    Returns:
        Dictionary with TDS hints
    """
    hints = {
        "section": None,
        "pan_available": False,
        "vendor_name": None,
        "neft_mode": False
    }
    
    text_lower = text.lower()
    
    # Check for PAN
    pan_pattern = r'[A-Z]{5}\d{4}[A-Z]'
    if re.search(pan_pattern, text, re.IGNORECASE):
        hints["pan_available"] = True
    
    # Check for NEFT/RTGS/IMPS
    if any(mode in text_lower for mode in ["neft", "rtgs", "imps", "upi"]):
        hints["neft_mode"] = True
    
    # Extract vendor name (simple pattern: "to X", "from X", "X payment")
    vendor_patterns = [
        r'(?:to|from|paid to|received from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:payment|invoice|bill)',
    ]
    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            hints["vendor_name"] = match.group(1)
            break
    
    return hints


def extract_gst_hints(text: str) -> Dict[str, Any]:
    """
    Extract GST-related hints from transaction text.
    
    Args:
        text: Transaction description
        
    Returns:
        Dictionary with GST hints
    """
    hints = {
        "gstin_available": False,
        "taxable_base": None,
        "cgst": None,
        "sgst": None,
        "igst": None
    }
    
    text_lower = text.lower()
    
    # Check for GSTIN
    gstin_pattern = r'\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]'
    if re.search(gstin_pattern, text, re.IGNORECASE):
        hints["gstin_available"] = True
    
    # Extract tax amounts
    cgst_match = re.search(r'cgst[:\s]+(\d+(?:\.\d{2})?)', text_lower)
    sgst_match = re.search(r'sgst[:\s]+(\d+(?:\.\d{2})?)', text_lower)
    igst_match = re.search(r'igst[:\s]+(\d+(?:\.\d{2})?)', text_lower)
    
    if cgst_match:
        hints["cgst"] = float(cgst_match.group(1))
    if sgst_match:
        hints["sgst"] = float(sgst_match.group(1))
    if igst_match:
        hints["igst"] = float(igst_match.group(1))
    
    return hints


def classify_transaction_nature(text: str, rulebook_section: Dict[str, Any]) -> Optional[str]:
    """
    Classify transaction nature using rulebook mapping_by_nature.
    
    Args:
        text: Transaction description
        rulebook_section: TDS rulebook section
        
    Returns:
        Nature key or None
    """
    text_lower = text.lower()
    classification_engine = rulebook_section.get("tds_classification_engine", {})
    mapping = classification_engine.get("mapping_by_nature", {})
    
    # Check each nature type
    if any(kw in text_lower for kw in ["salary", "wage", "employee"]):
        return "salary"
    elif any(kw in text_lower for kw in ["professional", "ca", "advocate", "doctor", "engineer", "architect"]):
        return "professional_fee"
    elif any(kw in text_lower for kw in ["contract", "contractor", "work"]):
        return "contractor_payment"
    elif any(kw in text_lower for kw in ["rent", "lease"]):
        if any(kw in text_lower for kw in ["plant", "machinery", "equipment"]):
            return "rent_plant_machinery"
        else:
            return "rent_land_building"
    elif any(kw in text_lower for kw in ["purchase", "buy", "goods"]):
        return "purchase_above_threshold_business"
    elif any(kw in text_lower for kw in ["commission", "brokerage"]):
        return "commission_brokerage"
    elif any(kw in text_lower for kw in ["property", "immovable", "land", "building"]):
        return "property_purchase"
    elif any(kw in text_lower for kw in ["perquisite", "benefit", "gift"]):
        return "business_perquisite"
    
    return None


def build_journal_entry_from_rulebook(
    nature: str,
    amount: float,
    tds_sections: Dict[str, Any],
    hints: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Build journal entry using rulebook journal templates.
    
    Args:
        nature: Transaction nature
        amount: Transaction amount
        tds_sections: TDS sections from rulebook
        hints: Extracted hints
        
    Returns:
        Journal entry dictionary or None
    """
    # Map nature to section
    nature_to_section = {
        "salary": "section_192",
        "professional_fee": "section_194J",
        "contractor_payment": "section_194C",
        "rent_land_building": "section_194I",
        "rent_plant_machinery": "section_194I",
        "purchase_above_threshold_business": "section_194Q",
        "commission_brokerage": "section_194H",
        "property_purchase": "section_194IA",
        "business_perquisite": "section_194R"
    }
    
    section_key = nature_to_section.get(nature)
    if not section_key:
        return None
    
    section_data = tds_sections.get(section_key, {})
    journal_template = section_data.get("journal", {})
    
    if not journal_template:
        # Use generic template
        journal_template = {
            "deduction": [
                {"Dr": "Expense / Asset"},
                {"Cr": f"TDS Payable – {section_key.replace('section_', '').upper()}"},
                {"Cr": "Party Payable / Bank"}
            ]
        }
    
    # Extract journal structure
    deduction_entry = journal_template.get("deduction", [])
    if not deduction_entry:
        return None
    
    # Calculate TDS
    threshold = section_data.get("threshold") or section_data.get("threshold_aggregate") or 0
    rate_dict = section_data.get("rate", {})
    
    # Determine rate
    rate = 0.0
    if isinstance(rate_dict, dict):
        if hints.get("pan_available", False):
            # Use normal rate
            if "normal" in rate_dict:
                rate = rate_dict["normal"]
            elif "professional_services" in rate_dict:
                rate = rate_dict["professional_services"]
            elif "others" in rate_dict:
                rate = rate_dict["others"]
            elif "land_building_furniture_fittings" in rate_dict:
                rate = rate_dict["land_building_furniture_fittings"]
        else:
            # Use no_pan rate
            rate = rate_dict.get("no_pan", 0.20)
    elif isinstance(rate_dict, (int, float)):
        rate = float(rate_dict)
    
    # Check threshold
    tds_amount = 0.0
    if amount > threshold:
        tds_amount = amount * rate
    
    # Build entry
    entry = {
        "entry_type": nature,
        "section": section_key.replace("section_", ""),
        "amount": amount,
        "tds_amount": tds_amount,
        "net_amount": amount - tds_amount,
        "threshold": threshold,
        "rate": rate,
        "debit_accounts": [],
        "credit_accounts": [],
        "hints": hints
    }
    
    # Parse journal template
    for line in deduction_entry:
        if isinstance(line, dict):
            for dr_cr, account in line.items():
                if dr_cr == "Dr":
                    entry["debit_accounts"].append(account)
                elif dr_cr == "Cr":
                    entry["credit_accounts"].append(account)
    
    return entry


def suggest_journal_entries(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest journal entries based on transaction description.
    Fully integrated with rulebook for TDS, GST, and generic journaling.
    
    Args:
        data: Dictionary containing transaction description or details
        
    Returns:
        Dictionary with suggested journal entries in fractal structure
    """
    # Get rulebook sections
    tds_section = get_section("tds_tcs_engine") or {}
    gst_section = get_section("gst_itc_engine") or {}
    
    tds_sections = tds_section.get("tds_sections", {})
    gst_journal_rules = gst_section.get("gst_journal_entry_rules", {})
    
    # Extract transaction data
    transaction = str(data.get("transaction", "")).strip()
    amount = float(data.get("amount", 0) or 0)
    
    # If amount not provided, try to extract from transaction text
    if amount == 0:
        extracted_amount = extract_amount(transaction)
        if extracted_amount:
            amount = extracted_amount
    
    # Extract hints
    tds_hints = extract_tds_hints(transaction)
    gst_hints = extract_gst_hints(transaction)
    
    suggestions = []
    flags = []
    
    # Classify transaction nature
    nature = classify_transaction_nature(transaction, tds_section)
    
    # Build TDS-based journal entry if applicable
    if nature and tds_sections:
        entry = build_journal_entry_from_rulebook(nature, amount, tds_sections, tds_hints)
        if entry:
            suggestions.append(entry)
    
    # Check for GST transactions
    if gst_hints.get("gstin_available") or any(kw in transaction.lower() for kw in ["gst", "cgst", "sgst", "igst"]):
        # Use GST journal rules
        if "purchase" in transaction.lower() or "goods" in transaction.lower():
            purchase_entry = {
                "entry_type": "gst_purchase",
                "debit_accounts": ["Purchase", "Input CGST", "Input SGST"],
                "credit_accounts": ["Supplier Payable"],
                "amount": amount,
                "gst_applicable": True,
                "gst_hints": gst_hints
            }
            suggestions.append(purchase_entry)
    
    # If no suggestions yet, provide generic entry
    if not suggestions:
        generic_entry = {
            "entry_type": "generic",
            "debit_accounts": ["Expense Account"],
            "credit_accounts": ["Payable Account"],
            "amount": amount,
            "note": "Review and adjust accounts as needed. Transaction not matched to rulebook patterns."
        }
        suggestions.append(generic_entry)
        flags.append("Generic entry suggested - transaction not matched to rulebook patterns")
    
    # Build fractal output structure
    micro = {
        "transaction": transaction,
        "amount": amount,
        "suggestions": suggestions,
        "tds_hints": tds_hints,
        "gst_hints": gst_hints,
        "nature": nature
    }
    
    meso = {
        "suggestion_count": len(suggestions),
        "tds_applicable": any(s.get("tds_amount", 0) > 0 for s in suggestions),
        "gst_applicable": any(s.get("gst_applicable", False) for s in suggestions),
        "flags": flags,
        "rulebook_used": bool(tds_sections)
    }
    
    macro = {
        "summary": {
            "total_suggestions": len(suggestions),
            "total_amount": amount,
            "has_tds": any(s.get("tds_amount", 0) > 0 for s in suggestions),
            "has_gst": any(s.get("gst_applicable", False) for s in suggestions),
            "rulebook_integrated": bool(tds_sections)
        },
        "flags": flags
    }
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
    }

