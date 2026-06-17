"""Staleness — a provenance consumer. Has captured context drifted from its source?

Each `ContextItem` carries `content_sha256` (and optionally `source_commit`) from when
it was captured. To check staleness, re-fingerprint the live source and compare. No
content is stored to do this — just the hash that's already on the item. This is the
generalized version of the map-drift freshness question: flag context that changed
under you instead of silently trusting a stale window.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable

from .context_item import ContextItem


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Staleness:
    ref: str
    status: str   # "fresh" | "stale" | "missing" | "n/a"


def check_staleness(
    items: list[ContextItem],
    live_content: Callable[[ContextItem], str | None],
) -> list[Staleness]:
    """Compare each item's captured hash against its live source.

    `live_content(item)` returns the source's CURRENT content, or `None` if the source
    is gone (deleted) or not resolvable (e.g. a derived pool — reported "n/a").
    """
    out: list[Staleness] = []
    for it in items:
        if it.content_sha256 is None:
            out.append(Staleness(it.source_ref, "n/a"))
            continue
        cur = live_content(it)
        if cur is None:
            out.append(Staleness(it.source_ref, "missing"))
        elif sha256(cur) == it.content_sha256:
            out.append(Staleness(it.source_ref, "fresh"))
        else:
            out.append(Staleness(it.source_ref, "stale"))
    return out


def stale_refs(staleness: list[Staleness]) -> list[str]:
    return [s.ref for s in staleness if s.status in ("stale", "missing")]


if __name__ == "__main__":
    from .context_item import ContextItem, TrustTier

    a = ContextItem("export const x = 1;", "repo_file", "a.ts",
                    TrustTier.UNTRUSTED_RETRIEVED_CODE)
    b = ContextItem("export const y = 2;", "repo_file", "b.ts",
                    TrustTier.UNTRUSTED_RETRIEVED_CODE)
    live = {"a.ts": "export const x = 1;", "b.ts": "export const y = 999;  // changed"}
    res = check_staleness([a, b], lambda it: live.get(it.source_ref))
    for s in res:
        print(f"  {s.ref}: {s.status}")
    assert [s.status for s in res] == ["fresh", "stale"]
    print("OK")
