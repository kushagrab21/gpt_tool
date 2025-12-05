"""
CA Super Tool - Main FastAPI Application
Unified Accounting Reasoning Engine (UARE) for CA-Auto v1.0
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import hashlib
import json
import logging

from ca_super_tool.engine.dispatcher import dispatch
from ca_super_tool.engine.normalize import normalize_input
from ca_super_tool.engine.fractal import run_fractal_expansion
from ca_super_tool.engine.invariants import enforce_invariants

# Configure logging (placeholder structure)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CA Super Tool",
    description="Unified Accounting Reasoning Engine for CA-Auto v1.0",
    version="1.0.0"
)


class SuperToolRequest(BaseModel):
    """Request schema for the CA Super Tool API."""
    task: str
    data: Dict[str, Any] = Field(..., description="Task-specific data dictionary")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional settings dictionary")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task": "schedule3_classification",
                "data": {
                    "items": [
                        {"ledger": "Unsecured Loan from Director", "amount": 400000}
                    ]
                },
                "settings": {}
            }
        }
    }


class SuperToolResponse(BaseModel):
    """Response schema for the CA Super Tool API."""
    status: str
    result: Dict[str, Any]
    capsule: str


def extract_flags(output_data: Dict[str, Any]) -> list:
    """
    Safely extract flags from output_data, checking multiple locations.
    
    Args:
        output_data: Engine output data (may be fractal structure)
        
    Returns:
        List of flags (empty list if none found)
    """
    flags = (
        output_data.get("flags", []) or
        output_data.get("micro", {}).get("flags", []) or
        output_data.get("meso", {}).get("flags", []) or
        output_data.get("macro", {}).get("flags", []) or
        []
    )
    return flags if isinstance(flags, list) else []


def normalize_result(output_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize engine output to consistent API schema.
    Extracts macro.summary as main result and preserves details.
    
    Args:
        output_data: Engine output (may be fractal structure or flat)
        
    Returns:
        Normalized result with summary and details
    """
    # Check if output_data is a fractal structure
    if isinstance(output_data, dict) and "macro" in output_data:
        macro = output_data.get("macro", {})
        summary = macro.get("summary", {}) if isinstance(macro, dict) else {}
        
        # If summary is empty, try to use the whole macro or output_data
        if not summary:
            summary = macro if isinstance(macro, dict) else output_data
        
        # Extract details (micro/meso/macro)
        details = {
            "micro": output_data.get("micro", {}),
            "meso": output_data.get("meso", {}),
            "macro": output_data.get("macro", {})
        }
        
        return {
            "summary": summary,
            "details": details
        }
    else:
        # Flat structure - use output_data as summary, no details
        return {
            "summary": output_data if isinstance(output_data, dict) else {},
            "details": {}
        }


