"""
Dispatcher module for CA Super Tool.
Routes tasks to appropriate specialized engines.
"""

from typing import Dict, Any


def dispatch(task: str, fractal: dict, settings: dict) -> dict:
    """
    Route tasks to the appropriate specialized engine.
    
    Receives FRACTAL structure, not raw input.
    Passes fractal['micro'] to engines.
    
    Args:
        task: The task name to execute
        fractal: Fractal data structure (contains micro/meso/macro)
        settings: Optional settings for the task
        
    Returns:
        Dictionary containing the result from the engine
        
    Raises:
        ValueError: If the task is not recognized
    """
    # Extract micro data from fractal
    micro = fractal.get("micro", {})
    
    # Import engines (lazy import to avoid circular dependencies)
    from engine.sales_invoice import run_sales_invoice_prepare
    from engine.gst_reconcile import (
        run_auto_gst_fetch_and_map,
        run_gst_reconcile_2b_3b,
        run_gst_reconcile_3b_books,
        run_gst_reconcile_3b_r1
    )
    from engine.tds_classifier import run_tds_liability
    from engine.auto_entries import run_auto_entries
    from engine.tax_audit import run_tax_audit
    
    # Task routing map
    task_map = {
        "sales_invoice_prepare": run_sales_invoice_prepare,
        "auto_gst_fetch_and_map": run_auto_gst_fetch_and_map,
        "tds_liability": run_tds_liability,
        "auto_entries": run_auto_entries,
        "tax_audit": run_tax_audit,
        "gst_reconcile_2b_3b": run_gst_reconcile_2b_3b,
        "gst_reconcile_3b_books": run_gst_reconcile_3b_books,
        "gst_reconcile_3b_r1": run_gst_reconcile_3b_r1,
    }
    
    # Route to appropriate engine
    if task not in task_map:
        raise ValueError(f"Unknown task: {task}. Supported tasks: {list(task_map.keys())}")
    
    engine_func = task_map[task]
    return engine_func(micro, settings)

