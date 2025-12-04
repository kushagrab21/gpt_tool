"""
Journal Engine for CA Super Tool.
Handles automatic journal entry suggestions based on transactions.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_section
import re


def suggest_journal_entries(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest journal entries based on transaction description.
    
    Args:
        data: Dictionary containing transaction description or details
        
    Returns:
        Dictionary with suggested journal entries
    """
    rulebook_section = get_section("tds_tcs_engine") or {}
    tds_sections = rulebook_section.get("tds_sections", {})
    
    # Fallback if YAML not loaded
    if not tds_sections:
        tds_sections = {
            "section_194I": {
                "threshold": 240000,
                "rate": {"land_building_furniture_fittings": 0.10}
            },
            "section_194J": {
                "threshold": 30000,
                "rate": {"professional_services": 0.10}
            },
            "section_194C": {
                "threshold_aggregate": 100000,
                "rate": {"others": 0.02}
            }
        }
    
    transaction = data.get("transaction", "").lower()
    amount = float(data.get("amount", 0) or 0)
    
    suggestions = []
    
    # Pattern matching for common transactions
    if "rent" in transaction:
        # Rent payment
        section_194i = tds_sections.get("section_194I", {})
        rate = section_194i.get("rate", {}).get("land_building_furniture_fittings", 0.10)
        tds_amount = amount * rate if amount > 240000 else 0
        
        suggestions.append({
            "entry_type": "rent_payment",
            "debit": "Rent Expense",
            "credit": "TDS Payable - 194I" if tds_amount > 0 else None,
            "credit2": "Landlord Payable",
            "amount": amount,
            "tds_amount": tds_amount,
            "net_amount": amount - tds_amount
        })
    
    elif "professional" in transaction or "fees" in transaction or "ca" in transaction:
        # Professional fees
        section_194j = tds_sections.get("section_194J", {})
        rate = section_194j.get("rate", {}).get("professional_services", 0.10)
        tds_amount = amount * rate if amount > 30000 else 0
        
        suggestions.append({
            "entry_type": "professional_fees",
            "debit": "Professional Charges",
            "credit": "TDS Payable - 194J" if tds_amount > 0 else None,
            "credit2": "Professional Payable",
            "amount": amount,
            "tds_amount": tds_amount,
            "net_amount": amount - tds_amount
        })
    
    elif "contract" in transaction or "contractor" in transaction:
        # Contract payment
        section_194c = tds_sections.get("section_194C", {})
        rate = section_194c.get("rate", {}).get("others", 0.02)
        tds_amount = amount * rate if amount > 100000 else 0
        
        suggestions.append({
            "entry_type": "contract_payment",
            "debit": "Contract Expense",
            "credit": "TDS Payable - 194C" if tds_amount > 0 else None,
            "credit2": "Contractor Payable",
            "amount": amount,
            "tds_amount": tds_amount,
            "net_amount": amount - tds_amount
        })
    
    elif "purchase" in transaction or "goods" in transaction:
        # Purchase with GST
        suggestions.append({
            "entry_type": "purchase",
            "debit": "Purchase",
            "debit2": "Input GST",
            "credit": "Supplier Payable",
            "amount": amount,
            "gst_applicable": True
        })
    
    elif "salary" in transaction:
        # Salary payment
        section_192 = tds_sections.get("section_192", {})
        suggestions.append({
            "entry_type": "salary_payment",
            "debit": "Salary Expense",
            "credit": "TDS Payable - Salaries",
            "credit2": "Net Salary Payable",
            "amount": amount
        })
    
    else:
        # Generic suggestion
        suggestions.append({
            "entry_type": "generic",
            "debit": "Expense Account",
            "credit": "Payable Account",
            "amount": amount,
            "note": "Review and adjust accounts as needed"
        })
    
    return {
        "suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "transaction": transaction,
        "amount": amount
    }

