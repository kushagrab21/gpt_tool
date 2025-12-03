"""
Auto Entries Engine for CA Super Tool.
Handles automatic accounting entry generation from TDS and GST engine outputs.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict


def get_config(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, str]:
    """
    Get configuration for ledger names and defaults.
    
    Args:
        micro: Micro-level data containing config
        settings: Settings dictionary
        
    Returns:
        Configuration dictionary with ledger names and defaults
    """
    config = micro.get("config", {})
    
    defaults = {
        "tds_payable_ledger": "TDS Payable",
        "tds_expense_ledger": "TDS Expense",
        "tds_rounding_ledger": "Rounding Off",
        "gst_input_ledger": "Input GST",
        "gst_output_ledger": "Output GST",
        "gst_diff_ledger": "GST Difference",
        "suspense_ledger": "Suspense A/c",
        "default_date": "2024-04-30",
        "entry_prefix": "AUTO"
    }
    
    # Merge config from micro, then settings, then defaults
    result = defaults.copy()
    result.update(settings.get("config", {}))
    result.update(config)
    
    return result


def build_tds_entries(payload: Dict[str, Any], config: Dict[str, str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Build journal entries from TDS liability payload.
    
    Args:
        payload: Full result dict from TDS liability engine
        config: Configuration dictionary
        
    Returns:
        Tuple of (entries list, flags list)
    """
    entries = []
    flags = []
    
    # Check if payload structure is valid
    if not isinstance(payload, dict):
        flags.append("Invalid payload structure for TDS entries")
        return entries, flags
    
    meso = payload.get("meso", {})
    by_party = meso.get("by_party", [])
    micro = payload.get("micro", {})
    transactions = micro.get("transactions", [])
    
    # Create lookup for transactions by party+section
    txn_lookup = defaultdict(list)
    for txn in transactions:
        party_key = txn.get("party_pan") or txn.get("party_name", "")
        section = txn.get("section", "")
        fy = txn.get("fy", "")
        if party_key and section and fy:
            lookup_key = f"{fy}|{section}|{party_key}"
            txn_lookup[lookup_key].append(txn.get("txn_id", ""))
    
    # Check for missing ledger config
    missing_ledgers = []
    if not config.get("tds_expense_ledger"):
        missing_ledgers.append("tds_expense_ledger")
    if not config.get("tds_payable_ledger"):
        missing_ledgers.append("tds_payable_ledger")
    
    if missing_ledgers:
        flags.append(f"Missing ledger config for TDS: {', '.join(missing_ledgers)}; using defaults.")
    
    entry_prefix = config.get("entry_prefix", "AUTO")
    default_date = config.get("default_date", "2024-04-30")
    entry_counter = 1
    
    # Generate entries for each party+section with TDS > 0
    for party_data in by_party:
        total_tds = float(party_data.get("total_tds", 0) or 0)
        
        if total_tds <= 0:
            continue
        
        fy = party_data.get("fy", "")
        section = party_data.get("section", "")
        party_pan = party_data.get("party_pan", "")
        party_name = party_data.get("party_name", "")
        total_gross = float(party_data.get("total_gross", 0) or 0)
        txn_count = party_data.get("txn_count", 0)
        
        # Get linked transaction IDs
        party_key = party_pan if party_pan else party_name
        lookup_key = f"{fy}|{section}|{party_key}"
        linked_txn_ids = txn_lookup.get(lookup_key, [])
        
        # Build narration
        narration = (
            f"Auto TDS entry for FY {fy}, Section {section}, "
            f"Party {party_name} ({party_pan if party_pan else 'PAN not available'}), "
            f"gross ₹{total_gross:.2f}, TDS ₹{total_tds:.2f}."
        )
        
        # Build tags
        tags = ["AUTO", "TDS"]
        
        # Add REVIEW_REQUIRED if conditions met
        if total_tds > 100000:
            tags.append("REVIEW_REQUIRED")
        elif not party_pan:
            tags.append("REVIEW_REQUIRED")
        else:
            tags.append("ENTRY_READY")
        
        # Build entry
        entry = {
            "entry_id": f"{entry_prefix}-TDS-{entry_counter:03d}",
            "date": default_date,
            "entry_type": "TDS",
            "debit_account": config.get("tds_expense_ledger", "TDS Expense"),
            "credit_account": config.get("tds_payable_ledger", "TDS Payable"),
            "amount": total_tds,
            "narration": narration,
            "tags": tags,
            "linked_txn_ids": linked_txn_ids,
            "meta": {
                "fy": fy,
                "section": section,
                "party_name": party_name,
                "party_pan": party_pan,
                "source": "tds_liability",
                "txn_count": txn_count
            }
        }
        
        entries.append(entry)
        entry_counter += 1
    
    return entries, flags


