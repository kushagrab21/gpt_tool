"""
GST Reconciliation Engine for CA Super Tool.
Handles various GST reconciliation tasks with full invoice-level, supplier-level, and return-level logic.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict


def _get_invoice_key(invoice: Dict[str, Any]) -> str:
    """
    Generate matching key for an invoice.
    
    Args:
        invoice: Invoice dictionary
        
    Returns:
        Matching key string
    """
    supplier_gstin = invoice.get("supplier_gstin", "") or invoice.get("gstin", "")
    invoice_no = invoice.get("invoice_no", "") or invoice.get("invoice_number", "")
    invoice_date = invoice.get("invoice_date", "") or invoice.get("date", "")
    return f"{supplier_gstin}|{invoice_no}|{invoice_date}"


def _calculate_total_tax(invoice: Dict[str, Any]) -> float:
    """
    Calculate total tax from an invoice.
    
    Args:
        invoice: Invoice dictionary
        
    Returns:
        Total tax amount
    """
    igst = float(invoice.get("igst", 0) or 0)
    cgst = float(invoice.get("cgst", 0) or 0)
    sgst = float(invoice.get("sgst", 0) or 0)
    cess = float(invoice.get("cess", 0) or 0)
    return igst + cgst + sgst + cess


def _is_perfect_match(invoice1: Dict[str, Any], invoice2: Dict[str, Any], tolerance: float = 0.01) -> bool:
    """
    Check if two invoices match within tolerance.
    
    Args:
        invoice1: First invoice
        invoice2: Second invoice
        tolerance: Tolerance for matching
        
    Returns:
        True if invoices match within tolerance
    """
    tax1 = _calculate_total_tax(invoice1)
    tax2 = _calculate_total_tax(invoice2)
    value1 = float(invoice1.get("taxable_value", 0) or 0)
    value2 = float(invoice2.get("taxable_value", 0) or 0)
    
    tax_diff = abs(tax1 - tax2)
    value_diff = abs(value1 - value2)
    
    return tax_diff <= tolerance and value_diff <= tolerance


def _bucket_invoices_2b_3b(
    invoices_2b: List[Dict[str, Any]],
    invoices_3b: List[Dict[str, Any]],
    tolerance: float = 0.01
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Bucket invoices for 2B vs 3B reconciliation.
    
    Args:
        invoices_2b: List of 2B invoices
        invoices_3b: List of 3B invoices (if available)
        tolerance: Tolerance for matching
        
    Returns:
        Dictionary of buckets
    """
    buckets = {
        "perfect_match": [],
        "in_2b_not_in_3b": [],
        "in_3b_not_in_2b": [],
        "value_mismatch": [],
        "itc_ineligible": [],
        "pending_itc": []
    }
    
    # Create lookup for 3B invoices
    invoices_3b_lookup = {}
    for inv in invoices_3b:
        key = _get_invoice_key(inv)
        invoices_3b_lookup[key] = inv
    
    # Process 2B invoices
    processed_keys = set()
    for inv_2b in invoices_2b:
        key = _get_invoice_key(inv_2b)
        processed_keys.add(key)
        
        # Check ITC eligibility
        eligibility = inv_2b.get("itc_eligibility", "").upper()
        if eligibility == "INELIGIBLE":
            buckets["itc_ineligible"].append(inv_2b)
            continue
        elif eligibility == "PENDING":
            buckets["pending_itc"].append(inv_2b)
            continue
        
        # Check if in 3B
        if key in invoices_3b_lookup:
            inv_3b = invoices_3b_lookup[key]
            if _is_perfect_match(inv_2b, inv_3b, tolerance):
                buckets["perfect_match"].append(inv_2b)
            else:
                buckets["value_mismatch"].append({
                    "invoice_2b": inv_2b,
                    "invoice_3b": inv_3b,
                    "tax_diff": _calculate_total_tax(inv_2b) - _calculate_total_tax(inv_3b),
                    "value_diff": float(inv_2b.get("taxable_value", 0) or 0) - float(inv_3b.get("taxable_value", 0) or 0)
                })
        else:
            buckets["in_2b_not_in_3b"].append(inv_2b)
    
    # Find invoices in 3B but not in 2B
    for inv_3b in invoices_3b:
        key = _get_invoice_key(inv_3b)
        if key not in processed_keys:
            buckets["in_3b_not_in_2b"].append(inv_3b)
    
    return buckets


