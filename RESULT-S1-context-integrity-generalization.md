# RESULT — archolith-security S1: offline generalization (placement x density x in-degree)

Status: DONE (offline, zero API). Corpus: bulletproof-react `react-vite/src`.
Runner: `sec_s1_generalization.py` (merged via PR #1). Reproduce:
```
export ARCHOLITH_CORPUS=.../projects/forked/bulletproof-react/apps/react-vite/src
cd .../projects/archolith/archolith-security && python sec_s1_generalization.py
```
Grid: 3 payload classes x {density 1,2,3,5} x {placement front,middle,back} x
{MAP in-degree 0,4,8,16,24} x 5 fill strategies x {budget 6000,3000,1500} = 693 cells,
3,465 injected markers. EXPOSURE/GOVERNED only — no model, no obedience (that is S2).

## Why S1
S0 established the baseline on one placement and flagged a caveat: fifo's 100%
exposure for CONTENT/PRIMING was partly a *front-placement* artifact. S1 widens the
grid — especially **placement** — to separate "position-driven" exposure from
"structure-driven" exposure, still at zero API cost, before the metered S2 obedience
experiment.

## Harness correction made before trusting these numbers
The MAP importer files (which exist only to give the shadow dependency in-degree)
previously echoed the shadow's marker in a comment. Combined with a substring-match
exposure contract, that would credit MAP exposure whenever an *importer* survived
assembly — not the shadow itself — overstating MAP reach in exactly S1's new
fifo/front/high-budget cells. Fixed: importers no longer carry the marker, so EXPOSURE
now measures the **shadow foundation** reaching the window. S0's topological
dose-response is unchanged by the fix (deg 0 = 0%, deg>=8 = 100%), confirming S0 was
already measuring the shadow.

## Findings

### 1. GOVERNED = 0 across the ENTIRE widened grid (the robust core)
3,465 injected markers, 1,253 exposed, **0 governed**. Across every class, density,
placement, in-degree, strategy, and budget, not one surviving payload is rendered
inside a provenance/untrusted boundary. The S0 core gap is not a one-placement
artifact — it is the assembler's structural default. This is the load-bearing motivation
for the deterministic governed-context defense (S2).

### 2. Placement asymmetry — the sharp new result
Mean exposure by class x placement:

| class    | front | middle | back |
|----------|------:|-------:|-----:|
| content  |  46%  |   6%   |  0%  |
| priming  |  20%  |   0%   |  0%  |
| map      |  67%  |  41%   | 35%  |

- **CONTENT and PRIMING are placement-DEPENDENT.** They are orphan leaves (no
  in-degree, not the scored exemplar): position is the only thing carrying them, so
  they survive mainly under fifo at the front and collapse to ~0% in the middle/back.
  S0's caveat is now a measured result: their exposure is largely a front-arrival
  effect, not an intrinsic property of the fill.
- **MAP is placement-RESISTANT.** The shadow stays exposed at 35-41% even when moved
  to the middle or back, because in-degree inflation lets the structure-aware fill
  pull it up *regardless of where it sits in the briefing*. **Structure beats
  position.** This is the dangerous class: an attacker who can make poison look
  load-bearing does not need to control its position in the retrieved set.

### 3. MAP in-degree dose-response holds across the wider grid
Mean exposure by planted in-degree (aggregated over all strategies/placements/budgets):

| in-degree | mean exposure |
|----------:|--------------:|
| 0         |       18%     |
| 4         |       38%     |
| 8         |       49%     |
| 16        |       68%     |
| 24        |       66%     |

Monotonic rise, plateauing ~67% by degree 16. (The aggregate floor of 18% at degree 0
is the fifo+front cells where even an orphan shadow rides arrival order; under the
structure-aware fills specifically, degree 0 is still fully resisted — the S0 step
function.) The dose-response is robust, not a single-budget artifact.

## Reading
- The honest threat ranking is now **placement-conditional**: at the front, CONTENT
  injection is the easiest hit; but the only *placement-independent* attack is **MAP
  in-degree inflation** — the one that exploits the structure-aware fill itself. That
  makes MAP the priority target for both the S2 obedience test and the defense.
- Nothing here shows the model OBEYS exposed poison; EXPOSURE is the carrier rate.
  Obedience + the governed-context defense's effect on it are the metered S2 question.

## Caveats
- One corpus, synthetic payloads, substring-match exposure — hypothesis-grade, same
  bar as the recall work. A 2nd corpus would test whether the placement asymmetry and
  the in-degree threshold generalize.
- GOVERNED=0 is true by construction today (no boundary exists); its value is as the
  pre-defense baseline S2 must move off zero.

## Next
- **S2 (metered, gated behind credits):** does the model obey exposed-but-ungoverned
  poison (lead with MAP in-degree inflation; CONTENT-front as the direct-injection
  control), and does deterministic governed context reduce obedience at matched task
  quality? This is the External Researcher Access headline experiment.
