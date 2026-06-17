"""Adapter #1 (read-only): archolith-context SessionBriefing -> [ContextItem].

Reference adapter. It reads the archolith `SessionBriefing` typed pools and maps each
to a trust tier; it does NOT call the deterministic assembler and does NOT depend on
that assembler producing good (or any) output. If archolith-context's assembler is
broken, this adapter still works — it only needs the briefing's items + their pool of
origin, which the prepper produces upstream of assembly.

This is the bridge that lets the existing S0/S1 corpus (built as a SessionBriefing) be
governed by the portable core, and lets us measure archolith's own rendering against
the same GOVERNED metric for comparison.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Repo root on path so `core` and `sec_paths` import regardless of entrypoint.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
import sec_paths  # noqa: E402,F401  -> archolith-context on path

from archolith_proxy.curator.briefing import PreFetchedFile, SessionBriefing  # noqa: E402

from core.context_item import ContextItem, TrustTier  # noqa: E402

# SessionBriefing pool -> trust tier. Files are untrusted retrieved code; the small
# typed pools are derived state / facts; the goal is the trusted instruction.
_POOL_TIERS: dict[str, TrustTier] = {
    "session_goal": TrustTier.TRUSTED_USER_GOAL,
    "checkpoint_text": TrustTier.DERIVED_SESSION_STATE,
    "open_issues_text": TrustTier.DERIVED_SESSION_STATE,
    "last_verification_text": TrustTier.TOOL_EVIDENCE,
    "decisions_text": TrustTier.DERIVED_SESSION_STATE,
    "facts_text": TrustTier.MEMORY_FACT,
}


def _file_content(f: PreFetchedFile) -> str:
    if f.sections:
        return "\n".join(s[2] for s in f.sections)
    return f.outline or ""


def from_session_briefing(briefing: SessionBriefing) -> list[ContextItem]:
    """Convert a SessionBriefing into portable ContextItems (read-only)."""
    items: list[ContextItem] = []

    for attr, tier in _POOL_TIERS.items():
        text = getattr(briefing, attr, "") or ""
        if text.strip():
            items.append(ContextItem(
                content=text, source_type=f"briefing.{attr}", source_ref=attr,
                trust_tier=tier, source_turn=briefing.source_turn))

    for f in briefing.files:
        content = _file_content(f)
        if content.strip():
            items.append(ContextItem(
                content=content, source_type="repo_file", source_ref=f.path,
                trust_tier=TrustTier.UNTRUSTED_RETRIEVED_CODE,
                source_turn=briefing.source_turn))

    return items


if __name__ == "__main__":
    # Self-check needs the bpr corpus; degrade gracefully if absent.
    sys.path.insert(0, str(_ROOT.parent / "archolith-bench" / "experiments"
                           / "context-quality" / "rung3" / "corpus2-bpr"))
    try:
        from bpr_corpus import build_briefing
    except Exception as exc:  # noqa: BLE001
        print(f"(skipped live check: {exc})")
        raise SystemExit(0)

    b = build_briefing()
    items = from_session_briefing(b)
    untrusted = sum(1 for i in items if i.is_untrusted)
    print(f"briefing -> {len(items)} context items ({untrusted} untrusted retrieved code)")
    if items:
        print("OK" if untrusted else "WARN: no untrusted items (corpus set?)")
