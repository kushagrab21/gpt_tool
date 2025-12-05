"""
Bank Reconciliation Engine for CA Super Tool.
Handles bank statement matching and unmatched transaction detection.
Implements fuzzy matching, date tolerance, amount tolerance, and sign reversal detection.
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Datetime object or None
    """
    if not date_str:
        return None
    
    date_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y.%m.%d"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    
    return None


def calculate_string_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using SequenceMatcher.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    if not str1 or not str2:
        return 0.0
    
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def fuzzy_match_description(
    desc1: str,
    desc2: str,
    threshold: float = 0.6
) -> Tuple[bool, float]:
    """
    Check if two descriptions match using fuzzy matching.
    
    Args:
        desc1: First description
        desc2: Second description
        threshold: Minimum similarity threshold
        
    Returns:
        Tuple of (is_match, similarity_score)
    """
    similarity = calculate_string_similarity(desc1, desc2)
    return similarity >= threshold, similarity


def check_partial_match(desc1: str, desc2: str) -> bool:
    """
    Check if descriptions have significant partial match (keywords).
    
    Args:
        desc1: First description
        desc2: Second description
        
    Returns:
        True if significant partial match found
    """
    # Extract meaningful words (length > 3)
    words1 = set(re.findall(r'\b\w{4,}\b', desc1.lower()))
    words2 = set(re.findall(r'\b\w{4,}\b', desc2.lower()))
    
    if not words1 or not words2:
        return False
    
    # Check if at least 2 words match
    common_words = words1.intersection(words2)
    return len(common_words) >= 2


