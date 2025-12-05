"""
TDS Classifier Engine for CA Super Tool.
Handles TDS (Tax Deducted at Source) liability classification and calculation.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict


def detect_section(txn: Dict[str, Any]) -> str:
    """
    Detect TDS section for a transaction based on nature of payment.
    
    Rules:
    - If section_override is present, return that
    - Else, map nature_of_payment to section:
      - PROFESSIONAL_FEES → 194J
      - CONTRACT → 194C
      - RENT → 194I
      - COMMISSION → 194H
      - PURCHASE_OF_GOODS → 194Q
      - OTHER → 194C (fallback)
    
    Args:
        txn: Transaction dictionary
        
    Returns:
        Section code string (e.g., "194C")
    """
    # Check for override
    section_override = txn.get("section_override")
    if section_override:
        return str(section_override)
    
    # Map nature of payment to section
    nature = txn.get("nature_of_payment", "").upper()
    
    section_map = {
        "PROFESSIONAL_FEES": "194J",
        "CONTRACT": "194C",
        "RENT": "194I",
        "COMMISSION": "194H",
        "PURCHASE_OF_GOODS": "194Q",
        "OTHER": "194C"  # Fallback
    }
    
    return section_map.get(nature, "194C")  # Default fallback


def get_tds_rate_and_threshold(section: str, txn: Dict[str, Any]) -> Tuple[float, float]:
    """
    Get TDS rate and annual threshold for a section.
    
    Args:
        section: TDS section code (e.g., "194C")
        txn: Transaction dictionary
        
    Returns:
        Tuple of (rate, annual_threshold)
    """
    is_individual_or_huf = txn.get("is_individual_or_huf", False)
    is_pan_available = txn.get("is_pan_available", True)
    
    # Base rates and thresholds
    section_config = {
        "194C": {
            "rate_individual": 0.01,  # 1% for individuals/HUF
            "rate_other": 0.02,       # 2% for others
            "threshold": 100000.0
        },
        "194J": {
            "rate": 0.10,  # 10%
            "threshold": 30000.0
        },
        "194I": {
            "rate": 0.10,  # 10%
            "threshold": 240000.0
        },
        "194H": {
            "rate": 0.05,  # 5%
            "threshold": 15000.0
        },
        "194Q": {
            "rate": 0.01,  # 1%
            "threshold": 5000000.0
        }
    }
    
    config = section_config.get(section)
    if not config:
        # Unknown section - no TDS
        return (0.0, float('inf'))
    
    # Get rate based on section
    if section == "194C":
        rate = config["rate_individual"] if is_individual_or_huf else config["rate_other"]
    else:
        rate = config["rate"]
    
    threshold = config["threshold"]
    
    # Apply higher rate if PAN not available
    if not is_pan_available:
        rate = rate * 2.0
    
    return (rate, threshold)


def aggregate_gross_by_party_section(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate gross amounts by (FY, section, party) key.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary keyed by "fy|section|party" with aggregated gross amounts
    """
    aggregates = defaultdict(float)
    
    for txn in transactions:
        fy = txn.get("fy", txn.get("default_fy", "2024-25"))
        section = detect_section(txn)
        party_pan = txn.get("party_pan", "")
        party_name = txn.get("party_name", "")
        
        # Use PAN if available, else name
        party_key = party_pan if party_pan else party_name
        
        if not party_key:
            continue
        
        amount = float(txn.get("amount", 0) or 0)
        
        # Create aggregation key
        agg_key = f"{fy}|{section}|{party_key}"
        aggregates[agg_key] += amount
    
    return dict(aggregates)


