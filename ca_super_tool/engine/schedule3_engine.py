"""
Schedule III Engine for CA Super Tool.
Handles Schedule III classification, grouping, and note generation.
"""

from typing import Dict, Any, List
from ca_super_tool.engine.rulebook_loader import get_section


def classify_schedule3(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify ledger items into Schedule III categories.
    
    Args:
        data: Dictionary containing 'items' list with ledger names and amounts
        
    Returns:
        Dictionary with classified items grouped by Schedule III categories
    """
    rulebook_section = get_section("schedule_iii_engine") or {}
    mapping_rules = rulebook_section.get("schedule_iii_mapping_rules", [])
    
    # Fallback rules if YAML not loaded
    if not mapping_rules:
        mapping_rules = [
            {
                "id": "map_unsecured_loan_from_director",
                "ledger_keywords": ["unsecured loan", "director loan"],
                "mapped_to": "non_current_liabilities/long_term_borrowings"
            },
            {
                "id": "map_advances_from_customers",
                "ledger_keywords": ["advance from customer", "customer advance"],
                "mapped_to": "current_liabilities/other_current_liabilities"
            },
            {
                "id": "map_furniture_and_fixtures",
                "ledger_keywords": ["furniture", "fixtures"],
                "mapped_to": "non_current_assets/ppe"
            },
            {
                "id": "map_cash_in_hand",
                "ledger_keywords": ["cash", "cash in hand"],
                "mapped_to": "current_assets/cash_and_cash_equivalents"
            }
        ]
    
    items = data.get("items", [])
    classified = {}
    
    for item in items:
        ledger = str(item.get("ledger", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        
        # Find matching rule
        matched_category = None
        for rule in mapping_rules:
            keywords = [kw.lower() for kw in rule.get("ledger_keywords", [])]
            if any(keyword in ledger for keyword in keywords):
                matched_category = rule.get("mapped_to", "unclassified")
                break
        
        if not matched_category:
            matched_category = "unclassified"
        
        # Group by category
        if matched_category not in classified:
            classified[matched_category] = []
        
        classified[matched_category].append({
            "ledger": item.get("ledger"),
            "amount": amount,
            "original_item": item
        })
    
    # Calculate totals per category
    summary = {}
    for category, items_list in classified.items():
        summary[category] = {
            "count": len(items_list),
            "total": sum(item["amount"] for item in items_list),
            "items": items_list
        }
    
    return {
        "classified": classified,
        "summary": summary,
        "total_items": len(items),
        "categories_found": list(classified.keys())
    }


def group_schedule3(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Group Schedule III items by major categories (Assets, Liabilities, Equity, P&L).
    
    Args:
        data: Dictionary containing classified items
        
    Returns:
        Dictionary with items grouped by major Schedule III categories
    """
    rulebook_section = get_section("schedule_iii_engine")
    
    # Get classification rules
    asset_classification = rulebook_section.get("asset_classification", {})
    liability_classification = rulebook_section.get("liability_classification", {})
    equity_classification = rulebook_section.get("equity_classification", {})
    
    classified = data.get("classified", {})
    
    grouped = {
        "current_assets": [],
        "non_current_assets": [],
        "current_liabilities": [],
        "non_current_liabilities": [],
        "equity": [],
        "revenue": [],
        "expenses": [],
        "unclassified": []
    }
    
    for category, items in classified.items():
        category_lower = category.lower()
        
        if "current_asset" in category_lower or "asset" in category_lower:
            if "non_current" in category_lower or "long_term" in category_lower:
                grouped["non_current_assets"].extend(items)
            else:
                grouped["current_assets"].extend(items)
        elif "liability" in category_lower or "borrowing" in category_lower:
            if "non_current" in category_lower or "long_term" in category_lower:
                grouped["non_current_liabilities"].extend(items)
            else:
                grouped["current_liabilities"].extend(items)
        elif "equity" in category_lower or "capital" in category_lower or "reserve" in category_lower:
            grouped["equity"].extend(items)
        elif "pnl" in category_lower or "revenue" in category_lower or "income" in category_lower:
            grouped["revenue"].extend(items)
        elif "expense" in category_lower or "cost" in category_lower:
            grouped["expenses"].extend(items)
        else:
            grouped["unclassified"].extend(items)
    
    # Calculate totals
    totals = {}
    for group_name, items_list in grouped.items():
        totals[group_name] = {
            "count": len(items_list),
            "total": sum(item.get("amount", 0) for item in items_list)
        }
    
    return {
        "grouped": grouped,
        "totals": totals
    }


def generate_schedule3_note(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Schedule III notes based on classified items.
    
    Args:
        data: Dictionary containing classified items and note type
        
    Returns:
        Dictionary with generated note structure
    """
    rulebook_section = get_section("schedule_iii_engine")
    notes_automation = rulebook_section.get("notes_automation", {})
    
    note_type = data.get("note_type", "general")
    items = data.get("items", [])
    
    if note_type == "ppe":
        ppe_note = notes_automation.get("ppe_note", {})
        required_fields = ppe_note.get("required_fields", [])
        
        return {
            "note_type": "Property, Plant and Equipment",
            "required_fields": required_fields,
            "structure": ppe_note,
            "items_count": len(items)
        }
    
    elif note_type == "trade_receivables":
        tr_note = notes_automation.get("trade_receivables_note", {})
        ageing_buckets = tr_note.get("ageing_buckets", [])
        
        return {
            "note_type": "Trade Receivables",
            "ageing_buckets": ageing_buckets,
            "disclosures": tr_note.get("disclosures", []),
            "items_count": len(items)
        }
    
    else:
        return {
            "note_type": "General",
            "items_count": len(items),
            "message": "Note structure generated based on items"
        }

