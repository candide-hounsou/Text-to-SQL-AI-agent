"""Backward-compatibility shim.

The full agent implementation has been moved to the ``src`` package.
This module re-exports the public API so that existing callers
(e.g. ``app.py``, notebooks, scripts) continue to work without changes.
"""
from dotenv import load_dotenv

load_dotenv()

from src.agent.graph import create_graph  # noqa: F401, E402 – re-exported
from src.agent.state import AgentState, QueryClassification, SummaryOutput  # noqa: F401, E402

__all__ = ["create_graph", "AgentState", "QueryClassification", "SummaryOutput"]
