"""Grounding — a provenance consumer. Which claims in an output are backed by a source?

For each distinctive line of an agent output, find the context item it came from and
attach that source_ref + trust tier as a citation. Lines with no source are flagged
ungrounded — the agent's own words (which may be correct synthesis, or a hallucination).
Offline, no model: a line-membership lookup over the items already captured.

Dual use, like attribution: it makes outputs citable ("per src/foo.ts"), and a claim
grounded ONLY in untrusted retrieved code is exactly what a reviewer wants flagged.
"""
from __future__ import annotations

from dataclasses import dataclass

from .context_item import ContextItem


@dataclass
class GroundedLine:
    line: str
    ref: str | None       # None => ungrounded (no source contains this line)
    tier: str | None


def ground(output: str, items: list[ContextItem], min_len: int = 20) -> list[GroundedLine]:
    """Cite each distinctive output line to the source item that contains it."""
    index = [({ln.strip() for ln in it.content.splitlines() if len(ln.strip()) > min_len},
              it) for it in items]
    out: list[GroundedLine] = []
    for raw in output.splitlines():
        s = raw.strip()
        if len(s) <= min_len:
            continue
        src = next((it for lines, it in index if s in lines), None)
        out.append(GroundedLine(s, src.source_ref if src else None,
                                src.trust_tier.value if src else None))
    return out


def grounding_summary(grounded: list[GroundedLine]) -> dict:
    total = len(grounded)
    ungrounded = sum(1 for g in grounded if g.ref is None)
    untrusted = sum(1 for g in grounded if g.tier == "untrusted_retrieved_code")
    return {"lines": total, "ungrounded": ungrounded, "untrusted_grounded": untrusted}


if __name__ == "__main__":
    from .context_item import ContextItem, TrustTier

    src = ContextItem("export const useThings = () => api.get('/things');",
                      "repo_file", "features/x/api/get-x.ts",
                      TrustTier.UNTRUSTED_RETRIEVED_CODE)
    output = ("export const useThings = () => api.get('/things');\n"
              "// I invented this line with no source")
    rows = ground(output, [src])
    for g in rows:
        tag = f"{g.ref} [{g.tier}]" if g.ref else "UNGROUNDED (agent's own)"
        print(f"  {tag}: {g.line[:48]}")
    print(" ", grounding_summary(rows))
    assert rows[0].ref == "features/x/api/get-x.ts" and rows[1].ref is None
    print("OK")
