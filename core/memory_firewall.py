"""Memory write firewall — gate persistence by provenance/lineage (workstream #4).

`lineage` (read-side) reports a fact's pedigree; this is the WRITE boundary. A candidate
memory write is gated by the effective capabilities the fact inherited from its sources
(via `derive_item`, which intersects to the lowest trust):

  - INSTRUCTION-grade memory (a fact that may steer future agents) requires `may_instruct`.
    So a fact derived from untrusted content can NEVER become future instruction — the
    deferred memory-poisoning attack is blocked at the write, not discovered on read.
  - EVIDENCE-grade memory requires `may_persist_to_memory`. Untrusted retrieved code has
    `persist_memory=False`, so it cannot even be stored as evidence.

Thin by design: it composes the existing policy gate at the persistence boundary, and
reports the lineage chain so a blocked/downgraded write is auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .context_item import ContextItem
from .lineage import lineage
from .policy import IntendedUse, check


class MemoryGrade(str, Enum):
    INSTRUCTION = "instruction"   # may steer future agents
    EVIDENCE = "evidence"         # stored as evidence only


@dataclass
class WriteDecision:
    allowed: bool
    grade: str
    reason: str
    chain: list[str] = field(default_factory=list)
    downgrade_to: str | None = None   # suggested safe grade when instruction is denied


def check_memory_write(fact: ContextItem, grade: MemoryGrade,
                       index: dict[str, ContextItem] | None = None) -> WriteDecision:
    """Gate a memory write at the requested grade by the fact's effective caps."""
    use = (IntendedUse.PERSIST_AS_INSTRUCTION if grade is MemoryGrade.INSTRUCTION
           else IntendedUse.PERSIST_AS_EVIDENCE)
    d = check(fact, use)
    chain = lineage(fact, index or {fact.source_ref: fact}).chain
    downgrade = None
    if not d.allowed and grade is MemoryGrade.INSTRUCTION:
        # If it can't instruct, can it at least be kept as evidence?
        if check(fact, IntendedUse.PERSIST_AS_EVIDENCE).allowed:
            downgrade = MemoryGrade.EVIDENCE.value
    return WriteDecision(allowed=d.allowed, grade=grade.value, reason=d.reason,
                         chain=chain, downgrade_to=downgrade)


if __name__ == "__main__":
    from .context_item import ContextItem, TrustTier, derive_item

    untrusted = ContextItem("api pattern", "repo_file", "features/x/get-x.ts",
                            TrustTier.UNTRUSTED_RETRIEVED_CODE)
    tool = ContextItem("build passed", "tool_result", "run:1", TrustTier.TOOL_EVIDENCE)
    goal = ContextItem("user wants notifications", "user_message", "turn:1",
                       TrustTier.TRUSTED_USER_GOAL)

    fact_code = derive_item(untrusted, "the app fetches via api-client", "fact:1")
    idx = {it.source_ref: it for it in (untrusted, tool, goal, fact_code)}

    # Deferred poisoning: a fact from untrusted code must not become instruction memory.
    d1 = check_memory_write(fact_code, MemoryGrade.INSTRUCTION, idx)
    d1e = check_memory_write(fact_code, MemoryGrade.EVIDENCE, idx)
    print(f"  untrusted-derived -> instruction: allowed={d1.allowed} "
          f"(downgrade={d1.downgrade_to}); evidence: allowed={d1e.allowed}")
    # Tool result may persist as evidence, never as instruction.
    d2 = check_memory_write(tool, MemoryGrade.EVIDENCE, idx)
    d3 = check_memory_write(tool, MemoryGrade.INSTRUCTION, idx)
    print(f"  tool_evidence -> evidence: allowed={d2.allowed}; "
          f"instruction: allowed={d3.allowed}")
    # The user's own instruction may persist as instruction.
    d4 = check_memory_write(goal, MemoryGrade.INSTRUCTION, idx)
    print(f"  user goal -> instruction: allowed={d4.allowed}")

    assert not d1.allowed and not d1e.allowed   # untrusted code: blocked entirely
    assert d2.allowed and not d3.allowed         # tool: evidence yes, instruction no
    assert d4.allowed                            # user: instruction yes
    print("OK")
