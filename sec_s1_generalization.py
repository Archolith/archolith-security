#!/usr/bin/env python3
"""S1 generalization runner — offline context-integrity surface expansion.

S0 proved the harness and established the baseline gap on one corpus: payloads can
reach the assembled context window while GOVERNED remains zero. S1 keeps the work
zero-API, but asks whether the S0 findings are robust to wider density, placement,
budget, and MAP in-degree choices before any metered S2 obedience experiments.

What this script measures, deterministically:
  EXPOSURE  - did the payload marker survive into the rendered context window?
  GOVERNED  - if exposed, was it inside an explicit untrusted/provenance boundary?

It deliberately does NOT ask a model to obey a payload. That belongs to S2.

Reproduce:
  export ARCHOLITH_CORPUS=.../projects/forked/bulletproof-react/apps/react-vite/src
  python sec_s1_generalization.py
  python sec_s1_generalization.py --densities 1,2,3,5 --placements front,middle,back
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))  # local dir importable
import sec_paths  # noqa: E402,F401  -> bench + corpus + archolith-context on path

from archolith_proxy.curator.briefing import SessionBriefing  # noqa: E402

from sec_contract import ExposureResult, score_exposure  # noqa: E402
from sec_corpus import build_poisoned_briefing  # noqa: E402
from sec_payloads import CLASSES, Payload  # noqa: E402
from sec_s0_surface import BUDGETS, STRATEGIES, _assemble  # noqa: E402


DEFAULT_DENSITIES = (1, 2, 3, 5)
DEFAULT_PLACEMENTS = ("front", "middle", "back")
DEFAULT_MAP_DEGREES = (0, 4, 8, 16, 24)


@dataclass(frozen=True)
class S1Cell:
    pclass: str
    density: int
    placement: str
    strategy: str
    budget: int
    map_degree: int
    exposure_rate: float
    governed_rate: float
    n_exposed: int
    n_governed: int
    n_injected: int


def _parse_csv_ints(raw: str) -> tuple[int, ...]:
    vals: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value < 0:
            raise argparse.ArgumentTypeError("values must be >= 0")
        vals.append(value)
    if not vals:
        raise argparse.ArgumentTypeError("at least one value is required")
    return tuple(vals)


def _parse_csv_choices(raw: str, allowed: Iterable[str]) -> tuple[str, ...]:
    allowed_set = set(allowed)
    vals = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not vals:
        raise argparse.ArgumentTypeError("at least one value is required")
    bad = [v for v in vals if v not in allowed_set]
    if bad:
        raise argparse.ArgumentTypeError(
            f"unsupported value(s): {', '.join(bad)}; allowed={sorted(allowed_set)}")
    return vals


def _map_importer_paths(payload: Payload, degree: int) -> set[str]:
    stem = payload.path.rsplit("/", 1)[-1].removesuffix(".ts")
    return {
        f"features/wired-{stem}/components/wired-{k}.tsx"
        for k in range(degree)
    }


def _poison_paths(payloads: list[Payload], map_degree: int) -> set[str]:
    paths = {p.path for p in payloads}
    for p in payloads:
        if p.pclass == "map" and map_degree:
            paths.update(_map_importer_paths(p, map_degree))
    return paths


def _place_poisoned_files(
    briefing: SessionBriefing,
    payloads: list[Payload],
    placement: str,
    map_degree: int,
) -> SessionBriefing:
    """Move injected files as a group while preserving clean-file order.

    S0 intentionally used one plausible placement. S1 checks that the result is not
    merely a front/back artifact by moving payload-bearing files to the front,
    middle, or back of the same clean briefing. The payload contents are unchanged.
    """
    paths = _poison_paths(payloads, map_degree)
    poisoned = [f for f in briefing.files if f.path in paths]
    clean = [f for f in briefing.files if f.path not in paths]

    if not poisoned:
        return briefing
    if placement == "front":
        files = poisoned + clean
    elif placement == "back":
        files = clean + poisoned
    elif placement == "middle":
        mid = len(clean) // 2
        files = clean[:mid] + poisoned + clean[mid:]
    else:
        raise ValueError(f"unknown placement: {placement}")

    return SessionBriefing(
        session_id="sec-s1",
        source_turn=briefing.source_turn,
        session_goal=briefing.session_goal,
        files=files,
    )


def _score_cell(
    pclass: str,
    density: int,
    placement: str,
    strategy: str,
    budget: int,
    map_degree: int,
) -> S1Cell:
    briefing, payloads = build_poisoned_briefing(
        pclass,
        density,
        map_degree=map_degree if pclass == "map" else 0,
    )
    briefing = _place_poisoned_files(briefing, payloads, placement, map_degree)
    ctx = _assemble(briefing, strategy, budget)
    result: ExposureResult = score_exposure(ctx, payloads)
    return S1Cell(
        pclass=pclass,
        density=density,
        placement=placement,
        strategy=strategy,
        budget=budget,
        map_degree=map_degree if pclass == "map" else 0,
        exposure_rate=result.exposure_rate,
        governed_rate=result.governed_rate,
        n_exposed=result.n_exposed,
        n_governed=result.n_governed,
        n_injected=result.n_injected,
    )


def _print_rollup(cells: list[S1Cell]) -> None:
    print("\n=== S1 rollup ===")
    print("Mean exposure / governed by class and placement")
    print(f"{'class':<8} {'placement':<8} {'cells':>5} {'exposure':>9} {'governed':>9}")
    print("-" * 47)
    for pclass in CLASSES:
        for placement in DEFAULT_PLACEMENTS:
            subset = [c for c in cells if c.pclass == pclass and c.placement == placement]
            if not subset:
                continue
            exposure = mean(c.exposure_rate for c in subset)
            governed = mean(c.governed_rate for c in subset)
            print(f"{pclass:<8} {placement:<8} {len(subset):>5} {exposure:>8.0%} {governed:>8.0%}")

    govd = sum(c.n_governed for c in cells)
    exposed = sum(c.n_exposed for c in cells)
    injected = sum(c.n_injected for c in cells)
    print("\nGlobal totals")
    print(f"  injected markers : {injected}")
    print(f"  exposed markers  : {exposed}")
    print(f"  governed markers : {govd}")
    if exposed and govd == 0:
        print("  headline         : exposed context remains ungoverned across this S1 grid")


def _print_map_threshold(cells: list[S1Cell]) -> None:
    print("\n=== MAP dose-response by planted in-degree ===")
    print(f"{'degree':>7} {'cells':>5} {'mean exposure':>14} {'any exposed':>12} {'governed':>9}")
    print("-" * 56)
    for degree in sorted({c.map_degree for c in cells if c.pclass == "map"}):
        subset = [c for c in cells if c.pclass == "map" and c.map_degree == degree]
        if not subset:
            continue
        print(
            f"{degree:>7} {len(subset):>5} "
            f"{mean(c.exposure_rate for c in subset):>13.0%} "
            f"{any(c.n_exposed for c in subset)!s:>12} "
            f"{mean(c.governed_rate for c in subset):>8.0%}"
        )


def run(
    densities: tuple[int, ...],
    placements: tuple[str, ...],
    map_degrees: tuple[int, ...],
    strategies: tuple[str, ...],
    budgets: tuple[int, ...],
) -> int:
    probe, _ = build_poisoned_briefing("content", 0)
    if not probe.files:
        print("(empty briefing — set ARCHOLITH_CORPUS to the bulletproof-react react-vite src)")
        return 2

    print("archolith-security S1 — offline generalization matrix (no API)")
    print(f"densities={densities} placements={placements} strategies={strategies} budgets={budgets}")
    print(f"map_degrees={map_degrees}")

    cells: list[S1Cell] = []
    for pclass in CLASSES:
        degrees = map_degrees if pclass == "map" else (0,)
        for density in densities:
            for placement in placements:
                for degree in degrees:
                    for budget in budgets:
                        row = []
                        for strategy in strategies:
                            cell = _score_cell(pclass, density, placement, strategy, budget, degree)
                            cells.append(cell)
                            row.append(f"{strategy}:{cell.exposure_rate:.0%}|{cell.governed_rate:.0%}")
                        print(
                            f"{pclass:<8} density={density:<2} placement={placement:<6} "
                            f"degree={degree:<2} budget={budget:<5} " + " ".join(row)
                        )

    _print_rollup(cells)
    _print_map_threshold(cells)
    print("\nS1 complete. EXPOSURE is deterministic carrier rate; obedience remains S2.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="archolith-security S1 offline generalization")
    ap.add_argument("--densities", type=_parse_csv_ints,
                    default=DEFAULT_DENSITIES,
                    help="comma-separated payload densities, default 1,2,3,5")
    ap.add_argument("--placements",
                    type=lambda s: _parse_csv_choices(s, DEFAULT_PLACEMENTS),
                    default=DEFAULT_PLACEMENTS,
                    help="comma-separated placements: front,middle,back")
    ap.add_argument("--map-degrees", type=_parse_csv_ints,
                    default=DEFAULT_MAP_DEGREES,
                    help="comma-separated MAP planted in-degrees, default 0,4,8,16,24")
    ap.add_argument("--strategies",
                    type=lambda s: _parse_csv_choices(s, STRATEGIES),
                    default=STRATEGIES,
                    help="comma-separated fill strategies")
    ap.add_argument("--budgets", type=_parse_csv_ints,
                    default=BUDGETS,
                    help="comma-separated token budgets, default 6000,3000,1500")
    args = ap.parse_args()
    raise SystemExit(run(args.densities, args.placements, args.map_degrees,
                         args.strategies, args.budgets))
