"""
Rulebook Loader for CA Super Tool.
Loads and caches the YAML rulebook for use across all engines.
"""

import yaml
import os
from typing import Dict, Any
from functools import lru_cache

# Path to the rulebook YAML file
RULEBOOK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "complete_ca_rulebook_v2.yaml"
)


@lru_cache(maxsize=1)
def get_rulebook() -> Dict[str, Any]:
    """
    Load and cache the YAML rulebook.
    
    Uses LRU cache to ensure the rulebook is only loaded once.
    
    Returns:
        Dictionary containing the entire rulebook structure
        
    Raises:
        FileNotFoundError: If the rulebook file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    if not os.path.exists(RULEBOOK_PATH):
        raise FileNotFoundError(
            f"Rulebook file not found at: {RULEBOOK_PATH}. "
            "Please ensure complete_ca_rulebook_v2.yaml exists in the project root."
        )
    
    try:
        with open(RULEBOOK_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            # Try to fix common YAML issues
            # Remove code block markers if present
            if content.startswith('```'):
                # Find and remove code block markers
                lines = content.split('\n')
                if lines[0].strip().startswith('```'):
                    lines = lines[1:]
                if lines[-1].strip().startswith('```'):
                    lines = lines[:-1]
                content = '\n'.join(lines)
            
            rulebook = yaml.safe_load(content)
            
            if rulebook is None:
                # If YAML is empty or invalid, return empty structure
                return {"sections": {}}
            
            # Ensure sections key exists
            if "sections" not in rulebook:
                rulebook["sections"] = {}
            
            return rulebook
    except yaml.YAMLError as e:
        # Return minimal structure if YAML parsing fails
        print(f"Warning: YAML parsing error: {e}. Using fallback structure.")
        return {"sections": {}}


def get_section(section_name: str) -> Dict[str, Any]:
    """
    Get a specific section from the rulebook.
    
    Args:
        section_name: Name of the section (e.g., 'schedule_iii_engine', 'gst_itc_engine')
        
    Returns:
        Dictionary containing the section data, or empty dict if not found
    """
    try:
        rulebook = get_rulebook()
        if rulebook is None:
            return {}
        sections = rulebook.get("sections", {})
        if sections is None:
            return {}
        return sections.get(section_name, {}) or {}
    except Exception:
        return {}

