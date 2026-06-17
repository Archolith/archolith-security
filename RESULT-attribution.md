# RESULT — Attribution: a second consumer of the provenance graph (OFFLINE)

Status: DONE (offline, zero API, model-independent). Code: `core/manifest.py`,
`attribution_demo.py`. Reproduce: `python attribution_demo.py`.

## Why
The provenance graph (every `ContextItem` tagged with origin + lineage) has been used
only as a security gate. "What's from where" is useful on its own — for attribution,
staleness, memory lineage, grounding. This is the first non-security consumer, and a
test of the standing worry that provenance is data-heavy.

## It is NOT data-heavy (measured)
Provenance stores **pointers + fingerprints, not content**: per item ~160 bytes
(`source_ref`, short hash, tier, turn/commit, `derived_from`). The content already
lives where it came from; the manifest is a thin index over it.

| window | content | manifest | overhead |
|--------|--------:|---------:|---------:|
| bpr, 36 items | 45,312 chars | 5,860 bytes | 12.9% |

The per-item cost is **fixed (~160 bytes), independent of file size** — so 12.9% is the
*worst case* (bpr's files are tiny). On a real codebase with multi-KB files the overhead
is **sub-1%**. A full turn's provenance is a few KB; a long session is a few MB of
manifests, with content never duplicated.

## Attribution works (offline, no model)
`attribute(output, items)` traces an agent output back to the context items it drew
from, by cheap distinctive-line overlap (no token-level influence tracing). On a
synthetic output it correctly identified the specific source files it borrowed from,
each carrying its trust tier:
```
<- features/comments/api/create-comment.ts   [untrusted_retrieved_code] 4 lines (67%)
<- features/discussions/api/create-discussion.ts [untrusted_retrieved_code] 4 lines (67%)
...  12 of 12 contributing sources are UNTRUSTED retrieved code
```

## Why it matters
- **"Why did the agent do that?"** becomes answerable: trace an output to the sources
  that produced it — observability every agent run needs, not just ones under attack.
- **It doubles as a contamination detector:** an output drawing heavily from an
  *untrusted* source is exactly the signal a security reviewer wants surfaced — so the
  same lightweight mechanism serves both observability and security.
- It confirms the reframe: provenance is the substrate; security is one consumer,
  attribution is another, and both run on data already captured, at KB scale.

## Next (other latent consumers, same captured data)
- **Staleness:** `source_commit`/`turn` flag context that changed since capture.
- **Memory lineage:** `derived_from` carries a stored fact's pedigree (trust + origin).
- **Grounding:** cite the `source_ref` behind a claim in generated output/reports.
