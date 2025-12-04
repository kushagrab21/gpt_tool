"""
Bank Reconciliation Engine for CA Super Tool.
Handles bank statement matching and unmatched transaction detection.
"""

from typing import Dict, Any, List


def match_bank_reco(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Match bank statement entries with books entries.
    
    Args:
        data: Dictionary containing bank statement and books entries
        
    Returns:
        Dictionary with matched and unmatched entries
    """
    bank_statement = data.get("bank_statement", [])
    books_entries = data.get("books_entries", [])
    
    matched = []
    unmatched_bank = []
    unmatched_books = []
    
    # Simple matching by amount and date proximity
    used_books_indices = set()
    
    for bank_entry in bank_statement:
        bank_amount = float(bank_entry.get("amount", 0) or 0)
        bank_date = bank_entry.get("date", "")
        bank_ref = bank_entry.get("reference", "")
        
        matched_entry = None
        
        for idx, books_entry in enumerate(books_entries):
            if idx in used_books_indices:
                continue
            
            books_amount = float(books_entry.get("amount", 0) or 0)
            books_date = books_entry.get("date", "")
            
            # Match if amount matches (within tolerance) and dates are close
            if abs(bank_amount - abs(books_amount)) < 0.01:  # Amount match
                matched_entry = {
                    "bank_entry": bank_entry,
                    "books_entry": books_entry,
                    "match_confidence": "high" if bank_date == books_date else "medium"
                }
                matched.append(matched_entry)
                used_books_indices.add(idx)
                break
        
        if not matched_entry:
            unmatched_bank.append(bank_entry)
    
    # Find unmatched books entries
    for idx, books_entry in enumerate(books_entries):
        if idx not in used_books_indices:
            unmatched_books.append(books_entry)
    
    return {
        "matched": matched,
        "unmatched_bank": unmatched_bank,
        "unmatched_books": unmatched_books,
        "match_count": len(matched),
        "unmatched_bank_count": len(unmatched_bank),
        "unmatched_books_count": len(unmatched_books),
        "reconciliation_status": "complete" if len(unmatched_bank) == 0 and len(unmatched_books) == 0 else "pending"
    }


def detect_unmatched(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect and analyze unmatched transactions in bank reconciliation.
    
    Args:
        data: Dictionary containing reconciliation results
        
    Returns:
        Dictionary with unmatched transaction analysis
    """
    unmatched_bank = data.get("unmatched_bank", [])
    unmatched_books = data.get("unmatched_books", [])
    
    analysis = {
        "unmatched_bank_analysis": {
            "count": len(unmatched_bank),
            "total_amount": sum(float(e.get("amount", 0) or 0) for e in unmatched_bank),
            "entries": unmatched_bank
        },
        "unmatched_books_analysis": {
            "count": len(unmatched_books),
            "total_amount": sum(float(e.get("amount", 0) or 0) for e in unmatched_books),
            "entries": unmatched_books
        },
        "requires_review": len(unmatched_bank) > 0 or len(unmatched_books) > 0
    }
    
    return analysis

