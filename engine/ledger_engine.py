"""
Ledger Engine for CA Super Tool.
Handles ledger normalization, grouping, and error detection.
"""

from typing import Dict, Any, List
import re


def normalize_ledgers(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize ledger names (remove extra spaces, standardize format).
    
    Args:
        data: Dictionary containing ledger entries
        
    Returns:
        Dictionary with normalized ledger names
    """
    entries = data.get("entries", data.get("ledgers", []))
    
    normalized = []
    
    for entry in entries:
        ledger_name = str(entry.get("ledger", "")).strip()
        
        # Normalize: remove extra spaces, standardize case
        normalized_name = re.sub(r'\s+', ' ', ledger_name).strip()
        normalized_name = normalized_name.title()  # Title case
        
        normalized_entry = {
            **entry,
            "ledger": normalized_name,
            "original_ledger": ledger_name
        }
        normalized.append(normalized_entry)
    
    return {
        "normalized_ledgers": normalized,
        "total_ledgers": len(normalized),
        "changes_made": sum(1 for e in normalized if e["ledger"] != e["original_ledger"])
    }


def group_ledgers(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Group ledgers by common patterns or categories.
    
    Args:
        data: Dictionary containing ledger entries
        
    Returns:
        Dictionary with grouped ledgers
    """
    entries = data.get("entries", data.get("ledgers", []))
    
    groups = {
        "expenses": [],
        "revenue": [],
        "assets": [],
        "liabilities": [],
        "equity": [],
        "other": []
    }
    
    for entry in entries:
        ledger = str(entry.get("ledger", "")).lower()
        
        if any(keyword in ledger for keyword in ["expense", "cost", "charge", "fee"]):
            groups["expenses"].append(entry)
        elif any(keyword in ledger for keyword in ["revenue", "income", "sale", "receipt"]):
            groups["revenue"].append(entry)
        elif any(keyword in ledger for keyword in ["asset", "investment", "receivable"]):
            groups["assets"].append(entry)
        elif any(keyword in ledger for keyword in ["liability", "payable", "borrowing", "loan"]):
            groups["liabilities"].append(entry)
        elif any(keyword in ledger for keyword in ["equity", "capital", "reserve"]):
            groups["equity"].append(entry)
        else:
            groups["other"].append(entry)
    
    return {
        "groups": groups,
        "total_ledgers": len(entries),
        "group_counts": {k: len(v) for k, v in groups.items()}
    }


def map_ledger_groups(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map ledger groups to standard accounting categories.
    
    Args:
        data: Dictionary containing ledger groups
        
    Returns:
        Dictionary with mapped ledger groups
    """
    groups = data.get("groups", {})
    
    mapping = {
        "expenses": "Profit & Loss - Expenses",
        "revenue": "Profit & Loss - Revenue",
        "assets": "Balance Sheet - Assets",
        "liabilities": "Balance Sheet - Liabilities",
        "equity": "Balance Sheet - Equity",
        "other": "Unclassified"
    }
    
    mapped = {}
    for group_name, ledgers in groups.items():
        mapped[mapping.get(group_name, "Unclassified")] = ledgers
    
    return {
        "mapped_groups": mapped,
        "mapping_applied": True
    }


def detect_ledger_errors(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect common ledger errors (duplicates, naming inconsistencies, etc.).
    
    Args:
        data: Dictionary containing ledger entries
        
    Returns:
        Dictionary with detected errors
    """
    entries = data.get("entries", data.get("ledgers", []))
    
    errors = []
    warnings = []
    
    # Check for duplicates
    ledger_names = [str(e.get("ledger", "")).lower().strip() for e in entries]
    duplicates = [name for name in set(ledger_names) if ledger_names.count(name) > 1]
    
    if duplicates:
        errors.append({
            "type": "duplicate_ledgers",
            "count": len(duplicates),
            "ledgers": duplicates,
            "severity": "high"
        })
    
    # Check for naming inconsistencies
    inconsistent = []
    for entry in entries:
        ledger = str(entry.get("ledger", ""))
        if len(ledger) < 3:  # Too short
            inconsistent.append(ledger)
        elif not re.match(r'^[A-Za-z0-9\s\-_]+$', ledger):  # Invalid characters
            inconsistent.append(ledger)
    
    if inconsistent:
        warnings.append({
            "type": "naming_inconsistencies",
            "count": len(inconsistent),
            "ledgers": inconsistent[:10],  # Limit to first 10
            "severity": "medium"
        })
    
    return {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "requires_action": len(errors) > 0
    }

