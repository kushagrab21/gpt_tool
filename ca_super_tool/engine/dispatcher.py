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
    
    # Normalize task name
    task_normalized = task.strip().lower()
    
    # Import legacy engines (lazy import to avoid circular dependencies)
    from ca_super_tool.engine.sales_invoice import run_sales_invoice_prepare
    from ca_super_tool.engine.gst_reconcile import (
        run_auto_gst_fetch_and_map,
        run_gst_reconcile_2b_3b,
        run_gst_reconcile_3b_books,
        run_gst_reconcile_3b_r1
    )
    from ca_super_tool.engine.tds_classifier import run_tds_liability
    from ca_super_tool.engine.auto_entries import run_auto_entries
    from ca_super_tool.engine.tax_audit import run_tax_audit
    
    # Import new engines
    from ca_super_tool.engine.schedule3_engine import classify_schedule3, group_schedule3, generate_schedule3_note
    from ca_super_tool.engine.gst_engine import (
        reconcile_3b_2b,
        classify_itc,
        detect_itc_mismatch,
        vendor_level_itc,
        check_gst_errors
    )
    from ca_super_tool.engine.tds_engine import classify_section, tag_ledger, detect_default
    from ca_super_tool.engine.journal_engine import suggest_journal_entries
    from ca_super_tool.engine.fs_engine import (
        map_tb_to_fs,
        classify_pnl,
        classify_bs,
        map_cashflow,
        check_tb_errors,
        analyze_ratios
    )
    from ca_super_tool.engine.audit_engine import detect_redflags, test_ic_control
    from ca_super_tool.engine.ledger_engine import normalize_ledgers, group_ledgers, map_ledger_groups, detect_ledger_errors
    from ca_super_tool.engine.bank_reco_engine import match_bank_reco, detect_unmatched
    from ca_super_tool.engine.generic_engine import expand_rules, generate_logic_tree, apply_mapping_rules
    
    # Legacy task routing map (preserve existing functionality)
    legacy_task_map = {
        "sales_invoice_prepare": run_sales_invoice_prepare,
        "auto_gst_fetch_and_map": run_auto_gst_fetch_and_map,
        "tds_liability": run_tds_liability,
        "auto_entries": run_auto_entries,
        "tax_audit": run_tax_audit,
        "gst_reconcile_2b_3b": run_gst_reconcile_2b_3b,
        "gst_reconcile_3b_books": run_gst_reconcile_3b_books,
        "gst_reconcile_3b_r1": run_gst_reconcile_3b_r1,
    }
    
    # New GPT task routing map
    new_task_map = {
        # Schedule III
        "schedule3_classification": classify_schedule3,
        "schedule3_grouping": group_schedule3,
        "schedule3_note_generation": generate_schedule3_note,
        
        # GST / ITC
        "gst_3b_2b_reconciliation": reconcile_3b_2b,
        "gst_itc_classification": classify_itc,
        "gst_itc_mismatch_detection": detect_itc_mismatch,
        "gst_vendor_level_itc": vendor_level_itc,
        "gst_error_checking": check_gst_errors,
        
        # TDS / TCS
        "tds_section_classification": classify_section,
        "tds_ledger_tagging": tag_ledger,
        "tds_default_detection": detect_default,
        
        # Journal Logic
        "auto_journal_suggestion": suggest_journal_entries,
        "ledger_normalization": normalize_ledgers,
        "ledger_group_mapping": map_ledger_groups,
        "ledger_error_detection": detect_ledger_errors,
        
        # Trial Balance Workflows
        "tb_schedule3_mapping": map_tb_to_fs,
        "tb_error_checking": check_tb_errors,
        "tb_ratio_analysis": analyze_ratios,
        
        # Bank Reconciliation
        "bank_reco_matching": match_bank_reco,
        "bank_reco_unmatched_detection": detect_unmatched,
        
        # Financial Statement Automation
        "pnl_auto_classification": classify_pnl,
        "bs_auto_classification": classify_bs,
        "cashflow_auto_mapping": map_cashflow,
        
        # Audit & Internal Control
        "audit_redflag_detection": detect_redflags,
        "ic_control_test": test_ic_control,
        
        # Generic Rule Engine
        "generic_rule_expansion": expand_rules,
        "logic_tree_generation": generate_logic_tree,
        "mapping_rules": apply_mapping_rules,
    }
    
    # Combine both maps
    all_tasks = {**legacy_task_map, **new_task_map}
    
    # Route to appropriate engine
    if task_normalized not in all_tasks:
        # Try case-insensitive match
        task_found = None
        for task_key in all_tasks.keys():
            if task_key.lower() == task_normalized:
                task_found = task_key
                break
        
        if task_found:
            engine_func = all_tasks[task_found]
        else:
            supported_tasks = sorted(list(legacy_task_map.keys()) + list(new_task_map.keys()))
            raise ValueError(
                f"Unknown task: {task}. "
                f"Supported tasks: {supported_tasks[:10]}... (total: {len(supported_tasks)})"
            )
    else:
        engine_func = all_tasks[task_normalized]
    
    # Call engine function
    # New engines expect data directly, legacy engines expect (micro, settings)
    if task_normalized in new_task_map:
        # New engines: pass micro directly as data
        return engine_func(micro)
    else:
        # Legacy engines: pass (micro, settings)
        return engine_func(micro, settings)

