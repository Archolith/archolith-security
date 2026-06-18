"""archolith-security core — the portable, assembler-independent context contract.

Exposes the whole security surface: the context item + trust model, the
authorization-binding policy engine, and the governed renderer. None of it imports
any assembler; producers live in `adapters/`.
"""
from .context_item import (
    CAP_TABLE,
    COMMERCIAL_INTEREST,
    Caps,
    ContextItem,
    Interest,
    TrustTier,
    derive_item,
)
from .disclosure import Disclosure, disclose, disclosure_note, entities
from .govern import GovernMode, GovernResult, govern
from .memory_firewall import MemoryGrade, WriteDecision, check_memory_write
from .pumping import Pumping, detect_pumping
from .toolcall import ToolCall, ToolClass, ToolDecision, check_tool_call, classify_tool
from .grounding import GroundedLine, ground, grounding_summary
from .lineage import Lineage, lineage
from .manifest import Attribution, attribute, manifest, manifest_bytes
from .policy import Decision, IntendedUse, check, check_all, denials
from .staleness import (
    GuardReport,
    Staleness,
    check_staleness,
    guard_freshness,
    stale_refs,
)

__all__ = [
    "CAP_TABLE", "Caps", "ContextItem", "TrustTier", "derive_item",
    "Interest", "COMMERCIAL_INTEREST",
    "Disclosure", "disclose", "disclosure_note", "entities",
    "Pumping", "detect_pumping",
    "ToolCall", "ToolClass", "ToolDecision", "check_tool_call", "classify_tool",
    "MemoryGrade", "WriteDecision", "check_memory_write",
    "GovernMode", "GovernResult", "govern",
    "Decision", "IntendedUse", "check", "check_all", "denials",
    # provenance consumers
    "Attribution", "attribute", "manifest", "manifest_bytes",
    "Staleness", "check_staleness", "stale_refs", "guard_freshness", "GuardReport",
    "Lineage", "lineage",
    "GroundedLine", "ground", "grounding_summary",
]
