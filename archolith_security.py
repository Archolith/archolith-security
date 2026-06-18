"""archolith-security — sidecar public API.

The single import surface for archolith products. Install the sidecar
(`pip install -e path/to/archolith-security`) and use it natively:

    from archolith_security import (
        ContextItem, TrustTier, Interest,        # the provenance model
        govern, GovernMode, check, IntendedUse,  # authority: render + gate
        check_tool_call, ToolCall,               # authority: tool boundary
        check_memory_write, MemoryGrade,         # authority: memory boundary
        assess_influence,                        # influence: disclosure + pumping
        guard_freshness, attribute, lineage, ground,  # observability
    )

Producers (build ContextItems from your context) live in `adapters`:
    from adapters.proxy import from_sources, from_messages   # any pipeline / gateway
    from adapters.archolith import from_session_briefing     # archolith-context briefing

This module re-exports the whole `core` public API; `core` is dependency-free
(standard library only), so the sidecar adds no third-party dependencies.
"""
from core import *  # noqa: F401,F403
from core import __all__ as _core_all

__all__ = list(_core_all)
