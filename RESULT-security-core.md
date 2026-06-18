# RESULT — Security core: tool-call provenance + memory firewall (OFFLINE)

Status: DONE (offline, model-independent). Code: `core/toolcall.py`,
`core/memory_firewall.py`, `tests/test_security_core.py` (9 tests),
`lethal_trifecta_demo.py`. Closes roadmap workstreams **#6** and **#4**. Reproduce:
`python lethal_trifecta_demo.py` / `python tests/test_security_core.py`.

## Why this is the maturity jump
The earlier work labeled and fenced context but never enforced anything at the boundary
where harm happens. The credible threat models define attack success as *actual data
leakage*, not task hijack — so the security core has to act where data flows to tools and
to memory. This adds both enforcement points.

## Tool-call provenance enforcement (#6 — the lethal trifecta)
`check_tool_call(call, items, allowed_hosts=...)` blocks a proposed tool call on a
DATA-FLOW criterion:
- **(a) tainted data -> exfiltration sink.** A sink = an outbound tool to a non-allowlisted
  host. Tainted = data that shares a secret/identifier (long-token overlap) with an
  untrusted-origin context item, or matches a secret pattern (`sk-live`, `process.env`,
  `API_KEY`, AWS keys, private-key headers). Tainted-to-sink = BLOCK.
- **(b) authorized only by untrusted content.** If the call's justification is grounded
  only in untrusted items, the call is unauthorized (untrusted content may not authorize
  tools).
- Sinks to **allowlisted** hosts with untainted bodies, and local reads, are allowed.

Demo: posting a planted secret to an external host is blocked (tainted by
`features/x/api/get-x.ts`); the same tool to an allowlisted host with a clean body is
allowed.

## Memory write firewall (#4)
`check_memory_write(fact, grade)` gates persistence by the fact's inherited capabilities:
- **INSTRUCTION-grade** (a fact that may steer future agents) requires `may_instruct`. A
  fact derived from untrusted content can NEVER become instruction memory — deferred
  poisoning is blocked at the write, with the lineage chain reported for audit.
- **EVIDENCE-grade** requires `may_persist_to_memory`; untrusted retrieved code
  (`persist_memory=False`) is blocked from memory entirely.
- A user instruction may persist as instruction; a tool result may persist as evidence
  but not instruction.

## End-to-end (lethal_trifecta_demo)
A planted untrusted file carries a secret and an injected directive. Both attack steps
are blocked at their boundaries by provenance, no model involved:
```
[1] http_post secret -> external host : BLOCK (tainted -> exfil sink), tainted by get-x.ts
    http_post -> allowlisted host       : allow
[2] persist injected pattern as instruction memory : BLOCK
    lineage: ['fact:poison', 'features/x/api/get-x.ts']
```

## Tests
`tests/test_security_core.py` — 9 tests (tainted-to-sink, secret-to-sink, allowlisted-host,
local-read, untainted-external, untrusted-authorized; memory grades for untrusted/tool/
user). All pass; the 10 capture-integrity tests still pass.

## Honest limits
- Taint is content-overlap + secret-pattern, not true dynamic dataflow — it catches
  verbatim/identifier propagation, not data that is transformed/encoded before exfil.
- Tool classification is a name + URL-host heuristic; a real deploy supplies its tool
  registry and host allowlist.
- This is the deterministic enforcement layer; behavioral evaluation (does it hold up on
  AgentDojo against adaptive attacks?) is the Tier-C benchmark step, still owed.

## Next (maturity)
- **Tier C:** port the eval onto **AgentDojo** so the tool-call defense is measured
  against the standard benchmark and adaptive attacks (the credibility step).
- True dataflow taint (propagate taint through tool results, not just first-order overlap).
- Tier A framing docs (threat model + prior-art positioning) remain the cheapest
  credibility and are still owed before any filing.
