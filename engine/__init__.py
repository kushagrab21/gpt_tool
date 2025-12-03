"""
Engine module for CA Super Tool.
Contains all specialized engines and core processing modules.
"""

from engine.dispatcher import dispatch
from engine.normalize import normalize_input
from engine.fractal import run_fractal_expansion
from engine.invariants import enforce_invariants

__all__ = [
    "dispatch",
    "normalize_input",
    "run_fractal_expansion",
    "enforce_invariants"
]

