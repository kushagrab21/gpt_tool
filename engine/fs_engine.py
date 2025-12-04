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
    Auto-classify Balance Sheet items.
    
    Args:
        data: Dictionary containing Balance Sheet items
        
    Returns:
        Dictionary with classified Balance Sheet structure
    """
    items = data.get("items", [])
    
    classified = {
        "assets": {"current": [], "non_current": []},
        "liabilities": {"current": [], "non_current": []},
        "equity": []
    }
    
    for item in items:
        ledger = str(item.get("ledger", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        balance_type = item.get("balance_type", "debit")
        
        if balance_type == "debit":
            if "current" in ledger or "short" in ledger:
                classified["assets"]["current"].append(item)
            else:
                classified["assets"]["non_current"].append(item)
        elif balance_type == "credit":
            if "equity" in ledger or "capital" in ledger or "reserve" in ledger:
                classified["equity"].append(item)
            elif "current" in ledger or "short" in ledger:
                classified["liabilities"]["current"].append(item)
            else:
                classified["liabilities"]["non_current"].append(item)
    
    return classified


def map_cashflow(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map items to Cash Flow Statement categories.
    
    Args:
        data: Dictionary containing transaction/ledger data
        
    Returns:
        Dictionary with cash flow mapping
    """
    items = data.get("items", [])
    
    cashflow = {
        "operating": [],
        "investing": [],
        "financing": []
    }
    
    for item in items:
        ledger = str(item.get("ledger", "")).lower()
        amount = float(item.get("amount", 0) or 0)
        
        if any(keyword in ledger for keyword in ["sale", "purchase", "expense", "revenue", "operating"]):
            cashflow["operating"].append(item)
        elif any(keyword in ledger for keyword in ["investment", "asset", "ppe", "capital"]):
            cashflow["investing"].append(item)
        elif any(keyword in ledger for keyword in ["loan", "borrowing", "equity", "capital", "dividend"]):
            cashflow["financing"].append(item)
        else:
            cashflow["operating"].append(item)  # Default
    
    return cashflow


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