def match_bank_reco(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Match bank statement entries with books entries using fuzzy matching,
    date tolerance, amount tolerance, and sign reversal detection.
    
    Args:
        data: Dictionary containing bank statement and books entries
        
    Returns:
        Dictionary with matched and unmatched entries in fractal format
    """
    # Initialize flags (preserve existing flags from input if present)
    flags = data.get("flags", [])
    if not isinstance(flags, list):
        flags = []
    
    # Handle both direct keys and nested structure (fractal micro)
    bank_statement = data.get("bank_statement", []) or data.get("bank_entries", []) or []
    books_entries = data.get("books_entries", []) or data.get("book_entries", []) or data.get("ledger_entries", []) or []
    
    # Ensure both are lists
    if not isinstance(bank_statement, list):
        bank_statement = []
    if not isinstance(books_entries, list):
        books_entries = []
    
    # Validate input data
    if not bank_statement:
        flags.append("Warning: bank_statement is empty - no entries to match")
    if not books_entries:
        flags.append("Warning: books_entries is empty - no entries to match")
    if not bank_statement and not books_entries:
        flags.append("Error: Both bank_statement and books_entries are empty")
    
    # Get matching parameters from data or use defaults
    amount_tolerance = float(data.get("amount_tolerance", 0.01))
    date_tolerance_days = int(data.get("date_tolerance_days", 7))
    fuzzy_threshold = float(data.get("fuzzy_threshold", 0.6))
    enable_sign_reversal = data.get("enable_sign_reversal", True)
    enable_partial_match = data.get("enable_partial_match", True)
    
    matched = []
    unmatched_bank = []
    unmatched_books = []
    
    used_books_indices = set()
    
    for bank_entry in bank_statement:
        bank_amount = float(bank_entry.get("amount", 0) or 0)
        bank_date_str = bank_entry.get("date", "")
        bank_ref = bank_entry.get("reference", "")
        bank_desc = str(bank_entry.get("description", "")).lower()
        bank_narration = str(bank_entry.get("narration", "")).lower()
        bank_combined_desc = f"{bank_desc} {bank_narration}".strip()
        
        bank_date = parse_date(bank_date_str)
        
        best_match = None
        best_match_score = 0.0
        best_match_idx = None
        
        for idx, books_entry in enumerate(books_entries):
            if idx in used_books_indices:
                continue
            
            books_amount = float(books_entry.get("amount", 0) or 0)
            books_date_str = books_entry.get("date", "")
            books_desc = str(books_entry.get("description", "")).lower()
            books_narration = str(books_entry.get("narration", "")).lower()
            books_combined_desc = f"{books_desc} {books_narration}".strip()
            
            books_date = parse_date(books_date_str)
            
            match_score = 0.0
            match_reasons = []
            
            # 1. Amount matching (with tolerance and sign reversal)
            amount_match = False
            amount_diff = abs(bank_amount - abs(books_amount))
            
            if amount_diff <= amount_tolerance:
                amount_match = True
                match_score += 0.4
                match_reasons.append("amount_exact")
            elif enable_sign_reversal:
                # Check sign reversal (bank debit = books credit, or vice versa)
                if abs(bank_amount + books_amount) <= amount_tolerance:
                    amount_match = True
                    match_score += 0.35
                    match_reasons.append("amount_sign_reversed")
            
            if not amount_match:
                continue  # Skip if amount doesn't match
            
            # 2. Date matching (with tolerance)
            date_match = False
            if bank_date and books_date:
                date_diff = abs((bank_date - books_date).days)
                if date_diff <= date_tolerance_days:
                    date_match = True
                    if date_diff == 0:
                        match_score += 0.3
                        match_reasons.append("date_exact")
                    else:
                        match_score += 0.2
                        match_reasons.append(f"date_within_tolerance_{date_diff}_days")
            elif bank_date_str == books_date_str:
                # String match if parsing failed
                date_match = True
                match_score += 0.3
                match_reasons.append("date_string_match")
            
            # 3. Description fuzzy matching
            desc_match = False
            if bank_combined_desc and books_combined_desc:
                is_fuzzy_match, similarity = fuzzy_match_description(
                    bank_combined_desc, books_combined_desc, fuzzy_threshold
                )
                if is_fuzzy_match:
                    desc_match = True
                    match_score += 0.2 * similarity
                    match_reasons.append(f"description_fuzzy_{similarity:.2f}")
                elif enable_partial_match and check_partial_match(bank_combined_desc, books_combined_desc):
                    desc_match = True
                    match_score += 0.1
                    match_reasons.append("description_partial")
            
            # 4. Reference matching (if available)
            if bank_ref and books_entry.get("reference"):
                if bank_ref.lower() == str(books_entry.get("reference", "")).lower():
                    match_score += 0.1
                    match_reasons.append("reference_match")
            
            # Determine match confidence
            if match_score >= 0.5:  # Minimum threshold for match
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match = {
                        "bank_entry": bank_entry,
                        "books_entry": books_entry,
                        "match_score": match_score,
                        "match_reasons": match_reasons,
                        "match_confidence": (
                            "high" if match_score >= 0.8 else
                            "medium" if match_score >= 0.6 else
                            "low"
                        ),
                        "amount_diff": amount_diff,
                        "date_diff_days": abs((bank_date - books_date).days) if bank_date and books_date else None
                    }
                    best_match_idx = idx
        
        if best_match:
            matched.append(best_match)
            used_books_indices.add(best_match_idx)
        else:
            unmatched_bank.append(bank_entry)
    
    # Find unmatched books entries
    for idx, books_entry in enumerate(books_entries):
        if idx not in used_books_indices:
            unmatched_books.append(books_entry)
    
    # Build fractal output
    micro = {
        "bank_statement": bank_statement,
        "books_entries": books_entries,
        "matched": matched,
        "unmatched_bank": unmatched_bank,
        "unmatched_books": unmatched_books
    }
    
    meso = {
        "matching_summary": {
            "match_count": len(matched),
            "unmatched_bank_count": len(unmatched_bank),
            "unmatched_books_count": len(unmatched_books),
            "match_rate": len(matched) / len(bank_statement) if bank_statement else 0.0
        },
        "matching_parameters": {
            "amount_tolerance": amount_tolerance,
            "date_tolerance_days": date_tolerance_days,
            "fuzzy_threshold": fuzzy_threshold,
            "enable_sign_reversal": enable_sign_reversal,
            "enable_partial_match": enable_partial_match
        },
        "confidence_distribution": {
            "high": sum(1 for m in matched if m.get("match_confidence") == "high"),
            "medium": sum(1 for m in matched if m.get("match_confidence") == "medium"),
            "low": sum(1 for m in matched if m.get("match_confidence") == "low")
        },
        "flags": flags
    }
    
    macro = {
        "summary": {
            "total_bank_entries": len(bank_statement),
            "total_books_entries": len(books_entries),
            "matched_count": len(matched),
            "unmatched_bank_count": len(unmatched_bank),
            "unmatched_books_count": len(unmatched_books),
            "reconciliation_status": (
                "complete" if len(unmatched_bank) == 0 and len(unmatched_books) == 0 else
                "pending"
            ),
            "match_rate": len(matched) / len(bank_statement) if bank_statement else 0.0
        },
        "flags": flags
    }
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
    }


def detect_unmatched(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect and analyze unmatched transactions in bank reconciliation.
    
    Args:
        data: Dictionary containing reconciliation results (can be from match_bank_reco output)
        
    Returns:
        Dictionary with unmatched transaction analysis in fractal format
    """
    # Handle both direct data and fractal structure
    if "micro" in data:
        unmatched_bank = data["micro"].get("unmatched_bank", [])
        unmatched_books = data["micro"].get("unmatched_books", [])
    else:
        unmatched_bank = data.get("unmatched_bank", [])
        unmatched_books = data.get("unmatched_books", [])
    
    # Analyze unmatched bank entries
    unmatched_bank_amounts = [float(e.get("amount", 0) or 0) for e in unmatched_bank]
    unmatched_bank_total = sum(unmatched_bank_amounts)
    unmatched_bank_positive = sum(amt for amt in unmatched_bank_amounts if amt > 0)
    unmatched_bank_negative = sum(amt for amt in unmatched_bank_amounts if amt < 0)
    
    # Analyze unmatched books entries
    unmatched_books_amounts = [float(e.get("amount", 0) or 0) for e in unmatched_books]
    unmatched_books_total = sum(unmatched_books_amounts)
    unmatched_books_positive = sum(amt for amt in unmatched_books_amounts if amt > 0)
    unmatched_books_negative = sum(amt for amt in unmatched_books_amounts if amt < 0)
    
    # Build fractal output
    micro = {
        "unmatched_bank": unmatched_bank,
        "unmatched_books": unmatched_books
    }
    
    meso = {
        "unmatched_bank_analysis": {
            "count": len(unmatched_bank),
            "total_amount": unmatched_bank_total,
            "positive_amount": unmatched_bank_positive,
            "negative_amount": unmatched_bank_negative,
            "average_amount": unmatched_bank_total / len(unmatched_bank) if unmatched_bank else 0.0
        },
        "unmatched_books_analysis": {
            "count": len(unmatched_books),
            "total_amount": unmatched_books_total,
            "positive_amount": unmatched_books_positive,
            "negative_amount": unmatched_books_negative,
            "average_amount": unmatched_books_total / len(unmatched_books) if unmatched_books else 0.0
        }
    }
    
    macro = {
        "summary": {
            "unmatched_bank_count": len(unmatched_bank),
            "unmatched_books_count": len(unmatched_books),
            "unmatched_bank_total": unmatched_bank_total,
            "unmatched_books_total": unmatched_books_total,
            "net_difference": unmatched_bank_total - unmatched_books_total,
            "requires_review": len(unmatched_bank) > 0 or len(unmatched_books) > 0,
            "reconciliation_gap": abs(unmatched_bank_total - unmatched_books_total)
        },
        "recommendations": []
    }
    
    # Add recommendations
    if len(unmatched_bank) > 0:
        macro["recommendations"].append("Review unmatched bank entries - may require manual matching or represent new transactions")
    if len(unmatched_books) > 0:
        macro["recommendations"].append("Review unmatched books entries - may represent pending transactions or errors")
    if abs(unmatched_bank_total - unmatched_books_total) > 1000:
        macro["recommendations"].append("Significant reconciliation gap detected - investigate potential missing entries or errors")
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
    }

