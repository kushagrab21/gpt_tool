"""
Invariant enforcement module for CA Super Tool.
Enforces business rules and invariants on processed data.
"""

from typing import Dict, Any, Tuple


def enforce_invariants(fractal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Run invariant checks (IC1-IC4) on fractal data structure.
    
    IC1: micro exists
    IC2: micro/meso/macro keys exist
    IC3: no empty keys
    IC4: data types valid
    
    Args:
        fractal: Fractal data structure to validate
        
    Returns:
        Tuple of (bool, report_dict):
        - bool: True if all invariants pass, False otherwise
        - report_dict: Detailed report of invariant checks
    """
    report = {
        "ic1": {"passed": False, "message": ""},
        "ic2": {"passed": False, "message": ""},
        "ic3": {"passed": False, "message": ""},
        "ic4": {"passed": False, "message": ""}
    }
    
    # IC1: micro exists
    if "micro" in fractal:
        report["ic1"]["passed"] = True
        report["ic1"]["message"] = "micro key exists"
    else:
        report["ic1"]["message"] = "micro key missing"
    
    # IC2: micro/meso/macro keys exist
    required_keys = ["micro", "meso", "macro"]
    missing_keys = [key for key in required_keys if key not in fractal]
    if not missing_keys:
        report["ic2"]["passed"] = True
        report["ic2"]["message"] = "All required keys (micro/meso/macro) exist"
    else:
        report["ic2"]["message"] = f"Missing keys: {missing_keys}"
    
    # IC3: no empty keys
    empty_keys = []
    for key, value in fractal.items():
        if value is None or value == "" or (isinstance(value, dict) and len(value) == 0):
            empty_keys.append(key)
    
    if not empty_keys:
        report["ic3"]["passed"] = True
        report["ic3"]["message"] = "No empty keys found"
    else:
        report["ic3"]["message"] = f"Empty keys found: {empty_keys}"
    
    # IC4: data types valid
    type_valid = True
    type_errors = []
    
    if "micro" in fractal:
        if not isinstance(fractal["micro"], dict):
            type_valid = False
            type_errors.append("micro must be dict")
    
    if "meso" in fractal:
        if not isinstance(fractal["meso"], dict):
            type_valid = False
            type_errors.append("meso must be dict")
    
    if "macro" in fractal:
        if not isinstance(fractal["macro"], dict):
            type_valid = False
            type_errors.append("macro must be dict")
    
    if type_valid:
        report["ic4"]["passed"] = True
        report["ic4"]["message"] = "All data types valid"
    else:
        report["ic4"]["message"] = f"Type errors: {type_errors}"
    
    # Overall result: all invariants must pass
    all_passed = all(check["passed"] for check in report.values())
    
    return all_passed, report

