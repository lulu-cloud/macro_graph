"""Deterministic market and macro analytics."""

from .metrics import aligned_correlation, summarize_market, summarize_rate
from .regime import classify

__all__ = ["aligned_correlation", "classify", "summarize_market", "summarize_rate"]
