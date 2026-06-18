# archolith-security — Threat model

Status: v1 (2026-06-17). The contract a security project must state before it can be
evaluated: what we protect, against whom, under what assumptions, and explicitly what we
do NOT cover.

## 1. System model
archolith-security is a **provenance layer** that sits around an AI coding agent at four
boundaries:
- **Capture** — context arrives as sourced items (`adapters/`), each tagged with a trust
  tier and a commercial-interest label derived from its channel.
- **Emit** — context is rendered to the model with trust-tiered governance (`govern`).
- **Act/tool** — proposed tool calls are checked for data-flow violations (`toolcall`).
- **Memory** — writes are gated by provenance/lineage (`memory_firewall`).
It is a deterministic layer, not a model: no second LLM, no token overhead beyond a
KB-scale manifest. It runs *on top of* an agent; it does not replace model safety.

## 2. Assets to protect
- **Instruction integrity** — only the user's instructions steer the agent.
- **Data confidentiality** — secrets / sensitive data do not leak to external sinks.
- **Memory integrity** — persisted facts cannot silently become future instructions.
- **Output transparency** — what the answer surfaces is attributable; commercial
  influence is disclosed.

## 3. Adversary model
**Capabilities (what the attacker CAN do):**
- Plant content the agent will retrieve: repo files, code comments, READMEs, issues/PRs,
  web pages, tool results, prior-session memory.
- Craft that content to instruct, to carry secrets toward a sink, to masquerade as a
  high-trust source, or to push a product.
- Place commercial content on channels the agent reads.

**Limits (what the attacker CANNOT do, by assumption):**
- Control the user's **authenticated** input channel (the real user goal).
- Control or modify the **host model** or the proxy/runtime itself.
- Break cryptographic hashes or forge an authenticated transport label.

**Goals:** authority hijack (make the agent obey), data exfiltration, memory poisoning,
and influence (get a product/idea surfaced).

## 4. Trust assumptions
- The **capture boundary** correctly labels provenance from the *transport it observed*
  (not from attacker-supplied content). Tier-spoofing showed this is the single load-
  bearing assumption; the capture hardening (`authenticated_refs`, `trust_roles`,
  `goal_verbatim`) enforces it, regression-tested.
- The **host model and runtime are trusted** (out of scope to defend — a layer on the
  platform cannot police the platform).
- The user's **authenticated channel is trusted** (a compromised user is out of scope).

## 5. In-scope threats -> defense
| Threat | Defense | Evidence |
|--------|---------|----------|
| Instruction injection (authority) | trust-tiered govern + policy authorization binding | S0/S1, defense arm, S2 |
| Lethal trifecta (exfiltration) | tool-call data-flow enforcement | `toolcall`, lethal-trifecta demo |
| Memory poisoning (deferred) | memory write firewall (lineage-gated) | `memory_firewall` |
| Tier spoofing (capture forgery) | capture hardening, safe-by-default | tier-spoofing (0 bypasses), 10 tests |
| Navigation/exemplar/content injection | retrieval-poisoning surface | S0/S1 (MAP in-degree, etc.) |
| Commercial influence | interest labeling + disclosure + pumping | disclosure/pumping demos |
| Stale/drifted context | freshness guard | staleness + guard |

## 6. Out of scope / explicit non-goals
- **The host model.** Influence or injection performed by the model provider itself is
  not defendable from a layer running on it.
- **Unmarked native influence.** Disclosure is *channel-marked* — a commercial source
  whose channel looks organic is invisible. We shrink the unmarked surface, not erase it.
- **Transformed-data exfiltration.** Taint is first-order content overlap + secret
  patterns, NOT dynamic dataflow — data that is encoded/transformed before exfil can
  evade the tool-call check (CaMeL-style interpretation is more rigorous here; see
  PRIOR-ART).
- **A compromised user channel.** If the attacker owns the authenticated user input, the
  trust model's root is gone.
- **Model-level robustness.** We do not retrain the model; behavioral obedience reduction
  is conditional on the model/injection (S2 showed it is model- and corpus-dependent).
- **Multi-agent authority propagation.** Trust propagation across agent-to-agent handoffs
  is not yet modeled.

## 7. Security properties
- **Deterministic guarantees (offline, regression-tested):** trust-tiered governance and
  fencing; authorization-binding policy gates; tool-call data-flow blocking; memory-write
  gating; safe-by-default capture. These hold regardless of the model.
- **Conditional property:** *behavioral* reduction of model obedience to injection — real
  where the model is susceptible (S2: 58%->0% on one cell), absent where it is robust.
  Claimed as conditional, never as universal.

## 8. Residual risk
The defense is only as good as capture integrity (one boundary), the host/runtime trust,
and the first-order taint model. The honest posture: a deterministic, cheap, fail-safe
layer that closes the *attributable* attack surface and is explicit about the unattributable
remainder — not a claim to defeat all prompt injection.
