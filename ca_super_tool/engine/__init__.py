"""
Engine module for CA Super Tool.
Contains all specialized engines and core processing modules.
"""

from ca_super_tool.engine.dispatcher import dispatch
from ca_super_tool.engine.normalize import normalize_input
from ca_super_tool.engine.fractal import run_fractal_expansion
from ca_super_tool.engine.invariants import enforce_invariants

__all__ = [
    "dispatch",
    "normalize_input",
    "run_fractal_expansion",
    "enforce_invariants"
]

