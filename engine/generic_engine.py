"""
Generic Engine for CA Super Tool.
Handles generic rule expansion, logic tree generation, and mapping rules.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_rulebook, get_section


def expand_rules(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand generic rules based on context.
    
    Args:
        data: Dictionary containing rule context and parameters
        
    Returns:
        Dictionary with expanded rules
    """
    rule_type = data.get("rule_type", "")
    context = data.get("context", {})
    
    rulebook = get_rulebook()
    
    # Critical fix: Handle None rulebook
    if rulebook is None:
        return {
            "expanded_rules": [],
            "rule_type": rule_type,
            "rules_count": 0,
            "error": "Rulebook not loaded"
        }
    
    sections = rulebook.get("sections", {}) or {}
    
    # Critical fix: Ensure sections is always a dict
    if not isinstance(sections, dict):
        sections = {}
    
    expanded_rules = []
    
    # Expand based on rule type
    if rule_type == "schedule3":
        schedule3_section = get_section("schedule_iii_engine")
        mapping_rules = schedule3_section.get("schedule_iii_mapping_rules", [])
        expanded_rules = mapping_rules
    
    elif rule_type == "gst":
        gst_section = get_section("gst_itc_engine")
        itc_rules = gst_section.get("general_itc_principles", {})
        expanded_rules = itc_rules.get("conditions_for_itc", [])
    
    elif rule_type == "tds":
        tds_section = get_section("tds_tcs_engine")
        tds_sections = tds_section.get("tds_sections", {})
        expanded_rules = list(tds_sections.keys()) if isinstance(tds_sections, dict) else []
    
    else:
        # Generic expansion from all sections
        # Safe iteration: sections is guaranteed to be a dict
        for section_name, section_data in sections.items():
            if isinstance(section_data, dict):
                expanded_rules.append({
                    "section": section_name,
                    "rules": section_data
                })
    
    return {
        "expanded_rules": expanded_rules,
        "rule_type": rule_type,
        "rules_count": len(expanded_rules)
    }


def generate_logic_tree(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a logic tree for decision-making based on rules.
    
    Args:
        data: Dictionary containing decision parameters
        
    Returns:
        Dictionary with generated logic tree
    """
    decision_point = data.get("decision_point", "")
    parameters = data.get("parameters", {})
    
    # Simple logic tree structure
    tree = {
        "root": decision_point,
        "branches": [],
        "leaves": []
    }
    
    if decision_point == "itc_eligibility":
        tree["branches"] = [
            {"condition": "invoice_in_2b", "action": "check_compliance"},
            {"condition": "supplier_compliant", "action": "allow_itc"},
            {"condition": "blocked_category", "action": "deny_itc"}
        ]
        tree["leaves"] = ["allowed", "blocked", "conditional"]
    
    elif decision_point == "tds_applicability":
        tree["branches"] = [
            {"condition": "check_threshold", "action": "calculate_rate"},
            {"condition": "check_section", "action": "apply_tds"},
            {"condition": "pan_available", "action": "use_base_rate"}
        ]
        tree["leaves"] = ["tds_applicable", "tds_not_applicable"]
    
    else:
        tree["branches"] = [{"condition": "generic", "action": "evaluate"}]
        tree["leaves"] = ["result"]
    
    return {
        "logic_tree": tree,
        "decision_point": decision_point
    }


def apply_mapping_rules(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply mapping rules to transform data.
    
    Args:
        data: Dictionary containing items to map and mapping type
        
    Returns:
        Dictionary with mapped results
    """
    items = data.get("items", [])
    mapping_type = data.get("mapping_type", "schedule3")
    
    mapped_items = []
    
    if mapping_type == "schedule3":
        from engine.schedule3_engine import classify_schedule3
        result = classify_schedule3({"items": items})
        mapped_items = result.get("classified", {})
    
    elif mapping_type == "tds":
        from engine.tds_engine import classify_section
        for item in items:
            classification = classify_section(item)
            mapped_items.append({
                **item,
                "tds_section": classification.get("section"),
                "tds_rate": classification.get("rate")
            })
    
    else:
        # Generic mapping
        for item in items:
            mapped_items.append({
                **item,
                "mapped": True
            })
    
    return {
        "mapped_items": mapped_items,
        "mapping_type": mapping_type,
        "items_mapped": len(mapped_items)
    }

