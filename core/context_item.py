"""The portable context contract — the ONE abstraction archolith-security owns.

A `ContextItem` is a single sourced piece of context plus its trust tier and the
capabilities that tier grants. This is deliberately tiny and dependency-free: it
does NOT import archolith-context or any assembler. Producers (the archolith
adapter, the proxy adapter) convert their native context into a list of these; the
policy engine and the governed renderer consume them. The security layer therefore
needs only two things to exist — itemized context and a source per item — neither of
which depends on any assembler working.

Capabilities follow the 2026 "authorization binding" control: bind what context may
DO to where it CAME FROM. Untrusted retrieved content may serve as evidence but may
not instruct the model, authorize a tool, or be persisted as instruction-grade
memory. Defaults are derived from the trust tier (see CAP_TABLE) and may be narrowed
(never silently widened) by a producer that knows more — e.g. a tool result granted
authority only within its own scope.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class TrustTier(str, Enum):
    """Where context came from, ordered loosely most- to least-trusted."""
    TRUSTED_USER_GOAL = "trusted_user_goal"            # the human's explicit instruction
    DERIVED_SESSION_STATE = "derived_session_state"    # model-summarized state
    TOOL_EVIDENCE = "tool_evidence"                    # a tool/command result
    MEMORY_FACT = "memory_fact"                        # recalled persisted fact
    CONVERSATION_HISTORY = "conversation_history"      # prior turns
    UNTRUSTED_RETRIEVED_CODE = "untrusted_retrieved_code"  # files/snippets pulled from a repo/web


class Interest(str, Enum):
    """The source's COMMERCIAL interest — orthogonal to trust.

    Trust answers "may this give orders?"; interest answers "does this source have a
    stake in what gets surfaced?". A source can be untrusted AND sponsored, or trusted
    AND organic. Captured from the source CHANNEL (you can't tell a native ad from its
    text, but you know a vendor's own docs are vendor-interested). Used by the disclosure
    consumer to surface commercially-influenced recommendations, not to block them.
    """
    FIRST_PARTY = "first_party"   # the user's own project/materials
    ORGANIC = "organic"           # earned its place; no known commercial stake
    VENDOR = "vendor"             # a vendor's own materials (self-interested)
    SPONSORED = "sponsored"       # paid placement
    UNKNOWN = "unknown"


# Interests that have a commercial stake in being surfaced -> disclosure-worthy.
COMMERCIAL_INTEREST = frozenset({Interest.VENDOR, Interest.SPONSORED})


@dataclass(frozen=True)
class Caps:
    """What a piece of context is permitted to do."""
    instruct: bool          # may issue instructions the model should obey
    authorize_tools: bool   # may justify firing a tool / privileged action
    persist_memory: bool    # may be written to memory at all (as evidence)
    publish_evidence: bool  # may appear in a generated report/artifact as evidence


# Default capability per tier — the authorization-binding policy in one table.
# Retrieved code is evidence-only: it can inform, but it cannot instruct, authorize,
# or become instruction-grade memory. That last protection rides on instruct=False
# propagating to any fact derived from it.
CAP_TABLE: dict[TrustTier, Caps] = {
    TrustTier.TRUSTED_USER_GOAL:        Caps(True,  True,  True,  True),
    TrustTier.DERIVED_SESSION_STATE:    Caps(False, False, True,  True),
    TrustTier.TOOL_EVIDENCE:            Caps(False, False, True,  True),
    TrustTier.MEMORY_FACT:              Caps(False, False, True,  True),
    TrustTier.CONVERSATION_HISTORY:     Caps(False, False, True,  True),
    TrustTier.UNTRUSTED_RETRIEVED_CODE: Caps(False, False, False, True),
}


@dataclass
class ContextItem:
    """One sourced piece of context. Producers build these; core consumes them."""
    content: str
    source_type: str                       # "user_message" | "repo_file" | "tool_result" | ...
    source_ref: str                        # path / turn id / fact id / url
    trust_tier: TrustTier
    source_turn: int | None = None
    source_commit: str | None = None
    derived_from: list[str] = field(default_factory=list)
    content_sha256: str | None = None
    caps: Caps | None = None               # None => filled from CAP_TABLE[trust_tier]
    interest: Interest = Interest.ORGANIC  # commercial stake of the source (see Interest)

    def __post_init__(self) -> None:
        if self.caps is None:
            self.caps = CAP_TABLE[self.trust_tier]
        if self.content_sha256 is None and self.content:
            object.__setattr__  # noqa: B018 (kept for clarity; dataclass is mutable)
            self.content_sha256 = hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    @property
    def is_untrusted(self) -> bool:
        """True when this item may not instruct — the renderer must fence it."""
        return not self.caps.instruct  # type: ignore[union-attr]


def derive_item(parent: ContextItem, content: str, source_ref: str,
                source_type: str = "derived") -> ContextItem:
    """Create an item derived from another, inheriting the LOWEST trust.

    A model summary of retrieved code cannot exceed the trust of the code. Capability
    flags are intersected, never widened.
    """
    p = parent.caps  # type: ignore[union-attr]
    return ContextItem(
        content=content, source_type=source_type, source_ref=source_ref,
        trust_tier=parent.trust_tier, derived_from=[parent.source_ref],
        caps=Caps(False, False, p.persist_memory, p.publish_evidence),
    )


if __name__ == "__main__":
    a = ContextItem("export const api = ...", "repo_file", "lib/api.ts",
                    TrustTier.UNTRUSTED_RETRIEVED_CODE)
    g = ContextItem("add a notifications feature", "user_message", "turn:5",
                    TrustTier.TRUSTED_USER_GOAL)
    print("retrieved code  is_untrusted:", a.is_untrusted, "caps:", a.caps)
    print("user goal       is_untrusted:", g.is_untrusted, "caps:", g.caps)
    print("sha present:", bool(a.content_sha256))
    assert a.is_untrusted and not g.is_untrusted
    assert not a.caps.instruct and not a.caps.persist_memory  # type: ignore[union-attr]
    print("OK")
