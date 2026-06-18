# archolith-security — Prior art & positioning

Status: v1 (2026-06-17). Where this sits relative to the 2025-26 prompt-injection /
agent-security literature, honestly — including where others are stronger.

## One-line position
A **lightweight, deterministic provenance LAYER** for agent context — no second LLM, no
token overhead beyond a KB manifest — that does authorization binding for *authority*,
disclosure for *influence*, and boundary enforcement at the tool and memory edges. It
trades the formal dataflow rigor of heavier systems for being cheap, fail-safe, and
drop-in, and it adds an influence axis and observability that the authority-only defenses
omit.

## Closest comparison — CaMeL (Google DeepMind, 2025)
*"Defeating Prompt Injections by Design"* (arXiv 2503.18813). CaMeL attaches
**capabilities (metadata) to every value** and restricts data/control flows via
fine-grained policies, using a **dual-LLM** (privileged + quarantined) and a custom
interpreter that extracts control/data flow from the query. ~67% attack reduction
(often 0% on strong models), at **2.7-2.8x token cost**, and it **relies on
user-defined policies** (user-fatigue risk).

- **Shared idea:** capability/provenance metadata on values + policy-gated data flow.
  Our `Caps`/`ContextItem` + `policy.check` + `toolcall` taint check are the same family.
- **Where CaMeL is stronger:** a formal interpreter that tracks *transformed* data flow;
  ours is first-order content-overlap taint (see THREAT-MODEL non-goals).
- **Where we differ / add:** no second LLM and no interpreter -> deterministic, ~0 token
  overhead (KB manifest vs 2.7x); **default conservative policies** that fail safe
  instead of relying on the user; a second **influence** axis (disclosure/pumping) CaMeL
  does not address; and observability consumers (attribution/lineage/grounding/staleness).
- **Honest takeaway:** CaMeL is the SOTA "by design" authority defense and is more
  rigorous on dataflow; archolith-security is a lighter-weight point on the cost/rigor
  curve with broader scope. Complementary, not a claim to beat it.

## Detector defenses
- **PromptArmor** (ICLR 2026, arXiv 2507.15219) — an off-the-shelf LLM as a preprocessor
  that detects/strips injection; ~<1% FP/FN on AgentDojo. Strong, but **needs a model
  call per prompt** and is classification-based. Ours is deterministic and adds
  enforcement at tool/memory boundaries rather than input filtering. Composable: detect
  then govern.
- **Spotlighting / sandwiching / instructional defenses** — prompt-level delimiting of
  untrusted data. Our `govern(ANNOTATE)` fence is the same idea, but we *also* bind
  authorization (the Contextual-Integrity impossibility limit means delimiting alone is
  insufficient).

## Runtime / program-analysis defenses
- **AgentArmor** (arXiv 2508.01249) — program analysis over the agent runtime trace. The
  closest in spirit to our provenance graph; heavier (trace analysis) and authority-
  focused. Our manifest/lineage are a lighter trace-provenance substrate.
- **Tool-result parsing IPI defense** (arXiv 2601.04795) — sanitizes tool outputs. Adjacent
  to our capture-side untrusted tiering of tool results.

## Model-level
- **Meta SecAlign** (arXiv 2507.02735) — a foundation model trained to resist injection.
  Orthogonal: model robustness vs our system-layer provenance. Our S2 shows a robust
  model (gpt-4.1-mini) needs no layer; a susceptible one benefits — so the two compose.

## Benchmark
- **AgentDojo** (arXiv 2406.13352) — the standard dynamic eval (70 tools, 97 tasks, 27
  injection targets). **We have not run on it** (homemade S2 only). This is the Tier-C
  credibility gap: our tool-call defense should be measured here against adaptive attacks
  and reported next to PromptArmor/AgentArmor/CaMeL.

## Taxonomy / standards
- **OWASP Top 10 for Agentic Applications (Dec 2025)** — our threat list maps to it
  (memory poisoning, tool misuse, goal hijacking).
- **C2PA / content provenance** — media-authenticity provenance; a *different* provenance
  problem (proving document origin), which is why doc-watermarking (PR #2) was parked.

## Net assessment
archolith-security is not novel in the *core idea* (provenance/capabilities-gated flow —
CaMeL got there first and more rigorously). Its contribution is the **packaging**: a
cheap, deterministic, fail-safe, drop-in layer with **two integrity axes** (authority +
influence) and observability, on already-captured data. Its credibility now hinges on a
standard-benchmark number (AgentDojo) and the framing it now has (this doc + THREAT-MODEL).
