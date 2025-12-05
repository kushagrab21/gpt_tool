"""
Input normalization module for CA Super Tool.
Normalizes and validates input data before processing.
"""

from typing import Dict, Any
from datetime import datetime
import re


def normalize_input(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize input data with safe, non-breaking transformations.
    
    - Ensure keys are strings
    - Convert all numbers to float where possible
    - Convert dates into ISO format if possible
    - Strip whitespace in strings
    - Remove null/None values
    
    Args:
        raw: Raw input data dictionary
        
    Returns:
        Clean normalized data dictionary
    """
    if not isinstance(raw, dict):
        return {}
    
    normalized = {}
    
    for key, value in raw.items():
        # Ensure keys are strings
        clean_key = str(key).strip()
        
        # Skip None/null values
        if value is None:
            continue
        
        # Handle dictionaries recursively
        if isinstance(value, dict):
            normalized[clean_key] = normalize_input(value)
        
        # Handle lists
        elif isinstance(value, list):
            normalized[clean_key] = [
                normalize_input(item) if isinstance(item, dict) else _normalize_value(item)
                for item in value
            ]
        
        # Handle primitive values
        else:
            normalized[clean_key] = _normalize_value(value)
    
    return normalized


def _normalize_value(value: Any) -> Any:
    """
    Normalize a single value.
    
    Args:
        value: Value to normalize
        
    Returns:
        Normalized value
    """
    # Handle strings
    if isinstance(value, str):
        # Strip whitespace
        cleaned = value.strip()
        
        # Try to convert to number if it looks like one
        try:
            if '.' in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except ValueError:
            # Try to parse as date
            date_value = _try_parse_date(cleaned)
            if date_value:
                return date_value
            
            return cleaned if cleaned else None
    
    # Handle numbers - convert to float for consistency
    elif isinstance(value, (int, float)):
        return float(value)
    
    # Handle booleans
    elif isinstance(value, bool):
        return value
    
    # Handle datetime objects
    elif isinstance(value, datetime):
        return value.isoformat()
    
    # Return as-is for other types
    else:
        return value


def _try_parse_date(date_str: str) -> str:
    """
    Try to parse a date string and return ISO format.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        ISO format date string or None if parsing fails
    """
    # Common date formats
    date_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d/%m/%y"
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    # Try regex patterns for common date formats
    patterns = [
        (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
        (r'(\d{2})-(\d{2})-(\d{4})', '%d-%m-%Y'),
        (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),
    ]
    
    for pattern, fmt in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
    
    return None

