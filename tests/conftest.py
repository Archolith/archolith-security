"""pytest bootstrap. Adds the repo root to sys.path so `core`/`adapters` import.

The pure-core tests depend only on `core` and `adapters.proxy`/`adapters.channel`
(stdlib only), so they run anywhere — including CI with no archolith-context present.
Tests that need `archolith_proxy` import `sec_paths` and `pytest.importorskip` it, and
skip cleanly when it (and the bench tree) are absent.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:  # wire archolith_proxy + bench when present (local dev); harmless if absent
    import sec_paths  # noqa: F401
except Exception:
    pass
