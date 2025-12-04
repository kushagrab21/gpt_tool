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

from engine.dispatcher import dispatch
from engine.normalize import normalize_input
from engine.fractal import run_fractal_expansion
from engine.invariants import enforce_invariants

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


def structured_response(result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap results with standard structure.
    
    Args:
        result: The engine result
        metadata: Metadata including capsule, invariant status, etc.
        
    Returns:
        Structured response dictionary
    """
    return {
        "result": result,
        "metadata": metadata,
        "engine_version": "1.0.0"
    }


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
    capsule_data = {
        "engine_version": engine_version,
        "input_hash": hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest(),
        "output_hash": hashlib.sha256(json.dumps(output_data, sort_keys=True).encode()).hexdigest()
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
    """Health check endpoint that verifies rulebook loading."""
    try:
        from engine.rulebook_loader import get_rulebook
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
        
        # Check for key sections
        key_sections = []
        if "schedule_iii_engine" in sections:
            key_sections.append("schedule_iii_engine")
        if "gst_itc_engine" in sections:
            key_sections.append("gst_itc_engine")
        if "tds_tcs_engine" in sections:
            key_sections.append("tds_tcs_engine")
        
        return {
            "status": "healthy",
            "rulebook_loaded": True,
            "sections_count": len(sections),
            "key_sections": key_sections,
            "key_sections_present": len(key_sections) == 3
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
        result = dispatch(
            task=request.task,
            fractal=fractal,
            settings=request.settings or {}
        )
        
        # Step 5: Compute capsule
        capsule = compute_capsule(
            input_data=request.data,
            output_data=result
        )
        
        # Step 6: Structure response
        metadata = {
            "capsule": capsule,
            "invariants_passed": invariants_passed,
            "invariant_report": invariant_report,
            "fractal_structure": {
                "has_micro": "micro" in fractal,
                "has_meso": "meso" in fractal,
                "has_macro": "macro" in fractal
            }
        }
        
        structured = structured_response(result, metadata)
        
        # Add invariant warning if needed
        if not invariants_passed:
            structured["invariant_warning"] = invariant_report
        
        return SuperToolResponse(
            status="success",
            result=structured,
            capsule=capsule
        )
    
    except Exception as e:
        logger.error(f"Error processing task {request.task}: {str(e)}", exc_info=True)
        
        # Return error response
        error_result = {
            "error": str(e),
            "error_type": type(e).__name__
        }
        capsule = compute_capsule(
            input_data=request.data,
            output_data=error_result
        )
        
        return SuperToolResponse(
            status="error",
            result=error_result,
            capsule=capsule
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

