# RESULT — Disclosure: influence integrity (commercial injection), OFFLINE

Status: DONE prototype (offline, model-independent). Code: `core/disclosure.py`, the
`Interest` dimension in `core/context_item.py`, `disclosure_demo.py`. Reproduce:
`python disclosure_demo.py`.

## The threat this addresses (a different axis from prompt injection)
A company pays to place its product in the agent's context, so when you ask for "an X"
the model surfaces it. It never gives an order and never needs to be trusted — so the
authorization-binding defense (fence + deny instruct/tool/persist) does **nothing**: the
harm rides the legitimate "evidence" channel we explicitly permit. This is *influence*
integrity, not *authority* integrity.

## Approach: transparency, not censorship
Add a provenance dimension orthogonal to trust — `Interest`
(`first_party` / `organic` / `vendor` / `sponsored`) — captured from the source CHANNEL,
not the content. Then attribute the entities in an output back to their sources and
**disclose** any whose only backing is a commercially-interested source. The model is not
blocked from mentioning it; the user is told who put it in front of them.

Trust and interest are independent: in the demo all web sources are `untrusted_retrieved_code`,
but their interest differs (organic vs sponsored vs vendor).

## Demo result
A user asks for a TypeScript HTTP client; context holds an organic doc (Axios), a
sponsored ad (TurboFetch/VendorCo), and a vendor doc (AcmeHTTP/AcmeCorp). The model's
answer mentions all three. Disclosure output:
```
[disclosure] this answer surfaced items from commercially-interested sources:
  - AcmeHTTP:  from vendor:acme   (vendor)     *** no organic source corroborates this
  - TurboFetch: from ad:vendorco  (sponsored)  *** no organic source corroborates this
```
- **Axios** (surfaced from an organic source) — not disclosed.
- **TurboFetch / AcmeHTTP** (commercial sources, no organic corroboration) — disclosed
  with the source named. A label, not a gag.
- **"TypeScript"** (a common term the *user* introduced, `first_party`) — correctly
  excluded; a term the user used themselves cannot be an injected entity.

## Honest limits (this is partly solvable, by design)
- **Channel-marked only.** It catches commercial influence whose source CHANNEL is marked
  vendor/sponsored. An unmarked native ad whose channel looks organic is invisible — you
  shrink the unmarked surface, you don't eliminate it.
- **Cheap entity extraction is noisy.** CamelCase/Capitalized matching produces false
  positives (the demo's "TypeScript" before the first-party filter). The `uncorroborated`
  severity and the first-party exclusion isolate the real signal; a production version
  wants better recommendation/entity detection or a stop-list.
- **Cannot police the host.** Influence injected by the model provider itself is out of
  scope — a layer running on the platform can't audit the platform. Scope = content
  injected into *context* (RAG, retrieval, tool results, docs), which is where third-party
  commercial injection lives.

## Why it matters
It shows the provenance substrate generalizes past prompt injection to a second, distinct
integrity problem with the SAME data and a different consumer: authorization binding for
*authority*, disclosure for *influence*. Two threat axes, one substrate.

## Next
- Capture `interest` from real channel signals (known ad/vendor domains, sponsored-result
  flags) in the proxy adapter (it already accepts an `interest` field per record).
- Over-representation / "pumping" detection: flag entities appearing across many
  low-relevance injected items relative to query relevance.
