"""
Sales Invoice Engine for CA Super Tool.
Handles sales invoice preparation with GST computation and classification.
"""

from typing import Dict, Any, List, Tuple
import math


def get_config(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get configuration with defaults.
    
    Args:
        micro: Micro-level data containing config
        settings: Settings dictionary
        
    Returns:
        Configuration dictionary
    """
    config = micro.get("config", {})
    
    defaults = {
        "default_tax_rate": 18.0,
        "rounding_mode": "NEAREST",  # or "UP", "DOWN"
        "invoice_prefix": "INV",
        "default_currency": "INR",
        "invoice_date": "2024-04-30",
        "invoice_number_seed": 1
    }
    
    # Merge config from micro, then settings, then defaults
    result = defaults.copy()
    result.update(settings.get("config", {}))
    result.update(config)
    
    return result


def generate_invoice_number(micro: Dict[str, Any]) -> str:
    """
    Generate invoice number.
    
    Rules:
    - If existing_invoice_number is provided, use it
    - Else, use prefix and seed from config
    
    Args:
        micro: Micro-level data
        
    Returns:
        Invoice number string
    """
    meta = micro.get("meta", {})
    existing_number = meta.get("existing_invoice_number")
    
    if existing_number:
        return str(existing_number)
    
    config = get_config(micro, {})
    prefix = config.get("invoice_prefix", "INV")
    seed = int(config.get("invoice_number_seed", 1))
    
    return f"{prefix}-{seed:05d}"


def compute_supply_type(customer: Dict[str, Any], seller: Dict[str, Any]) -> str:
    """
    Compute supply type: INTRA or INTER.
    
    Args:
        customer: Customer dictionary
        seller: Seller dictionary
        
    Returns:
        "INTRA" or "INTER"
    """
    customer_state = str(customer.get("state_code", "") or "")
    seller_state = str(seller.get("state_code", "") or "")
    
    if customer_state and seller_state and customer_state == seller_state:
        return "INTRA"
    
    return "INTER"


def compute_invoice_type(customer: Dict[str, Any]) -> str:
    """
    Compute invoice type: B2B or B2C.
    
    Args:
        customer: Customer dictionary
        
    Returns:
        "B2B" or "B2C"
    """
    gstin = customer.get("gstin", "")
    
    if gstin and str(gstin).strip():
        return "B2B"
    
    return "B2C"


def compute_line_values(
    line: Dict[str, Any],
    supply_type: str,
    default_tax_rate: float,
    rounding_mode: str
) -> Dict[str, Any]:
    """
    Compute line-level values including tax.
    
    Args:
        line: Line item dictionary
        supply_type: "INTRA" or "INTER"
        default_tax_rate: Default tax rate in percent
        rounding_mode: Rounding mode (not used per line, but kept for consistency)
        
    Returns:
        Line dictionary with computed values
    """
    quantity = float(line.get("quantity", 0) or 0)
    unit_price = float(line.get("unit_price", 0) or 0)
    discount = float(line.get("discount", 0) or 0)
    is_exempt = line.get("is_exempt", False)
    
    # Effective quantity (floor at 0)
    effective_qty = max(quantity, 0)
    
    # Base value
    base_value = effective_qty * unit_price
    
    # Taxable value before discount
    taxable_value_before_discount = base_value
    
    # Taxable value after discount (floor at 0)
    taxable_value = max(taxable_value_before_discount - discount, 0)
    
    # Initialize tax components
    igst = 0.0
    cgst = 0.0
    sgst = 0.0
    cess = 0.0
    tax_rate = 0.0
    
    # Compute tax if not exempt
    if not is_exempt:
        # Get tax rate
        tax_rate = float(line.get("tax_rate", 0) or 0)
        if tax_rate <= 0:
            tax_rate = default_tax_rate
        
        # Calculate total tax
        total_tax = taxable_value * tax_rate / 100
        
        # Split based on supply type
        if supply_type == "INTRA":
            cgst = total_tax / 2
            sgst = total_tax / 2
            igst = 0.0
        else:  # INTER
            igst = total_tax
            cgst = 0.0
            sgst = 0.0
    
    return {
        "line_no": line.get("line_no", 0),
        "sku": line.get("sku", ""),
        "description": line.get("description", ""),
        "quantity": effective_qty,
        "unit_price": unit_price,
        "discount": discount,
        "taxable_value": taxable_value,
        "tax_rate": tax_rate,
        "igst": igst,
        "cgst": cgst,
        "sgst": sgst,
        "cess": cess,
        "hsn": line.get("hsn", "")
    }


def apply_rounding(value: float, mode: str) -> float:
    """
    Apply rounding to a value.
    
    Args:
        value: Value to round
        mode: "NEAREST", "UP", or "DOWN"
        
    Returns:
        Rounded value
    """
    if mode == "UP":
        return math.ceil(value)
    elif mode == "DOWN":
        return math.floor(value)
    else:  # NEAREST
        return round(value)


def compute_totals(
    lines: List[Dict[str, Any]],
    rounding_mode: str
) -> Dict[str, float]:
    """
    Compute invoice totals with rounding.
    
    Args:
        lines: List of computed line items
        rounding_mode: Rounding mode
        
    Returns:
        Totals dictionary
    """
    total_taxable = sum(float(line.get("taxable_value", 0) or 0) for line in lines)
    total_igst = sum(float(line.get("igst", 0) or 0) for line in lines)
    total_cgst = sum(float(line.get("cgst", 0) or 0) for line in lines)
    total_sgst = sum(float(line.get("sgst", 0) or 0) for line in lines)
    total_cess = sum(float(line.get("cess", 0) or 0) for line in lines)
    
    total_tax = total_igst + total_cgst + total_sgst + total_cess
    
    # Pre-round invoice value
    pre_round_invoice_value = total_taxable + total_tax
    
    # Apply rounding
    invoice_value = apply_rounding(pre_round_invoice_value, rounding_mode)
    
    # Rounding adjustment
    rounding_adjustment = invoice_value - pre_round_invoice_value
    
    return {
        "total_taxable": total_taxable,
        "total_igst": total_igst,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_cess": total_cess,
        "total_tax": total_tax,
        "invoice_value": invoice_value,
        "rounding_adjustment": rounding_adjustment
    }


def build_gst_mapping(
    invoice_type: str,
    supply_type: str,
    customer: Dict[str, Any],
    totals: Dict[str, float]
) -> Dict[str, Any]:
    """
    Build GST mapping hints for 3B and R1.
    
    Args:
        invoice_type: "B2B" or "B2C"
        supply_type: "INTRA" or "INTER"
        customer: Customer dictionary
        totals: Totals dictionary
        
    Returns:
        GST mapping dictionary
    """
    place_of_supply = customer.get("place_of_supply") or customer.get("state_code", "")
    
    return {
        "for_3b": {
            "table": "3.1(a)",  # Outward taxable supplies
            "taxable_value": totals.get("total_taxable", 0),
            "igst": totals.get("total_igst", 0),
            "cgst": totals.get("total_cgst", 0),
            "sgst": totals.get("total_sgst", 0),
            "cess": totals.get("total_cess", 0)
        },
        "for_r1": {
            "section": invoice_type,  # "B2B" or "B2C"
            "place_of_supply": str(place_of_supply),
            "gstin": customer.get("gstin", ""),
            "doc_type": "INV"
        }
    }


def run_sales_invoice_prepare(micro: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare sales invoice with GST computation.
    
    Args:
        micro: Micro-level data containing customer, seller, lines, config
        settings: Optional settings
        
    Returns:
        Dictionary with invoice structure and flags
    """
    flags = []
    
    # Extract data safely
    customer = micro.get("customer", {})
    seller = micro.get("seller", {})
    lines = micro.get("lines", [])
    config = get_config(micro, settings)
    
    if not lines:
        return {
            "invoice": {},
            "flags": ["No line items provided; invoice cannot be generated."]
        }
    
    # Generate invoice number
    invoice_number = generate_invoice_number(micro)
    
    # Get invoice date
    invoice_date = config.get("invoice_date", "2024-04-30")
    currency = config.get("default_currency", "INR")
    default_tax_rate = float(config.get("default_tax_rate", 18.0))
    rounding_mode = config.get("rounding_mode", "NEAREST")
    
    # Compute supply type and invoice type
    supply_type = compute_supply_type(customer, seller)
    invoice_type = compute_invoice_type(customer)
    
    # Flag for missing GSTIN
    if not customer.get("gstin"):
        flags.append("Customer GSTIN missing: treated as B2C")
    
    # Process lines
    computed_lines = []
    used_default_tax_rate = False
    has_exempt_items = False
    
    for idx, line in enumerate(lines):
        # Check if tax rate is missing
        line_tax_rate = float(line.get("tax_rate", 0) or 0)
        if line_tax_rate <= 0 and not line.get("is_exempt", False):
            used_default_tax_rate = True
        
        # Check for exempt items
        if line.get("is_exempt", False):
            has_exempt_items = True
        
        # Compute line values
        computed_line = compute_line_values(
            {**line, "line_no": idx + 1},
            supply_type,
            default_tax_rate,
            rounding_mode
        )
        computed_lines.append(computed_line)
    
    # Add flags
    if used_default_tax_rate:
        flags.append(f"Tax rate inferred from default {default_tax_rate}%")
    
    if has_exempt_items:
        flags.append("Exempt line items detected")
    
    # Compute totals
    totals = compute_totals(computed_lines, rounding_mode)
    
    # Flag for significant rounding
    rounding_adj = abs(totals.get("rounding_adjustment", 0))
    if rounding_adj > 0.5:
        flags.append(f"Significant rounding adjustment: ₹{rounding_adj:.2f}")
    
    # Build GST mapping
    gst_mapping = build_gst_mapping(invoice_type, supply_type, customer, totals)
    
    # Build invoice structure
    invoice = {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "currency": currency,
        "supply_type": supply_type,
        "invoice_type": invoice_type,
        "customer": customer.copy(),
        "seller": seller.copy(),
        "lines": computed_lines,
        "totals": totals,
        "gst_mapping": gst_mapping
    }
    
    return {
        "invoice": invoice,
        "flags": flags
    }
