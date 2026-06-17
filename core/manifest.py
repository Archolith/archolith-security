"""Provenance manifest + attribution — a second consumer of the provenance graph.

Light BY CONSTRUCTION: a manifest stores POINTERS + FINGERPRINTS (source_ref, a short
content hash, tier, turn/commit, derived_from), never the content itself. The content
already lives where it came from; the manifest is a thin index over it. A full turn's
provenance is therefore a few KB, not a second copy of the context window.

`attribute(output, items)` answers "what is this output made of, and where did each
part come from?" with cheap line-overlap — no model, no token-level influence tracing,
no stored window. It is the offline, model-independent "figure out what's from where".
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .context_item import ContextItem


def manifest(items: list[ContextItem]) -> list[dict]:
    """A compact per-item provenance record. No content — pointers + fingerprint only."""
    return [{
        "ref": it.source_ref,
        "type": it.source_type,
        "tier": it.trust_tier.value,
        "sha": (it.content_sha256 or "")[:12],
        "turn": it.source_turn,
        "commit": it.source_commit,
        "derived_from": it.derived_from or None,
    } for it in items]


def manifest_bytes(items: list[ContextItem]) -> int:
    """Serialized size of the manifest — the actual storage cost per turn."""
    return len(json.dumps(manifest(items), separators=(",", ":")).encode("utf-8"))


def _distinctive_lines(text: str) -> set[str]:
    # Lines long enough to be a real shared signal (skip braces, imports of noise).
    return {ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20}


@dataclass
class Attribution:
    ref: str
    tier: str
    shared: int          # distinctive lines this source shares with the output
    share: float         # fraction of the output's distinctive lines from this source


def attribute(output: str, items: list[ContextItem], min_shared: int = 1) -> list[Attribution]:
    """Trace an output back to the context items it drew from, by line overlap.

    Cheap and deterministic: which sources' distinctive lines appear in the output.
    Returns sources ranked by overlap, each carrying its provenance (incl. trust tier),
    so you can see e.g. that an output drew from an UNTRUSTED file (contamination) vs.
    the trusted goal.
    """
    out = _distinctive_lines(output)
    denom = max(1, len(out))
    res: list[Attribution] = []
    for it in items:
        shared = len(_distinctive_lines(it.content) & out)
        if shared >= min_shared:
            res.append(Attribution(it.source_ref, it.trust_tier.value, shared,
                                   round(shared / denom, 3)))
    res.sort(key=lambda a: -a.shared)
    return res


if __name__ == "__main__":
    from .context_item import ContextItem, TrustTier

    goal = ContextItem("Add a notifications feature that lists notifications",
                       "user_message", "turn:5", TrustTier.TRUSTED_USER_GOAL)
    src = ContextItem("export const useNotifications = () =>\n"
                      "  useQuery(queryOptions({ queryKey: ['notifications'] }));",
                      "repo_file", "features/x/api/get-x.ts",
                      TrustTier.UNTRUSTED_RETRIEVED_CODE)
    items = [goal, src]

    output = ("export const useNotifications = () =>\n"
              "  useQuery(queryOptions({ queryKey: ['notifications'] }));\n"
              "// my new feature")
    print(f"manifest size for {len(items)} items: {manifest_bytes(items)} bytes "
          f"(content NOT stored)")
    for a in attribute(output, items):
        print(f"  output drew from {a.ref} [{a.tier}] — {a.shared} shared lines "
              f"({a.share:.0%})")
    assert any(a.tier == "untrusted_retrieved_code" for a in attribute(output, items))
    print("OK")
