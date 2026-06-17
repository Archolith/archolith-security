"""Path bootstrap for the archolith-security harness.

archolith-security lives OUTSIDE the archolith-bench tree on purpose: its
adversarial IPI payload fixtures (`sec_payloads.py`) must never be swept into
corpus profiling or memory ingestion of the bench experiments. The benign pieces
it reuses — the shared path resolver (`paths.py`) and the bulletproof-react corpus
builder (`bpr_corpus.py`) — stay in the bench tree as the single source of truth;
this module locates them and puts them (and archolith-context) on `sys.path`.

Layout assumption: this package sits at `projects/archolith/archolith-security/`,
a sibling of `archolith-bench` and `archolith-context`. Override the bench location
with `ARCHOLITH_BENCH_RUNG3` if the harness is relocated.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # .../archolith-security
_ARCH = _HERE.parent                             # .../projects/archolith
_RUNG3 = Path(os.environ.get(
    "ARCHOLITH_BENCH_RUNG3",
    _ARCH / "archolith-bench" / "experiments" / "context-quality" / "rung3"))
_CORPUS2BPR = _RUNG3 / "corpus2-bpr"

for _p in (_HERE, _RUNG3, _CORPUS2BPR):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)

# paths.py (bench) resolves archolith-context relative to ITS OWN location, so this
# is correct regardless of who imports it.
from paths import context_root, corpus_root  # noqa: E402,F401

_CTX = str(context_root())
if _CTX not in sys.path:
    sys.path.insert(0, _CTX)
