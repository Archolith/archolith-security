"""Pure-core tests — provenance consumers (manifest/attribution, staleness, lineage,
grounding). No archolith dependency (CI-safe)."""
from core import (
    ContextItem, MemoryGrade, TrustTier, attribute, check_memory_write, check_staleness,
    derive_item, ground, guard_freshness, lineage, manifest, manifest_bytes,
)

U = TrustTier.UNTRUSTED_RETRIEVED_CODE
T = TrustTier.TRUSTED_USER_GOAL
TOOL = TrustTier.TOOL_EVIDENCE


def _items():
    return [ContextItem("add a feature", "user_message", "turn:1", T),
            ContextItem("export const useThings = () => api.get('/things');",
                        "repo_file", "x.ts", U)]


# --- manifest / attribution ---
def test_manifest_is_pointers_not_content():
    # The manifest stores fingerprints, not content -> its size is independent of how
    # big the content is (same ref, 1-char vs 100k-char content => identical manifest).
    small = [ContextItem("x", "repo_file", "a.ts", U)]
    big = [ContextItem("x" * 100_000, "repo_file", "a.ts", U)]
    assert manifest_bytes(small) == manifest_bytes(big)
    assert all("content" not in rec for rec in manifest(small))


def test_attribution_traces_output_to_untrusted_source():
    items = _items()
    out = "export const useThings = () => api.get('/things');\n// mine"
    rows = attribute(out, items)
    assert any(a.tier == "untrusted_retrieved_code" for a in rows)


# --- staleness / freshness guard ---
def test_staleness_flags_changed_source():
    a = ContextItem("v1", "repo_file", "a.ts", U)
    live = {"a.ts": "v2 changed"}
    res = check_staleness([a], lambda it: live.get(it.source_ref))
    assert res[0].status == "stale"


def test_freshness_guard_drops_stale():
    a = ContextItem("v1", "repo_file", "a.ts", U)
    b = ContextItem("keep", "repo_file", "b.ts", U)
    live = {"a.ts": "changed", "b.ts": "keep"}
    kept, report = guard_freshness([a, b], lambda it: live.get(it.source_ref))
    assert report.kept == 1 and "a.ts" in report.dropped


# --- lineage + memory firewall ---
def test_lineage_untrusted_derived_cannot_instruct_or_persist():
    src = ContextItem("p", "repo_file", "x.ts", U)
    f = derive_item(src, "s", "fact:1")
    lg = lineage(f, {src.source_ref: src, f.source_ref: f})
    assert not lg.may_instruct and not lg.may_persist_to_memory
    assert "x.ts" in lg.chain


def test_memory_firewall_blocks_untrusted_instruction():
    src = ContextItem("p", "repo_file", "x.ts", U)
    f = derive_item(src, "s", "fact:1")
    assert not check_memory_write(f, MemoryGrade.INSTRUCTION).allowed


def test_memory_firewall_allows_tool_evidence():
    tool = ContextItem("ok", "tool_result", "run:1", TOOL)
    assert check_memory_write(tool, MemoryGrade.EVIDENCE).allowed
    assert not check_memory_write(tool, MemoryGrade.INSTRUCTION).allowed


# --- grounding ---
def test_grounding_flags_ungrounded_lines():
    src = ContextItem("export const useThings = () => api.get('/things');",
                      "repo_file", "x.ts", U)
    out = ("export const useThings = () => api.get('/things');\n"
           "// I invented this line with no source")
    rows = ground(out, [src])
    assert rows[0].ref == "x.ts" and rows[1].ref is None