def _bucket_invoices_2b_books(
    invoices_2b: List[Dict[str, Any]],
    invoices_books: List[Dict[str, Any]],
    tolerance: float = 0.01
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Bucket invoices for 2B vs Books reconciliation.
    
    Args:
        invoices_2b: List of 2B invoices
        invoices_books: List of books invoices
        tolerance: Tolerance for matching
        
    Returns:
        Dictionary of buckets
    """
    buckets = {
        "perfect_match": [],
        "in_2b_not_in_books": [],
        "in_books_not_in_2b": [],
        "value_mismatch": [],
        "itc_ineligible": [],
        "pending_itc": []
    }
    
    # Create lookup for books invoices
    invoices_books_lookup = {}
    for inv in invoices_books:
        key = _get_invoice_key(inv)
        invoices_books_lookup[key] = inv
    
    # Process 2B invoices
    processed_keys = set()
    for inv_2b in invoices_2b:
        key = _get_invoice_key(inv_2b)
        processed_keys.add(key)
        
        # Check ITC eligibility
        eligibility = inv_2b.get("itc_eligibility", "").upper()
        if eligibility == "INELIGIBLE":
            buckets["itc_ineligible"].append(inv_2b)
            continue
        elif eligibility == "PENDING":
            buckets["pending_itc"].append(inv_2b)
            continue
        
        # Check if in books
        if key in invoices_books_lookup:
            inv_books = invoices_books_lookup[key]
            if _is_perfect_match(inv_2b, inv_books, tolerance):
                buckets["perfect_match"].append(inv_2b)
            else:
                buckets["value_mismatch"].append({
                    "invoice_2b": inv_2b,
                    "invoice_books": inv_books,
                    "tax_diff": _calculate_total_tax(inv_2b) - _calculate_total_tax(inv_books),
                    "value_diff": float(inv_2b.get("taxable_value", 0) or 0) - float(inv_books.get("taxable_value", 0) or 0)
                })
        else:
            buckets["in_2b_not_in_books"].append(inv_2b)
    
    # Find invoices in books but not in 2B
    for inv_books in invoices_books:
        key = _get_invoice_key(inv_books)
        if key not in processed_keys:
            buckets["in_books_not_in_2b"].append(inv_books)
    
    return buckets


def _aggregate_by_supplier(invoices: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate invoices by supplier.
    
    Args:
        invoices: List of invoices
        
    Returns:
        Dictionary keyed by supplier GSTIN with aggregated data
    """
    supplier_data = defaultdict(lambda: {
        "total_taxable": 0.0,
        "total_itc": 0.0,
        "total_invoices": 0,
        "invoices": []
    })
    
    for inv in invoices:
        supplier_gstin = inv.get("supplier_gstin", "") or inv.get("gstin", "")
        if not supplier_gstin:
            continue
        
        taxable_value = float(inv.get("taxable_value", 0) or 0)
        total_tax = _calculate_total_tax(inv)
        
        supplier_data[supplier_gstin]["total_taxable"] += taxable_value
        supplier_data[supplier_gstin]["total_itc"] += total_tax
        supplier_data[supplier_gstin]["total_invoices"] += 1
        supplier_data[supplier_gstin]["invoices"].append(inv)
    
    return dict(supplier_data)


def reconcile_2b_3b(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconcile GSTR-2B with GSTR-3B.
    
    Args:
        micro: Micro-level data containing gstr2b and gstr3b
        settings: Settings including tolerance
        
    Returns:
        Structured result with micro/meso/macro
    """
    tolerance = float(settings.get("tolerance", 0.01))
    
    # Extract data safely
    gstr2b = micro.get("gstr2b", {})
    gstr3b = micro.get("gstr3b", {})
    
    invoices_2b = gstr2b.get("invoices", [])
    invoices_3b = []  # 3B typically doesn't have invoice-level data, use ITC summary
    
    # Bucket invoices
    buckets = _bucket_invoices_2b_3b(invoices_2b, invoices_3b, tolerance)
    
    # Calculate eligible ITC from 2B
    eligible_invoices = buckets["perfect_match"] + buckets["value_mismatch"]
    total_itc_2b_eligible = sum(_calculate_total_tax(inv) for inv in eligible_invoices)
    
    # Get 3B ITC claimed
    itc_3b = gstr3b.get("itc", {})
    itc_3b_claimed = (
        float(itc_3b.get("igst", 0) or 0) +
        float(itc_3b.get("cgst", 0) or 0) +
        float(itc_3b.get("sgst", 0) or 0) +
        float(itc_3b.get("cess", 0) or 0)
    )
    
    # Supplier-level aggregation
    supplier_data = _aggregate_by_supplier(eligible_invoices)
    meso_suppliers = []
    flags_meso = []
    
    for supplier_gstin, data in supplier_data.items():
        supplier_info = {
            "supplier_gstin": supplier_gstin,
            "total_taxable": data["total_taxable"],
            "total_itc_2b": data["total_itc"],
            "total_invoices": data["total_invoices"]
        }
        
        # Check for issues
        if data["total_invoices"] == 0:
            flags_meso.append(f"Supplier {supplier_gstin}: No eligible invoices")
        
        meso_suppliers.append(supplier_info)
    
    # Macro-level summary
    macro_diff = itc_3b_claimed - total_itc_2b_eligible
    macro_flags = []
    
    if macro_diff > tolerance:
        macro_flags.append("ITC claimed higher than eligible")
    elif macro_diff < -tolerance:
        macro_flags.append("ITC claimed lower than eligible")
    
    if len(buckets["itc_ineligible"]) > 0:
        macro_flags.append(f"{len(buckets['itc_ineligible'])} invoices with ineligible ITC")
    
    if len(buckets["pending_itc"]) > 0:
        macro_flags.append(f"{len(buckets['pending_itc'])} invoices with pending ITC eligibility")
    
    return {
        "micro": {
            "buckets": {
                k: len(v) if isinstance(v, list) else v
                for k, v in buckets.items()
            },
            "bucket_details": buckets
        },
        "meso": {
            "suppliers": meso_suppliers,
            "flags": flags_meso
        },
        "macro": {
            "summary": {
                "total_itc_2b_eligible": total_itc_2b_eligible,
                "3b_itc_claimed": itc_3b_claimed,
                "macro_diff": macro_diff,
                "total_invoices_2b": len(invoices_2b),
                "eligible_invoices": len(eligible_invoices)
            },
            "flags": macro_flags
        }
    }


def reconcile_3b_books(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconcile GSTR-3B with Books.
    
    Args:
        micro: Micro-level data containing gstr3b and books
        settings: Settings including tolerance
        
    Returns:
        Structured result with micro/meso/macro
    """
    tolerance = float(settings.get("tolerance", 0.01))
    
    # Extract data safely
    gstr2b = micro.get("gstr2b", {})
    books = micro.get("books", {})
    gstr3b = micro.get("gstr3b", {})
    
    invoices_2b = gstr2b.get("invoices", [])
    invoices_books = books.get("invoices", [])
    
    # Bucket invoices (2B vs Books)
    buckets = _bucket_invoices_2b_books(invoices_2b, invoices_books, tolerance)
    
    # Calculate ITC from 2B (eligible)
    eligible_invoices_2b = buckets["perfect_match"] + [
        item.get("invoice_2b", item) if isinstance(item, dict) and "invoice_2b" in item else item
        for item in buckets["value_mismatch"]
    ]
    total_itc_2b_eligible = sum(
        _calculate_total_tax(inv) if isinstance(inv, dict) else 0
        for inv in eligible_invoices_2b
    )
    
    # Calculate ITC from books
    eligible_invoices_books = buckets["perfect_match"] + [
        item.get("invoice_books", item) if isinstance(item, dict) and "invoice_books" in item else item
        for item in buckets["value_mismatch"]
    ]
    total_itc_books = sum(
        _calculate_total_tax(inv) if isinstance(inv, dict) else 0
        for inv in eligible_invoices_books
    )
    
    # Supplier-level aggregation
    supplier_data_2b = _aggregate_by_supplier(eligible_invoices_2b)
    supplier_data_books = _aggregate_by_supplier(eligible_invoices_books)
    
    meso_suppliers = []
    flags_meso = []
    
    all_suppliers = set(supplier_data_2b.keys()) | set(supplier_data_books.keys())
    
    for supplier_gstin in all_suppliers:
        data_2b = supplier_data_2b.get(supplier_gstin, {"total_itc": 0.0, "total_taxable": 0.0, "total_invoices": 0})
        data_books = supplier_data_books.get(supplier_gstin, {"total_itc": 0.0, "total_taxable": 0.0, "total_invoices": 0})
        
        itc_diff = data_2b["total_itc"] - data_books["total_itc"]
        
        supplier_info = {
            "supplier_gstin": supplier_gstin,
            "total_taxable_2b": data_2b["total_taxable"],
            "total_taxable_books": data_books["total_taxable"],
            "total_itc_2b": data_2b["total_itc"],
            "total_itc_books": data_books["total_itc"],
            "itc_diff": itc_diff,
            "total_invoices_2b": data_2b["total_invoices"],
            "total_invoices_books": data_books["total_invoices"]
        }
        
        # Add flags
        if abs(itc_diff) > tolerance:
            flags_meso.append(f"Supplier {supplier_gstin}: ITC mismatch > tolerance")
        
        if data_2b["total_invoices"] == 0 and data_books["total_invoices"] > 0:
            flags_meso.append(f"Supplier {supplier_gstin}: Missing invoices from 2B")
        
        if data_books["total_invoices"] == 0 and data_2b["total_invoices"] > 0:
            flags_meso.append(f"Supplier {supplier_gstin}: Missing invoices from books")
        
        meso_suppliers.append(supplier_info)
    
    # Get 3B ITC claimed
    itc_3b = gstr3b.get("itc", {})
    itc_3b_claimed = (
        float(itc_3b.get("igst", 0) or 0) +
        float(itc_3b.get("cgst", 0) or 0) +
        float(itc_3b.get("sgst", 0) or 0) +
        float(itc_3b.get("cess", 0) or 0)
    )
    
    # Macro-level summary
    macro_diff = itc_3b_claimed - total_itc_2b_eligible
    macro_flags = []
    
    if macro_diff > tolerance:
        macro_flags.append("ITC claimed higher than eligible")
    elif macro_diff < -tolerance:
        macro_flags.append("ITC claimed lower than eligible")
    
    if len(buckets["in_2b_not_in_books"]) > 0:
        macro_flags.append(f"{len(buckets['in_2b_not_in_books'])} invoices in 2B not in books")
    
    if len(buckets["in_books_not_in_2b"]) > 0:
        macro_flags.append(f"{len(buckets['in_books_not_in_2b'])} invoices in books not in 2B")
    
    if len(buckets["itc_ineligible"]) > 0:
        macro_flags.append(f"{len(buckets['itc_ineligible'])} invoices with ineligible ITC")
    
    if len(buckets["pending_itc"]) > 0:
        macro_flags.append(f"{len(buckets['pending_itc'])} invoices with pending ITC eligibility")
    
    return {
        "micro": {
            "buckets": {
                k: len(v) if isinstance(v, list) else v
                for k, v in buckets.items()
            },
            "bucket_details": buckets
        },
        "meso": {
            "suppliers": meso_suppliers,
            "flags": flags_meso
        },
        "macro": {
            "summary": {
                "total_itc_2b_eligible": total_itc_2b_eligible,
                "total_itc_books": total_itc_books,
                "3b_itc_claimed": itc_3b_claimed,
                "macro_diff": macro_diff,
                "total_invoices_2b": len(invoices_2b),
                "total_invoices_books": len(invoices_books)
            },
            "flags": macro_flags
        }
    }


def reconcile_3b_r1(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconcile GSTR-3B with GSTR-1 (outward supplies).
    
    Args:
        micro: Micro-level data containing gstr3b and gstr1
        settings: Settings including tolerance
        
    Returns:
        Structured result with micro/meso/macro
    """
    tolerance = float(settings.get("tolerance", 0.01))
    
    # Extract data safely
    gstr1 = micro.get("gstr1", {})
    gstr3b = micro.get("gstr3b", {})
    
    invoices_r1 = gstr1.get("invoices", [])
    
    # Calculate outward supplies from R1
    total_taxable_r1 = sum(float(inv.get("taxable_value", 0) or 0) for inv in invoices_r1)
    total_igst_r1 = sum(float(inv.get("igst", 0) or 0) for inv in invoices_r1)
    total_cgst_r1 = sum(float(inv.get("cgst", 0) or 0) for inv in invoices_r1)
    total_sgst_r1 = sum(float(inv.get("sgst", 0) or 0) for inv in invoices_r1)
    total_cess_r1 = sum(float(inv.get("cess", 0) or 0) for inv in invoices_r1)
    total_liability_r1 = total_igst_r1 + total_cgst_r1 + total_sgst_r1 + total_cess_r1
    
    # Get 3B liability
    liability_3b = gstr3b.get("liability", {})
    total_igst_3b = float(liability_3b.get("igst", 0) or 0)
    total_cgst_3b = float(liability_3b.get("cgst", 0) or 0)
    total_sgst_3b = float(liability_3b.get("sgst", 0) or 0)
    total_cess_3b = float(liability_3b.get("cess", 0) or 0)
    total_liability_3b = total_igst_3b + total_cgst_3b + total_sgst_3b + total_cess_3b
    
    # Bucket invoices
    buckets = {
        "in_r1_not_in_3b": [],
        "in_3b_not_in_r1": [],
        "value_mismatch": [],
        "tax_head_mismatch": []
    }
    
    # For now, we compare aggregates (invoice-level matching would require invoice data in 3B)
    # This is a simplified version - full implementation would require 3B invoice-level data
    
    igst_diff = total_igst_r1 - total_igst_3b
    cgst_diff = total_cgst_r1 - total_cgst_3b
    sgst_diff = total_sgst_r1 - total_sgst_3b
    cess_diff = total_cess_r1 - total_cess_3b
    liability_diff = total_liability_r1 - total_liability_3b
    taxable_diff = total_taxable_r1 - float(gstr3b.get("total_taxable", 0) or 0)
    
    if abs(liability_diff) > tolerance:
        buckets["value_mismatch"].append({
            "type": "liability",
            "r1_value": total_liability_r1,
            "3b_value": total_liability_3b,
            "diff": liability_diff
        })
    
    if abs(taxable_diff) > tolerance:
        buckets["value_mismatch"].append({
            "type": "taxable_value",
            "r1_value": total_taxable_r1,
            "3b_value": float(gstr3b.get("total_taxable", 0) or 0),
            "diff": taxable_diff
        })
    
    if abs(igst_diff) > tolerance or abs(cgst_diff) > tolerance or abs(sgst_diff) > tolerance or abs(cess_diff) > tolerance:
        buckets["tax_head_mismatch"].append({
            "igst_diff": igst_diff,
            "cgst_diff": cgst_diff,
            "sgst_diff": sgst_diff,
            "cess_diff": cess_diff
        })
    
    # Macro-level summary
    macro_flags = []
    
    if abs(liability_diff) > tolerance:
        if liability_diff > 0:
            macro_flags.append("Liability in R1 higher than 3B")
        else:
            macro_flags.append("Liability in R1 lower than 3B")
    
    if abs(taxable_diff) > tolerance:
        macro_flags.append("Taxable value mismatch between R1 and 3B")
    
    if len(buckets["tax_head_mismatch"]) > 0:
        macro_flags.append("Tax head mismatches detected")
    
    return {
        "micro": {
            "buckets": {
                k: len(v) if isinstance(v, list) else v
                for k, v in buckets.items()
            },
            "bucket_details": buckets
        },
        "meso": {
            "tax_heads": {
                "igst": {"r1": total_igst_r1, "3b": total_igst_3b, "diff": igst_diff},
                "cgst": {"r1": total_cgst_r1, "3b": total_cgst_3b, "diff": cgst_diff},
                "sgst": {"r1": total_sgst_r1, "3b": total_sgst_3b, "diff": sgst_diff},
                "cess": {"r1": total_cess_r1, "3b": total_cess_3b, "diff": cess_diff}
            },
            "flags": []
        },
        "macro": {
            "summary": {
                "total_taxable_r1": total_taxable_r1,
                "total_liability_r1": total_liability_r1,
                "total_liability_3b": total_liability_3b,
                "liability_diff": liability_diff,
                "taxable_diff": taxable_diff,
                "total_invoices_r1": len(invoices_r1)
            },
            "flags": macro_flags
        }
    }


# Wrapper functions for dispatcher compatibility
def run_auto_gst_fetch_and_map(micro: dict, settings: dict) -> dict:
    """
    Placeholder engine for auto GST fetch and map.
    Implemented later.
    
    Args:
        micro: Micro-level data from fractal expansion
        settings: Optional settings
        
    Returns:
        Result dictionary
    """
    return {
        "engine": "auto_gst_fetch_and_map",
        "received": micro
    }


def run_gst_reconcile_2b_3b(micro: dict, settings: dict) -> dict:
    """
    Reconcile GSTR-2B with GSTR-3B.
    
    Args:
        micro: Micro-level data from fractal expansion
        settings: Optional settings
        
    Returns:
        Structured result dictionary
    """
    return reconcile_2b_3b(micro, settings)


def run_gst_reconcile_3b_books(micro: dict, settings: dict) -> dict:
    """
    Reconcile GSTR-3B with Books.
    
    Args:
        micro: Micro-level data from fractal expansion
        settings: Optional settings
        
    Returns:
        Structured result dictionary
    """
    return reconcile_3b_books(micro, settings)


def run_gst_reconcile_3b_r1(micro: dict, settings: dict) -> dict:
    """
    Reconcile GSTR-3B with GSTR-1.
    
    Args:
        micro: Micro-level data from fractal expansion
        settings: Optional settings
        
    Returns:
        Structured result dictionary
    """
    return reconcile_3b_r1(micro, settings)