def build_gst_entries(payload: Dict[str, Any], config: Dict[str, str], source: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Build journal entries from GST reconciliation payload.
    
    Args:
        payload: Full result dict from GST reconciliation engine
        config: Configuration dictionary
        source: Source task name (e.g., "gst_reconcile_3b_books")
        
    Returns:
        Tuple of (entries list, flags list)
    """
    entries = []
    flags = []
    
    # Check if payload structure is valid
    if not isinstance(payload, dict):
        flags.append("Invalid payload structure for GST entries")
        return entries, flags
    
    macro = payload.get("macro", {})
    summary = macro.get("summary", {})
    
    # Extract differences
    # For 3b_books, we have macro_diff
    macro_diff = summary.get("macro_diff", 0)
    
    # For 2b_3b, we might have different structure
    if "total_itc_2b_eligible" in summary and "3b_itc_claimed" in summary:
        itc_2b_eligible = float(summary.get("total_itc_2b_eligible", 0) or 0)
        itc_3b_claimed = float(summary.get("3b_itc_claimed", 0) or 0)
        total_diff = itc_3b_claimed - itc_2b_eligible
    else:
        total_diff = float(macro_diff or 0)
    
    # Check for missing ledger config
    missing_ledgers = []
    if not config.get("gst_input_ledger"):
        missing_ledgers.append("gst_input_ledger")
    if not config.get("gst_diff_ledger"):
        missing_ledgers.append("gst_diff_ledger")
    if not config.get("suspense_ledger"):
        missing_ledgers.append("suspense_ledger")
    
    if missing_ledgers:
        flags.append(f"Missing ledger config for GST: {', '.join(missing_ledgers)}; using defaults.")
    
    # Skip if difference is too small
    if abs(total_diff) < 1.0:
        flags.append("GST difference below ₹1; entry skipped.")
        return entries, flags
    
    entry_prefix = config.get("entry_prefix", "AUTO")
    default_date = config.get("default_date", "2024-04-30")
    
    # If ITC claimed > eligible (positive diff) → reversal needed
    if total_diff > 0:
        entry = {
            "entry_id": f"{entry_prefix}-GST-001",
            "date": default_date,
            "entry_type": "GST",
            "debit_account": config.get("gst_diff_ledger", "GST Difference"),
            "credit_account": config.get("gst_input_ledger", "Input GST"),
            "amount": abs(total_diff),
            "narration": (
                f"Auto GST ITC reversal entry: ITC claimed in 3B exceeds "
                f"eligible ITC as per 2B by ₹{total_diff:.2f}."
            ),
            "tags": ["AUTO", "GST", "REVIEW_REQUIRED"],
            "linked_txn_ids": [],
            "meta": {
                "source": source,
                "itc_claimed": summary.get("3b_itc_claimed", 0),
                "itc_eligible": summary.get("total_itc_2b_eligible", 0),
                "difference": total_diff
            }
        }
        entries.append(entry)
    
    # If ITC claimed < eligible (negative diff) → adjustment suggestion
    elif total_diff < 0:
        entry = {
            "entry_id": f"{entry_prefix}-GST-001",
            "date": default_date,
            "entry_type": "GST",
            "debit_account": config.get("gst_input_ledger", "Input GST"),
            "credit_account": config.get("suspense_ledger", "Suspense A/c"),
            "amount": abs(total_diff),
            "narration": (
                f"Auto GST ITC adjustment suggestion: Eligible ITC as per 2B "
                f"exceeds ITC claimed in 3B by ₹{abs(total_diff):.2f}. "
                f"Consider adjusting in next period."
            ),
            "tags": ["AUTO", "GST", "REVIEW_REQUIRED"],
            "linked_txn_ids": [],
            "meta": {
                "source": source,
                "itc_claimed": summary.get("3b_itc_claimed", 0),
                "itc_eligible": summary.get("total_itc_2b_eligible", 0),
                "difference": total_diff
            }
        }
        entries.append(entry)
    
    return entries, flags


def build_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build summary statistics from journal entries.
    
    Args:
        entries: List of journal entries
        
    Returns:
        Summary dictionary
    """
    total_entries = len(entries)
    total_amount = sum(float(entry.get("amount", 0) or 0) for entry in entries)
    
    # Aggregate by type
    by_type = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    
    for entry in entries:
        entry_type = entry.get("entry_type", "UNKNOWN")
        amount = float(entry.get("amount", 0) or 0)
        by_type[entry_type]["count"] += 1
        by_type[entry_type]["total_amount"] += amount
    
    return {
        "total_entries": total_entries,
        "total_amount": total_amount,
        "by_type": dict(by_type)
    }


def run_auto_entries(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate automatic journal entries from TDS or GST engine outputs.
    
    Args:
        micro: Micro-level data containing source, payload, and config
        settings: Optional settings
        
    Returns:
        Dictionary with entries, summary, and flags
    """
    entries = []
    flags = []
    
    # Extract source and payload
    source = micro.get("source", "").lower()
    payload = micro.get("payload", {})
    
    if not source:
        flags.append("No source specified for auto_entries; no entries generated.")
        return {
            "entries": [],
            "summary": {
                "total_entries": 0,
                "total_amount": 0.0,
                "by_type": {}
            },
            "flags": flags
        }
    
    if not payload:
        flags.append("No payload provided for auto_entries; no entries generated.")
        return {
            "entries": [],
            "summary": {
                "total_entries": 0,
                "total_amount": 0.0,
                "by_type": {}
            },
            "flags": flags
        }
    
    # Get configuration
    config = get_config(micro, settings)
    
    # Build entries based on source
    if source == "tds_liability":
        tds_entries, tds_flags = build_tds_entries(payload, config)
        entries.extend(tds_entries)
        flags.extend(tds_flags)
    
    elif source.startswith("gst_"):
        gst_entries, gst_flags = build_gst_entries(payload, config, source)
        entries.extend(gst_entries)
        flags.extend(gst_flags)
    
    else:
        flags.append(f"Unsupported payload structure for auto_entries (source: {source}); no entries generated.")
    
    # Build summary
    summary = build_summary(entries)
    
    # Add additional flags based on entries
    small_entries = [e for e in entries if float(e.get("amount", 0) or 0) < 1000]
    if small_entries:
        flags.append(f"Some entries are below ₹1,000 and can be batched ({len(small_entries)} entries).")
    
    # Check for missing ledger configs in entries
    missing_ledger_entries = []
    for entry in entries:
        if not entry.get("debit_account") or not entry.get("credit_account"):
            missing_ledger_entries.append(entry.get("entry_id", "unknown"))
    
    if missing_ledger_entries:
        flags.append(f"Some entries have unknown/config-missing ledgers: {', '.join(missing_ledger_entries)}")
    
    return {
        "entries": entries,
        "summary": summary,
        "flags": flags
    }