def structured_response(result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap results with standard structure matching API schema.
    
    Args:
        result: The engine result (normalized with summary and details)
        metadata: Metadata including capsule, invariant status, etc.
        
    Returns:
        Structured response dictionary with result and metadata
    """
    return {
        "result": result,
        "metadata": metadata
    }


def stringify_keys(obj: Any) -> Any:
    """
    Recursively convert all dictionary keys to strings to ensure JSON serialization stability.
    This fixes TypeError when comparing bool and str during hashing.
    
    Args:
        obj: Object to canonicalize (dict, list, or primitive)
        
    Returns:
        Canonicalized object with all keys as strings
    """
    if isinstance(obj, dict):
        return {str(k): stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_keys(i) for i in obj]
    else:
        return obj


def compute_capsule(input_data: Dict[str, Any], output_data: Dict[str, Any], engine_version: str = "1.0.0") -> str:
    """
    Generate deterministic capsule hash using SHA256.
    
    Args:
        input_data: Input data dictionary
        output_data: Output data dictionary
        engine_version: Engine version string
        
    Returns:
        SHA256 hash string representing the capsule
    """
    # Canonicalize data before hashing to avoid TypeError
    canonical_input = stringify_keys(input_data)
    canonical_output = stringify_keys(output_data)
    
    capsule_data = {
        "engine_version": engine_version,
        "input_hash": hashlib.sha256(json.dumps(canonical_input, sort_keys=True).encode()).hexdigest(),
        "output_hash": hashlib.sha256(json.dumps(canonical_output, sort_keys=True).encode()).hexdigest()
    }
    capsule_str = json.dumps(capsule_data, sort_keys=True)
    return hashlib.sha256(capsule_str.encode()).hexdigest()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CA Super Tool API",
        "version": "1.0.0",
        "endpoint": "/api/ca_super_tool"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that verifies rulebook loading and shows all available sections."""
    try:
        from ca_super_tool.engine.rulebook_loader import get_rulebook, get_section
        rulebook = get_rulebook()
        
        if rulebook is None:
            return {
                "status": "unhealthy",
                "error": "Rulebook is None"
            }
        
        sections = rulebook.get("sections", {})
        if not isinstance(sections, dict):
            return {
                "status": "unhealthy",
                "error": "Sections is not a dict"
            }
        
        # Check for key sections required by engines
        key_sections_required = [
            "schedule_iii_engine",
            "gst_itc_engine",
            "tds_tcs_engine",
            "as_standards"
        ]
        
        key_sections_present = []
        key_sections_missing = []
        
        for section_name in key_sections_required:
            if section_name in sections:
                key_sections_present.append(section_name)
            else:
                key_sections_missing.append(section_name)
        
        # Check for additional important sections
        additional_sections = []
        for section_name in ["schedule_iii_engine", "gst_itc_engine", "tds_tcs_engine", 
                            "as_standards", "schedule3_engine"]:
            if section_name in sections and section_name not in key_sections_present:
                additional_sections.append(section_name)
        
        # Verify specific rulebook blocks are available
        rulebook_blocks = {
            "schedule3": bool(get_section("schedule_iii_engine")),
            "tds": bool(get_section("tds_tcs_engine")),
            "cashflow": bool(get_section("as_standards")),  # AS3 is in as_standards
            "gst": bool(get_section("gst_itc_engine")),
            "journaling": bool(get_section("tds_tcs_engine")),  # TDS journal rules
            "generic_expansion": True  # Always available via rulebook structure
        }
        
        # Check for specific sub-sections
        schedule3_section = get_section("schedule_iii_engine") or {}
        tds_section = get_section("tds_tcs_engine") or {}
        gst_section = get_section("gst_itc_engine") or {}
        as_standards = get_section("as_standards") or {}
        
        sub_sections_status = {
            "schedule3_mapping_rules": bool(schedule3_section.get("schedule_iii_mapping_rules")),
            "tds_sections": bool(tds_section.get("tds_sections")),
            "tds_journal_engine": bool(tds_section.get("tds_journal_engine")),
            "gst_journal_rules": bool(gst_section.get("gst_journal_entry_rules")),
            "as3_cashflow": bool(as_standards.get("AS3") if isinstance(as_standards, dict) else False)
        }
        
        all_key_sections_present = len(key_sections_missing) == 0
        
        return {
            "status": "healthy" if all_key_sections_present else "degraded",
            "rulebook_loaded": True,
            "sections_count": len(sections),
            "all_sections": list(sections.keys()),
            "key_sections": {
                "present": key_sections_present,
                "missing": key_sections_missing,
                "all_present": all_key_sections_present
            },
            "rulebook_blocks": rulebook_blocks,
            "sub_sections_status": sub_sections_status,
            "additional_sections": additional_sections
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.post("/api/ca_super_tool", response_model=SuperToolResponse)
async def ca_super_tool(request: SuperToolRequest):
    """
    Main API endpoint for the CA Super Tool.
    
    Implements the UARE core pipeline:
    normalize_input → fractal_expansion → invariants → dispatcher → structured_response
    
    Args:
        request: SuperToolRequest containing task, data, and settings
        
    Returns:
        SuperToolResponse with status, result, and capsule
    """
    try:
        logger.info(f"Processing task: {request.task}")
        
        # Step 1: Normalize input
        normalized = normalize_input(request.data)
        logger.info("Input normalized")
        
        # Step 2: Fractal expansion
        fractal = run_fractal_expansion(normalized)
        logger.info("Fractal expansion completed")
        
        # Step 3: Enforce invariants
        invariants_passed, invariant_report = enforce_invariants(fractal)
        logger.info(f"Invariants check: {'PASSED' if invariants_passed else 'WARNING'}")
        
        # Step 4: Dispatch to engine (pass fractal, engine will use fractal['micro'])
        output_data = dispatch(
            task=request.task,
            fractal=fractal,
            settings=request.settings or {}
        )
        
        # Step 5: Extract flags safely (for metadata)
        flags = extract_flags(output_data)
        
        # Step 6: Compute capsule (canonicalize before hashing)
        capsule = compute_capsule(
            input_data=request.data,
            output_data=output_data
        )
        
        # Step 8: Structure response - expose fractal structure at top level
        final_metadata = {
            "capsule": capsule,
            "invariants_passed": invariants_passed,
            "invariant_report": invariant_report
        }
        
        # Add flags to metadata if present
        if flags:
            final_metadata["flags"] = flags
        
        # Build result with micro/meso/macro exposed at top level
        final_result = {
            "micro": output_data.get("micro"),
            "meso": output_data.get("meso"),
            "macro": output_data.get("macro"),
            "summary": output_data.get("macro", {}).get("summary"),
            "reasoning_tree": output_data.get("macro", {}).get("reasoning_tree"),
            "metadata": final_metadata
        }
        
        # Add invariant warning if needed
        if not invariants_passed:
            final_result["metadata"]["invariant_warning"] = invariant_report
        
        return SuperToolResponse(
            status="success",
            result=final_result,
            capsule=capsule
        )
    
    except Exception as e:
        logger.error(f"Error processing task {request.task}: {str(e)}", exc_info=True)
        
        # Return error response with consistent schema
        error_result = {
            "summary": {
                "error": str(e),
                "error_type": type(e).__name__
            },
            "details": {}
        }
        
        error_output = {
            "error": str(e),
            "error_type": type(e).__name__
        }
        
        capsule = compute_capsule(
            input_data=request.data,
            output_data=error_output
        )
        
        final_metadata = {
            "capsule": capsule,
            "invariants_passed": False,
            "invariant_report": {
                "error": str(e),
                "error_type": type(e).__name__
            }
        }
        
        structured = structured_response(error_result, final_metadata)
        
        return SuperToolResponse(
            status="error",
            result=structured,
            capsule=capsule
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

