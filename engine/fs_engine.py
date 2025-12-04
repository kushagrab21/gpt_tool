"""
Financial Statements Engine for CA Super Tool.
Handles Trial Balance to Financial Statement mapping and classification.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_section


def map_tb_to_fs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Trial Balance items to Schedule III Financial Statement categories.
    
    Args:
        data: Dictionary containing trial balance items
        
    Returns:
        Dictionary with mapped financial statement structure
    """
    rulebook_section = get_section("schedule_iii_engine") or {}
    mapping_rules = rulebook_section.get("schedule_iii_mapping_rules", [])
    
    # Fallback rules if rulebook not loaded
    if not mapping_rules:
        mapping_rules = [
            {
                "ledger_keywords": ["cash", "cash in hand", "bank"],
                "mapped_to": "current_assets/cash_and_cash_equivalents"
            },
            {
                "ledger_keywords": ["inventory", "stock", "goods"],
                "mapped_to": "current_assets/inventory"
            },
            {
                "ledger_keywords": ["receivable", "debtor"],
                "mapped_to": "current_assets/trade_receivables"
            },
            {
                "ledger_keywords": ["loan", "borrowing"],
                "mapped_to": "non_current_liabilities/long_term_borrowings"
            },
            {
                "ledger_keywords": ["equity", "capital", "reserve"],
                "mapped_to": "equity"
            },
            {
                "ledger_keywords": ["revenue", "income", "sale"],
                "mapped_to": "profit_loss/revenue"
            },
            {
                "ledger_keywords": ["expense", "cost"],
                "mapped_to": "profit_loss/expenses"
            }
        ]
    
    tb_items = data.get("tb_items", [])
    
    balance_sheet = {
        "assets": {"current": [], "non_current": []},
        "liabilities": {"current": [], "non_current": []},
        "equity": []
    }
    
    profit_loss = {
        "revenue": [],
        "expenses": []
    }
    
    for item in tb_items:
        ledger = str(item.get("ledger", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        balance_type = item.get("balance_type", "debit")  # debit or credit
        
        # Find matching rule
        matched_category = None
        for rule in mapping_rules:
            keywords = [kw.lower() for kw in rule.get("ledger_keywords", [])]
            if any(keyword in ledger for keyword in keywords):
                matched_category = rule.get("mapped_to", "")
                break
        
        if matched_category:
            if "asset" in matched_category.lower():
                if "non_current" in matched_category.lower() or "long_term" in matched_category.lower():
                    balance_sheet["assets"]["non_current"].append(item)
                else:
                    balance_sheet["assets"]["current"].append(item)
            elif "liability" in matched_category.lower() or "borrowing" in matched_category.lower():
                if "non_current" in matched_category.lower() or "long_term" in matched_category.lower():
                    balance_sheet["liabilities"]["non_current"].append(item)
                else:
                    balance_sheet["liabilities"]["current"].append(item)
            elif "equity" in matched_category.lower() or "capital" in matched_category.lower():
                balance_sheet["equity"].append(item)
            elif "pnl" in matched_category.lower() or "revenue" in matched_category.lower():
                profit_loss["revenue"].append(item)
            elif "expense" in matched_category.lower():
                profit_loss["expenses"].append(item)
    
    return {
        "balance_sheet": balance_sheet,
        "profit_loss": profit_loss,
        "total_items_mapped": len(tb_items)
    }


def classify_pnl(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Auto-classify Profit & Loss items.
    
    Args:
        data: Dictionary containing P&L items
        
    Returns:
        Dictionary with classified P&L structure
    """
    items = data.get("items", [])
    
    classified = {
        "revenue": {"operating": [], "other": []},
        "expenses": {"operating": [], "finance": [], "depreciation": [], "tax": [], "other": []}
    }
    
    for item in items:
        ledger = str(item.get("ledger", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        
        if "revenue" in ledger or "income" in ledger or "sale" in ledger:
            if "other" in ledger or "non-operating" in ledger:
                classified["revenue"]["other"].append(item)
            else:
                classified["revenue"]["operating"].append(item)
        elif "expense" in ledger or "cost" in ledger:
            if "interest" in ledger or "finance" in ledger:
                classified["expenses"]["finance"].append(item)
            elif "depreciation" in ledger or "amortization" in ledger:
                classified["expenses"]["depreciation"].append(item)
            elif "tax" in ledger:
                classified["expenses"]["tax"].append(item)
            else:
                classified["expenses"]["operating"].append(item)
    
    return classified


def classify_bs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Auto-classify Balance Sheet items using rulebook schedule_iii_mapping_rules.
    
    Args:
        data: Dictionary containing Balance Sheet items
        
    Returns:
        Dictionary with classified Balance Sheet structure in fractal format
    """
    rulebook_section = get_section("schedule_iii_engine") or {}
    mapping_rules = rulebook_section.get("schedule_iii_mapping_rules", [])
    
    # Get asset/liability classification from rulebook
    asset_classification = rulebook_section.get("asset_classification", {})
    liability_classification = rulebook_section.get("liability_classification", {})
    equity_classification = rulebook_section.get("equity_classification", {})
    
    items = data.get("items", [])
    
    classified = {
        "assets": {
            "current": [],
            "non_current": []
        },
        "liabilities": {
            "current": [],
            "non_current": []
        },
        "equity": []
    }
    
    unmatched_items = []
    flags = []
    
    for item in items:
        ledger = str(item.get("ledger", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        balance_type = item.get("balance_type", "debit")
        
        matched = False
        matched_category = None
        
        # Try rulebook mapping rules first
        for rule in mapping_rules:
            keywords = [kw.lower() for kw in rule.get("ledger_keywords", [])]
            if any(keyword in ledger for keyword in keywords):
                matched_category = rule.get("mapped_to", "")
                matched = True
                break
        
        if matched and matched_category:
            # Parse category (e.g., "non_current_assets/ppe" or "current_liabilities/other_current_liabilities")
            category_parts = matched_category.split("/")
            
            if len(category_parts) >= 2:
                main_category = category_parts[0]
                sub_category = category_parts[1]
                
                # Add classification metadata to item
                item_with_classification = {
                    **item,
                    "classified_category": matched_category,
                    "rule_matched": rule.get("id", "")
                }
                
                if "asset" in main_category.lower():
                    if "non_current" in main_category.lower():
                        classified["assets"]["non_current"].append(item_with_classification)
                    else:
                        classified["assets"]["current"].append(item_with_classification)
                elif "liability" in main_category.lower() or "borrowing" in main_category.lower():
                    if "non_current" in main_category.lower():
                        classified["liabilities"]["non_current"].append(item_with_classification)
                    else:
                        classified["liabilities"]["current"].append(item_with_classification)
                elif "equity" in main_category.lower() or "capital" in main_category.lower():
                    classified["equity"].append(item_with_classification)
                elif "pnl" in main_category.lower():
                    # P&L items shouldn't be in BS, but handle gracefully
                    flags.append(f"P&L item found in BS classification: {ledger}")
                    unmatched_items.append(item)
                else:
                    unmatched_items.append(item)
            else:
                unmatched_items.append(item)
        else:
            # Fallback to balance type logic
            if balance_type == "debit":
                # Check if it's clearly current (cash, inventory, receivables)
                if any(kw in ledger for kw in ["cash", "bank", "inventory", "stock", "receivable", "debtor", "advance"]):
                    classified["assets"]["current"].append(item)
                elif any(kw in ledger for kw in ["ppe", "property", "plant", "equipment", "machinery", "building", "furniture", "intangible"]):
                    classified["assets"]["non_current"].append(item)
                else:
                    # Default to non-current for debit balances
                    classified["assets"]["non_current"].append(item)
            elif balance_type == "credit":
                if any(kw in ledger for kw in ["equity", "capital", "reserve", "surplus"]):
                    classified["equity"].append(item)
                elif any(kw in ledger for kw in ["payable", "creditor", "borrowing", "loan"]):
                    # Check if long-term
                    if any(kw in ledger for kw in ["long", "term", "non-current"]):
                        classified["liabilities"]["non_current"].append(item)
                    else:
                        classified["liabilities"]["current"].append(item)
                else:
                    # Default to current liability
                    classified["liabilities"]["current"].append(item)
            
            unmatched_items.append(item)
            flags.append(f"Item classified using fallback logic: {ledger}")
    
    # Build fractal output
    micro = {
        "items": items,
        "classified": classified,
        "unmatched_items": unmatched_items
    }
    
    meso = {
        "classification_summary": {
            "current_assets_count": len(classified["assets"]["current"]),
            "non_current_assets_count": len(classified["assets"]["non_current"]),
            "current_liabilities_count": len(classified["liabilities"]["current"]),
            "non_current_liabilities_count": len(classified["liabilities"]["non_current"]),
            "equity_count": len(classified["equity"]),
            "unmatched_count": len(unmatched_items)
        },
        "rulebook_used": bool(mapping_rules),
        "flags": flags
    }
    
    macro = {
        "summary": {
            "total_items": len(items),
            "classified_items": len(items) - len(unmatched_items),
            "rulebook_integrated": bool(mapping_rules),
            "total_assets": sum(
                item.get("amount", 0) for item in classified["assets"]["current"] + classified["assets"]["non_current"]
            ),
            "total_liabilities": sum(
                item.get("amount", 0) for item in classified["liabilities"]["current"] + classified["liabilities"]["non_current"]
            ),
            "total_equity": sum(item.get("amount", 0) for item in classified["equity"])
        },
        "flags": flags
    }
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
    }


def map_cashflow(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map items to Cash Flow Statement categories using AS3 rules from rulebook.
    Ensures PPE-related items are classified as investing activities.
    
    Args:
        data: Dictionary containing transaction/ledger data
        
    Returns:
        Dictionary with cash flow mapping in fractal format
    """
    # Get AS3 cashflow rules from rulebook
    rulebook = get_section("as_standards") or {}
    as3_section = rulebook.get("AS3", {}) if isinstance(rulebook, dict) else {}
    
    # Get classification examples from AS3
    operating_examples = as3_section.get("operating_examples", {})
    investing_examples = as3_section.get("investing_examples", [])
    financing_examples = as3_section.get("financing_examples", [])
    
    # Get schedule III mapping for PPE detection
    schedule3_section = get_section("schedule_iii_engine") or {}
    asset_classification = schedule3_section.get("asset_classification", {})
    non_current_assets = asset_classification.get("non_current_assets", [])
    
    items = data.get("items", [])
    
    cashflow = {
        "operating": [],
        "investing": [],
        "financing": []
    }
    
    flags = []
    unmatched_items = []
    
    # PPE keywords for investing classification
    ppe_keywords = ["ppe", "property", "plant", "equipment", "machinery", "building", 
                    "furniture", "fixtures", "vehicle", "capital work", "cwip", 
                    "intangible", "goodwill", "patent", "trademark"]
    
    # Operating keywords
    operating_keywords = ["sale", "purchase", "expense", "revenue", "operating", 
                        "supplier", "customer", "employee", "salary", "rent", 
                        "utility", "tax", "gst", "tds"]
    
    # Financing keywords
    financing_keywords = ["loan", "borrowing", "equity", "share", "capital", 
                         "dividend", "interest paid", "debt", "repayment"]
    
    # Investing keywords (beyond PPE)
    investing_keywords = ["investment", "purchase of", "sale of", "advance", 
                         "loan advanced", "loan recovered"]
    
    for item in items:
        ledger = str(item.get("ledger", "")).lower()
        description = str(item.get("description", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        
        combined_text = f"{ledger} {description}"
        
        classified = False
        
        # PRIORITY 1: Check for PPE/investing activities (CRITICAL - must be investing)
        if any(keyword in combined_text for keyword in ppe_keywords):
            # Special check: "Purchase of machinery" MUST be investing
            if "purchase" in combined_text and any(kw in combined_text for kw in ["machinery", "equipment", "plant", "ppe"]):
                cashflow["investing"].append({
                    **item,
                    "category": "investing",
                    "sub_category": "purchase_of_ppe",
                    "rule_applied": "AS3_investing_examples"
                })
                classified = True
            elif "sale" in combined_text and any(kw in combined_text for kw in ["machinery", "equipment", "plant", "ppe"]):
                cashflow["investing"].append({
                    **item,
                    "category": "investing",
                    "sub_category": "sale_of_ppe",
                    "rule_applied": "AS3_investing_examples"
                })
                classified = True
            elif any(kw in combined_text for kw in ["investment", "loan advanced", "loan recovered"]):
                cashflow["investing"].append({
                    **item,
                    "category": "investing",
                    "sub_category": "investments_loans",
                    "rule_applied": "AS3_investing_examples"
                })
                classified = True
        
        # PRIORITY 2: Check for financing activities
        if not classified and any(keyword in combined_text for keyword in financing_keywords):
            cashflow["financing"].append({
                **item,
                "category": "financing",
                "rule_applied": "AS3_financing_examples"
            })
            classified = True
        
        # PRIORITY 3: Check for operating activities
        if not classified and any(keyword in combined_text for keyword in operating_keywords):
            cashflow["operating"].append({
                **item,
                "category": "operating",
                "rule_applied": "AS3_operating_examples"
            })
            classified = True
        
        # PRIORITY 4: Check investing keywords (non-PPE)
        if not classified and any(keyword in combined_text for keyword in investing_keywords):
            cashflow["investing"].append({
                **item,
                "category": "investing",
                "rule_applied": "AS3_investing_examples"
            })
            classified = True
        
        # Default fallback
        if not classified:
            cashflow["operating"].append({
                **item,
                "category": "operating",
                "rule_applied": "default_fallback",
                "note": "Defaulted to operating - review required"
            })
            unmatched_items.append(item)
            flags.append(f"Item defaulted to operating: {ledger}")
    
    # Build fractal output
    micro = {
        "items": items,
        "cashflow": cashflow,
        "unmatched_items": unmatched_items
    }
    
    meso = {
        "classification_summary": {
            "operating_count": len(cashflow["operating"]),
            "investing_count": len(cashflow["investing"]),
            "financing_count": len(cashflow["financing"]),
            "unmatched_count": len(unmatched_items)
        },
        "rulebook_used": bool(as3_section),
        "flags": flags
    }
    
    macro = {
        "summary": {
            "total_items": len(items),
            "operating_total": sum(item.get("amount", 0) for item in cashflow["operating"]),
            "investing_total": sum(item.get("amount", 0) for item in cashflow["investing"]),
            "financing_total": sum(item.get("amount", 0) for item in cashflow["financing"]),
            "rulebook_integrated": bool(as3_section),
            "ppe_items_investing": sum(
                1 for item in cashflow["investing"] 
                if item.get("sub_category") == "purchase_of_ppe"
            )
        },
        "flags": flags
    }
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
    }


def check_tb_errors(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check Trial Balance for common errors.
    
    Args:
        data: Dictionary containing trial balance data
        
    Returns:
        Dictionary with error detection results
    """
    errors = []
    warnings = []
    
    tb_items = data.get("tb_items", [])
    
    total_debit = sum(float(item.get("amount", 0) or 0) for item in tb_items if item.get("balance_type") == "debit")
    total_credit = sum(float(item.get("amount", 0) or 0) for item in tb_items if item.get("balance_type") == "credit")
    
    # Check balance
    difference = abs(total_debit - total_credit)
    if difference > 0.01:
        errors.append({
            "type": "trial_balance_not_balanced",
            "message": f"Trial balance difference: {difference}",
            "severity": "high"
        })
    
    # Check for suspicious amounts
    for item in tb_items:
        amount = abs(float(item.get("amount", 0) or 0))
        if amount > 10000000:  # Very large amount
            warnings.append({
                "type": "large_amount",
                "ledger": item.get("ledger"),
                "amount": amount,
                "severity": "medium"
            })
    
    return {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "total_debit": total_debit,
        "total_credit": total_credit,
        "difference": difference
    }


def analyze_ratios(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform basic ratio analysis.
    
    Args:
        data: Dictionary containing financial statement data
        
    Returns:
        Dictionary with calculated ratios
    """
    bs = data.get("balance_sheet", {})
    pnl = data.get("profit_loss", {})
    
    # Calculate basic ratios
    current_assets = sum(item.get("amount", 0) for item in bs.get("assets", {}).get("current", []))
    current_liabilities = sum(item.get("amount", 0) for item in bs.get("liabilities", {}).get("current", []))
    
    revenue = sum(item.get("amount", 0) for item in pnl.get("revenue", {}).get("operating", []))
    expenses = sum(item.get("amount", 0) for item in pnl.get("expenses", {}).get("operating", []))
    
    ratios = {}
    
    if current_liabilities > 0:
        ratios["current_ratio"] = current_assets / current_liabilities
    
    if revenue > 0:
        ratios["profit_margin"] = (revenue - expenses) / revenue
    
    return {
        "ratios": ratios,
        "calculated_at": "basic_level"
    }

