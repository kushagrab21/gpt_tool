"""
Generic Engine for CA Super Tool.
Handles generic rule expansion, logic tree generation, and mapping rules.
"""

from typing import Dict, Any, List
from engine.rulebook_loader import get_rulebook, get_section


def expand_rules(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand generic rules based on context with reasoning chain.
    
    Args:
        data: Dictionary containing rule context and parameters
        
    Returns:
        Dictionary with expanded rules in fractal format with reasoning tree
    """
    rule_type = data.get("rule_type", "")
    context = data.get("context", {})
    
    rulebook = get_rulebook()
    
    # Critical fix: Handle None rulebook
    if rulebook is None:
        return {
            "micro": {
                "rule_type": rule_type,
                "context": context,
                "expanded_rules": [],
                "error": "Rulebook not loaded"
            },
            "meso": {
                "rules_count": 0,
                "reasoning_chain": ["Rulebook not available"],
                "rulebook_loaded": False
            },
            "macro": {
                "summary": {
                    "rules_count": 0,
                    "rulebook_available": False
                },
                "flags": ["Rulebook not loaded"]
            }
        }
    
    sections = rulebook.get("sections", {}) or {}
    
    # Critical fix: Ensure sections is always a dict
    if not isinstance(sections, dict):
        sections = {}
    
    expanded_rules = []
    reasoning_chain = []
    flags = []
    
    # Expand based on rule type
    if rule_type == "schedule3":
        schedule3_section = get_section("schedule_iii_engine")
        if schedule3_section:
            mapping_rules = schedule3_section.get("schedule_iii_mapping_rules", [])
            expanded_rules = mapping_rules
            reasoning_chain.append(f"Loaded {len(mapping_rules)} Schedule III mapping rules")
            reasoning_chain.append("Rules map ledger keywords to Schedule III categories")
        else:
            flags.append("Schedule III section not found in rulebook")
    
    elif rule_type == "gst":
        gst_section = get_section("gst_itc_engine")
        if gst_section:
            itc_rules = gst_section.get("general_itc_principles", {})
            conditions = itc_rules.get("conditions_for_itc", [])
            expanded_rules = conditions
            reasoning_chain.append(f"Loaded {len(conditions)} GST ITC eligibility conditions")
            reasoning_chain.append("Rules define when ITC can be claimed")
        else:
            flags.append("GST ITC section not found in rulebook")
    
    elif rule_type == "tds":
        tds_section = get_section("tds_tcs_engine")
        if tds_section:
            tds_sections = tds_section.get("tds_sections", {})
            if isinstance(tds_sections, dict):
                expanded_rules = [
                    {
                        "section_key": key,
                        "section_name": value.get("name", ""),
                        "threshold": value.get("threshold") or value.get("threshold_aggregate") or value.get("threshold_single"),
                        "rate": value.get("rate", {}),
                        "rules": value.get("rules", [])
                    }
                    for key, value in tds_sections.items()
                ]
                reasoning_chain.append(f"Loaded {len(expanded_rules)} TDS sections")
                reasoning_chain.append("Each section defines threshold, rate, and applicability rules")
            else:
                flags.append("TDS sections not in expected format")
        else:
            flags.append("TDS section not found in rulebook")
    
    elif rule_type == "cashflow":
        as_standards = get_section("as_standards")
        if as_standards and isinstance(as_standards, dict):
            as3 = as_standards.get("AS3", {})
            if as3:
                expanded_rules = {
                    "categories": as3.get("classification", {}).get("categories", []),
                    "operating_examples": as3.get("operating_examples", {}),
                    "investing_examples": as3.get("investing_examples", []),
                    "financing_examples": as3.get("financing_examples", [])
                }
                reasoning_chain.append("Loaded AS3 cashflow classification rules")
                reasoning_chain.append("Rules define operating, investing, and financing activities")
            else:
                flags.append("AS3 section not found")
        else:
            flags.append("AS standards section not found")
    
    else:
        # Generic expansion from all sections
        # Safe iteration: sections is guaranteed to be a dict
        # CRITICAL FIX: Filter out non-string keys to prevent bool < str comparison errors
        for section_name, section_data in sections.items():
            # Only process string keys to avoid TypeError when sorting/mixing types
            if not isinstance(section_name, str):
                continue
            if isinstance(section_data, dict):
                expanded_rules.append({
                    "section": section_name,
                    "meta": section_data.get("meta", {}),
                    "rules": section_data
                })
        reasoning_chain.append(f"Expanded all {len(expanded_rules)} rulebook sections")
        reasoning_chain.append("Generic expansion includes all available rule sections")
    
    # Build reasoning tree
    reasoning_tree = {
        "root": f"Rule expansion for type: {rule_type}",
        "branches": [
            {
                "step": 1,
                "action": "Load rulebook",
                "result": "success" if rulebook else "failed"
            },
            {
                "step": 2,
                "action": f"Extract {rule_type} rules",
                "result": f"Found {len(expanded_rules)} rules"
            },
            {
                "step": 3,
                "action": "Build reasoning chain",
                "result": f"Generated {len(reasoning_chain)} reasoning steps"
            }
        ],
        "leaves": expanded_rules[:5] if len(expanded_rules) > 5 else expanded_rules  # Sample rules
    }
    
    # Build fractal output
    micro = {
        "rule_type": rule_type,
        "context": context,
        "expanded_rules": expanded_rules,
        "reasoning_tree": reasoning_tree
    }
    
    meso = {
        "rules_count": len(expanded_rules),
        "reasoning_chain": reasoning_chain,
        "rulebook_loaded": rulebook is not None,
        # CRITICAL FIX: Filter to string keys only to prevent bool < str comparison errors
        "sections_available": [k for k in sections.keys() if isinstance(k, str)] if isinstance(sections, dict) else []
    }
    
    macro = {
        "summary": {
            "rule_type": rule_type,
            "rules_count": len(expanded_rules),
            "rulebook_available": rulebook is not None,
            "reasoning_steps": len(reasoning_chain)
        },
        "flags": flags,
        "reasoning_tree": reasoning_tree
    }
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
    }


def generate_logic_tree(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a logic tree for decision-making based on rules from rulebook.
    
    Args:
        data: Dictionary containing decision parameters
        
    Returns:
        Dictionary with generated logic tree in fractal format
    """
    decision_point = data.get("decision_point", "")
    parameters = data.get("parameters", {})
    
    # Get rulebook sections for decision trees
    tds_section = get_section("tds_tcs_engine") or {}
    gst_section = get_section("gst_itc_engine") or {}
    
    tree = {
        "root": decision_point,
        "branches": [],
        "leaves": []
    }
    
    reasoning_chain = []
    
    if decision_point == "itc_eligibility":
        # Use GST rulebook decision tree
        itc_rules = gst_section.get("general_itc_principles", {})
        conditions = itc_rules.get("conditions_for_itc", [])
        
        tree["branches"] = [
            {"condition": "invoice_in_2b", "action": "check_compliance", "rule_source": "gst_itc_engine"},
            {"condition": "supplier_compliant", "action": "allow_itc", "rule_source": "gst_itc_engine"},
            {"condition": "blocked_category", "action": "deny_itc", "rule_source": "gst_itc_engine"}
        ]
        tree["leaves"] = ["allowed", "blocked", "conditional"]
        reasoning_chain.append("Using GST ITC eligibility rules from rulebook")
        reasoning_chain.append(f"Found {len(conditions)} ITC conditions")
    
    elif decision_point == "tds_applicability":
        # Use TDS rulebook decision tree
        classification_engine = tds_section.get("tds_classification_engine", {})
        decision_tree = classification_engine.get("decision_tree", [])
        
        if decision_tree:
            # Convert rulebook decision tree to logic tree format
            tree["branches"] = [
                {
                    "condition": item.get("question", ""),
                    "action": f"if_yes: {item.get('yes', '')}, if_no: {item.get('no', '')}",
                    "rule_source": "tds_classification_engine",
                    "rule_id": item.get("id", "")
                }
                for item in decision_tree
            ]
            tree["leaves"] = ["tds_applicable", "tds_not_applicable"]
            reasoning_chain.append("Using TDS decision tree from rulebook")
            reasoning_chain.append(f"Found {len(decision_tree)} decision nodes")
        else:
            # Fallback
            tree["branches"] = [
                {"condition": "check_threshold", "action": "calculate_rate"},
                {"condition": "check_section", "action": "apply_tds"},
                {"condition": "pan_available", "action": "use_base_rate"}
            ]
            tree["leaves"] = ["tds_applicable", "tds_not_applicable"]
            reasoning_chain.append("Using fallback TDS logic (rulebook decision tree not found)")
    
    elif decision_point == "schedule3_classification":
        # Use Schedule III classification rules
        schedule3_section = get_section("schedule_iii_engine") or {}
        mapping_rules = schedule3_section.get("schedule_iii_mapping_rules", [])
        
        tree["branches"] = [
            {
                "condition": f"Match ledger keywords: {rule.get('ledger_keywords', [])}",
                "action": f"Map to: {rule.get('mapped_to', '')}",
                "rule_source": "schedule_iii_engine",
                "rule_id": rule.get("id", "")
            }
            for rule in mapping_rules[:10]  # Limit to first 10 for readability
        ]
        tree["leaves"] = ["current_asset", "non_current_asset", "current_liability", "non_current_liability", "equity"]
        reasoning_chain.append("Using Schedule III mapping rules from rulebook")
        reasoning_chain.append(f"Found {len(mapping_rules)} mapping rules")
    
    else:
        tree["branches"] = [{"condition": "generic", "action": "evaluate"}]
        tree["leaves"] = ["result"]
        reasoning_chain.append("Generic decision tree (no specific rulebook section found)")
    
    # Build fractal output
    micro = {
        "decision_point": decision_point,
        "parameters": parameters,
        "logic_tree": tree
    }
    
    meso = {
        "reasoning_chain": reasoning_chain,
        "branches_count": len(tree["branches"]),
        "leaves_count": len(tree["leaves"]),
        "rulebook_used": bool(tds_section or gst_section)
    }
    
    macro = {
        "summary": {
            "decision_point": decision_point,
            "tree_complexity": len(tree["branches"]),
            "rulebook_integrated": bool(tds_section or gst_section)
        },
        "logic_tree": tree
    }
    
    return {
        "micro": micro,
        "meso": meso,
        "macro": macro
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

