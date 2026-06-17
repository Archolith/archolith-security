# RESULT — Defense arm: governed rendering on the S0/S1 corpus (OFFLINE)

Status: DONE (offline, zero API). Corpus: bulletproof-react. Runner: `sec_defense_arm.py`.
Reproduce:
```
export ARCHOLITH_CORPUS=.../forked/bulletproof-react/apps/react-vite/src
cd .../projects/archolith/archolith-security && python sec_defense_arm.py
```

## What this measures
S0/S1 measured the **attack arm**: archolith's assembler renders retrieved code in one
equal-trust pool, so `GOVERNED=0` across the whole grid (3,465 markers, 0 governed).
This is the **defense arm** on the same poisoned corpus, routed through the portable
core instead of the assembler:

```
poisoned SessionBriefing --(adapter #1, read-only)--> [ContextItem]
   --> govern(mode) --> sec_contract.score_exposure   (EXPOSURE / GOVERNED)
   --> policy.check(payload, use)                      (AUTHORIZATION BINDING)
```

No assembler is in the loop, so the defense is not hostage to the assembler working.

## Design choice (the thesis)
The defense does **not** try to keep poison out of the window — the Contextual-Integrity
impossibility limit says pure instruction/data separation cannot reliably do that. So we
render the **full** item set (worst case: no fill, no budget — every payload is exposed)
and measure whether the defense *governs* what gets in. EXPOSURE is therefore 100% by
construction; the question is governance and binding.

## Findings

| class   | dens | off (exp/gov) | annotate (exp/gov) | enforce (exp/gov) | authz-bound |
|---------|-----:|:-------------:|:------------------:|:-----------------:|:-----------:|
| content | 1-3  | 100% / **0%** | 100% / **100%**    | 100% / **100%**   | 3/3 … 9/9   |
| map     | 1-3  | 100% / **0%** | 100% / **100%**    | 100% / **100%**   | 3/3 … 9/9   |
| priming | 1-3  | 100% / **0%** | 100% / **100%**    | 100% / **100%**   | 3/3 … 9/9   |

- **`OFF` reproduces the attack-arm baseline:** `GOVERNED=0`. The core's off mode is a
  faithful equal-trust renderer, not a strawman — it matches what the assembler does.
- **`ANNOTATE` / `ENFORCE` govern the entire exposed surface:** 18/18 exposed payloads
  fenced (`GOVERNED` 0 -> 100%) across all classes and densities.
- **Authorization binding holds for every payload:** 54/54 act-gates DENIED — no
  untrusted-tier payload may `instruct_model`, `authorize_tool`, or
  `persist_as_instruction`. This is the part that matters past the impossibility limit:
  the payload is in the window but cannot *act*.

## Reading
- This is the offline, deterministic complement to S0/S1: S0/S1 quantified the *gap*
  (what reaches the window, ungoverned); the defense arm shows the portable core
  *closes the governance gap to zero* and binds authorization — on the same corpus,
  without the assembler.
- It does **not** show the model *obeys* or *ignores* the fenced/bound payload. That is
  the metered **S2** question: does governed + authorization-bound context actually
  reduce obedience / block the privileged action at matched task quality? S2 needs a
  model and credits; this arm is the zero-cost evidence that the mechanism is in place
  and measurable.

## Caveats
- Governance here = the deterministic fence + the policy gate. Its *behavioral* effect
  on a model is unmeasured until S2.
- One corpus, synthetic payloads; the binding policy (`CAP_TABLE`) is a fixed default,
  not yet stress-tested against adversarial tier-spoofing (a future attack-arm rung:
  can a payload forge a higher trust tier upstream of the adapter?).

## Next
- **S2 (metered):** obedience / privileged-action eval, governed vs ungoverned, lead
  with MAP in-degree inflation + CONTENT-front; measure the three gates as outcomes.
- **Tier-spoofing rung (offline):** attack the *provenance capture* itself — can an
  attacker make untrusted content arrive labeled as a higher tier? Tests the adapter
  boundary, not just the renderer.
