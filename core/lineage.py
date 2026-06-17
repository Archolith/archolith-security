"""Lineage — a provenance consumer. What is a stored fact's pedigree?

When the system derives a fact from context (a summary, an extracted memory), the
derived item carries `derived_from` (the parent refs) and, via `derive_item`, inherits
the LOWEST trust of its sources. Lineage walks that chain so you can answer, before
acting on or persisting a fact: where did it ultimately come from, and what is it
allowed to do?

This is both memory hygiene (know a fact's origin/quality) and the deferred-poisoning
defense: a fact derived from untrusted code can never instruct and — because untrusted
retrieved code has `persist_memory=False` — cannot even be stored as memory. The write
is blocked at the boundary, not discovered later.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .context_item import ContextItem


@dataclass
class Lineage:
    ref: str
    chain: list[str] = field(default_factory=list)   # ref -> ... -> root sources
    effective_tier: str = ""
    may_instruct: bool = False
    may_persist_to_memory: bool = False
    may_publish_as_evidence: bool = True


def lineage(item: ContextItem, index: dict[str, ContextItem]) -> Lineage:
    """Reconstruct an item's provenance chain from `derived_from` via a {ref: item} index.

    The item's own caps already reflect the intersected (lowest) trust of its sources
    (see `derive_item`), so the effective permissions are read directly off the item;
    the chain is reconstructed for display/audit.
    """
    chain = [item.source_ref]
    seen = {item.source_ref}
    frontier = list(item.derived_from or [])
    while frontier:
        ref = frontier.pop(0)
        if ref in seen:
            continue
        seen.add(ref)
        chain.append(ref)
        parent = index.get(ref)
        if parent and parent.derived_from:
            frontier.extend(parent.derived_from)
    caps = item.caps
    return Lineage(
        ref=item.source_ref, chain=chain, effective_tier=item.trust_tier.value,
        may_instruct=caps.instruct, may_persist_to_memory=caps.persist_memory,
        may_publish_as_evidence=caps.publish_evidence)


if __name__ == "__main__":
    from .context_item import ContextItem, TrustTier, derive_item

    untrusted = ContextItem("api pattern...", "repo_file", "features/x/api/get-x.ts",
                            TrustTier.UNTRUSTED_RETRIEVED_CODE)
    tool = ContextItem("build passed", "tool_result", "run:1", TrustTier.TOOL_EVIDENCE)
    fact_from_code = derive_item(untrusted, "the app fetches via api-client", "fact:1")
    fact_from_tool = derive_item(tool, "the build is green", "fact:2")
    index = {it.source_ref: it for it in (untrusted, tool, fact_from_code, fact_from_tool)}

    for f in (fact_from_code, fact_from_tool):
        lg = lineage(f, index)
        print(f"  {lg.ref}: chain={lg.chain} tier={lg.effective_tier} "
              f"instruct={lg.may_instruct} persist={lg.may_persist_to_memory}")
    # A fact derived from untrusted code can neither instruct nor be stored as memory.
    lg_code = lineage(fact_from_code, index)
    assert not lg_code.may_instruct and not lg_code.may_persist_to_memory
    # A fact derived from a tool result may persist (as evidence) but not instruct.
    lg_tool = lineage(fact_from_tool, index)
    assert lg_tool.may_persist_to_memory and not lg_tool.may_instruct
    print("OK")