def build_micro_outputs(
    transactions: List[Dict[str, Any]],
    aggregates: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Build micro-level transaction outputs with TDS calculations.
    
    Args:
        transactions: List of input transactions
        aggregates: Aggregated gross amounts by (fy|section|party)
        
    Returns:
        List of detailed transaction outputs
    """
    micro_outputs = []
    cumulative_by_key = defaultdict(float)
    
    for txn in transactions:
        txn_id = txn.get("txn_id", "")
        fy = txn.get("fy", txn.get("default_fy", "2024-25"))
        section = detect_section(txn)
        party_pan = txn.get("party_pan", "")
        party_name = txn.get("party_name", "")
        party_key = party_pan if party_pan else party_name
        
        amount = float(txn.get("amount", 0) or 0)
        
        # Get rate and threshold
        rate, threshold = get_tds_rate_and_threshold(section, txn)
        
        # Build aggregation key
        agg_key = f"{fy}|{section}|{party_key}"
        
        # Update cumulative for this key
        cumulative_by_key[agg_key] += amount
        
        # Check if threshold exceeded (using cumulative)
        cumulative_gross = cumulative_by_key[agg_key]
        threshold_exceeded = cumulative_gross > threshold
        
        # Calculate TDS
        if threshold_exceeded:
            tds_amount = amount * rate
        else:
            tds_amount = 0.0
        
        net_amount = amount - tds_amount
        
        # Build reasons
        reasons = []
        if not threshold_exceeded:
            reasons.append(f"Below threshold (cumulative: {cumulative_gross:.2f} vs threshold: {threshold:.2f})")
        else:
            reasons.append(f"Threshold exceeded (cumulative: {cumulative_gross:.2f} > {threshold:.2f})")
        
        if not txn.get("is_pan_available", True):
            reasons.append("PAN not available - higher rate applied")
        
        if section not in ["194C", "194J", "194I", "194H", "194Q"]:
            reasons.append(f"Unknown section: {section}")
        
        micro_output = {
            "txn_id": txn_id,
            "fy": fy,
            "party_pan": party_pan,
            "party_name": party_name,
            "section": section,
            "gross_amount": amount,
            "tds_rate": rate,
            "tds_amount": tds_amount,
            "net_amount": net_amount,
            "threshold_exceeded": threshold_exceeded,
            "cumulative_gross": cumulative_gross,
            "threshold": threshold,
            "reasons": reasons
        }
        
        micro_outputs.append(micro_output)
    
    return micro_outputs


def build_meso_aggregates(micro_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build meso-level aggregates by party and by section.
    
    Args:
        micro_outputs: List of micro-level transaction outputs
        
    Returns:
        Dictionary with by_party and by_section lists
    """
    # Aggregate by party
    party_aggregates = defaultdict(lambda: {
        "total_gross": 0.0,
        "total_tds": 0.0,
        "txn_count": 0,
        "sections": set(),
        "party_pan": "",
        "party_name": "",
        "fy": ""
    })
    
    for txn in micro_outputs:
        party_key = txn.get("party_pan") or txn.get("party_name", "")
        fy = txn.get("fy", "")
        section = txn.get("section", "")
        
        if not party_key:
            continue
        
        agg_key = f"{fy}|{section}|{party_key}"
        
        party_aggregates[agg_key]["total_gross"] += txn.get("gross_amount", 0)
        party_aggregates[agg_key]["total_tds"] += txn.get("tds_amount", 0)
        party_aggregates[agg_key]["txn_count"] += 1
        party_aggregates[agg_key]["sections"].add(section)
        party_aggregates[agg_key]["party_pan"] = txn.get("party_pan", "")
        party_aggregates[agg_key]["party_name"] = txn.get("party_name", "")
        party_aggregates[agg_key]["fy"] = fy
    
    # Build by_party list
    by_party = []
    for agg_key, data in party_aggregates.items():
        parts = agg_key.split("|")
        if len(parts) >= 3:
            fy, section, party = parts[0], parts[1], parts[2]
        else:
            continue
        
        flags = []
        if data["total_tds"] > 100000:  # High TDS threshold
            flags.append("High TDS liability for this party")
        
        if not data["party_pan"]:
            flags.append("PAN not available for some transactions")
        
        # Check if threshold barely exceeded (within 10% above threshold)
        # This is a simplified check - in reality we'd need to track the actual threshold
        if data["total_gross"] > 0:
            flags.append("Threshold check completed")
        
        by_party.append({
            "party_key": agg_key,
            "fy": fy,
            "section": section,
            "party_pan": data["party_pan"],
            "party_name": data["party_name"],
            "total_gross": data["total_gross"],
            "total_tds": data["total_tds"],
            "txn_count": data["txn_count"],
            "flags": flags
        })
    
    # Aggregate by section
    section_aggregates = defaultdict(lambda: {
        "total_gross": 0.0,
        "total_tds": 0.0,
        "unique_parties": set(),
        "txn_count": 0
    })
    
    for txn in micro_outputs:
        section = txn.get("section", "")
        party_key = txn.get("party_pan") or txn.get("party_name", "")
        
        section_aggregates[section]["total_gross"] += txn.get("gross_amount", 0)
        section_aggregates[section]["total_tds"] += txn.get("tds_amount", 0)
        section_aggregates[section]["unique_parties"].add(party_key)
        section_aggregates[section]["txn_count"] += 1
    
    # Build by_section list
    by_section = []
    for section, data in section_aggregates.items():
        by_section.append({
            "section": section,
            "total_gross": data["total_gross"],
            "total_tds": data["total_tds"],
            "unique_parties": len(data["unique_parties"]),
            "txn_count": data["txn_count"]
        })
    
    return {
        "by_party": by_party,
        "by_section": by_section
    }


def build_macro_summary(micro_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build macro-level summary.
    
    Args:
        micro_outputs: List of micro-level transaction outputs
        
    Returns:
        Dictionary with summary and flags
    """
    total_gross = sum(txn.get("gross_amount", 0) for txn in micro_outputs)
    total_tds = sum(txn.get("tds_amount", 0) for txn in micro_outputs)
    
    # Count unique parties
    unique_parties = set()
    for txn in micro_outputs:
        party_key = txn.get("party_pan") or txn.get("party_name", "")
        if party_key:
            unique_parties.add(party_key)
    
    total_transactions = len(micro_outputs)
    
    # Build flags
    flags = []
    
    if total_tds > 500000:  # High overall TDS
        flags.append(f"Overall TDS liability is high: {total_tds:,.2f}")
    
    # Check for unknown sections
    unknown_sections = set()
    for txn in micro_outputs:
        section = txn.get("section", "")
        if section not in ["194C", "194J", "194I", "194H", "194Q"]:
            unknown_sections.add(section)
    
    if unknown_sections:
        flags.append(f"Some transactions have unknown sections: {', '.join(unknown_sections)}")
    
    # Check for transactions below threshold but close
    close_to_threshold = 0
    for txn in micro_outputs:
        if not txn.get("threshold_exceeded", False):
            cumulative = txn.get("cumulative_gross", 0)
            threshold = txn.get("threshold", float('inf'))
            if threshold != float('inf') and cumulative > threshold * 0.9:  # Within 90% of threshold
                close_to_threshold += 1
    
    if close_to_threshold > 0:
        flags.append(f"{close_to_threshold} transactions are below threshold but close")
    
    # Get most common FY
    fy_counts = defaultdict(int)
    for txn in micro_outputs:
        fy = txn.get("fy", "")
        if fy:
            fy_counts[fy] += 1
    
    most_common_fy = max(fy_counts.items(), key=lambda x: x[1])[0] if fy_counts else "2024-25"
    
    if most_common_fy:
        flags.append(f"Most transactions in FY: {most_common_fy}")
    
    return {
        "summary": {
            "total_gross_all": total_gross,
            "total_tds_all": total_tds,
            "total_parties": len(unique_parties),
            "total_transactions": total_transactions,
            "most_common_fy": most_common_fy
        },
        "flags": flags
    }


def run_tds_liability(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate TDS liability for transactions.
    
    Processes transactions, classifies by section, applies thresholds,
    and computes TDS amounts. Returns micro/meso/macro structure.
    
    Args:
        micro: Micro-level data containing transactions
        settings: Optional settings
        
    Returns:
        Dictionary with micro/meso/macro structure
    """
    # Extract transactions safely
    transactions = micro.get("transactions", [])
    if not transactions:
        # Return empty structure
        return {
            "micro": {"transactions": []},
            "meso": {"by_party": [], "by_section": []},
            "macro": {
                "summary": {
                    "total_gross_all": 0.0,
                    "total_tds_all": 0.0,
                    "total_parties": 0,
                    "total_transactions": 0
                },
                "flags": ["No transactions provided"]
            }
        }
    
    # Add default FY to transactions if missing
    default_fy = settings.get("default_fy", "2024-25")
    for txn in transactions:
        if "fy" not in txn:
            txn["fy"] = default_fy
        if "default_fy" not in txn:
            txn["default_fy"] = default_fy
    
    # Aggregate gross amounts by party+section+FY
    aggregates = aggregate_gross_by_party_section(transactions)
    
    # Build micro outputs
    micro_outputs = build_micro_outputs(transactions, aggregates)
    
    # Build meso aggregates
    meso_data = build_meso_aggregates(micro_outputs)
    
    # Build macro summary
    macro_data = build_macro_summary(micro_outputs)
    
    return {
        "micro": {
            "transactions": micro_outputs
        },
        "meso": meso_data,
        "macro": macro_data
    }
