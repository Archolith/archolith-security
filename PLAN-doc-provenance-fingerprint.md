# PLAN — Archolith document provenance fingerprint

Status: PROPOSED / ACTIONABLE
Scope: tamper-evident provenance for LLM-authored security docs, grant artifacts, and benchmark reports.

## Goal

Build a local, offline-first provenance layer for Archolith-authored Markdown documents.

The target claim is **not** "this text was definitely written by an LLM." The target claim is:

> This document, or these surviving chunks/claims, descend from an Archolith-generated artifact that was signed by a known key and tied to a specific repo/commit/harness context.

This is intentionally stronger and more useful than stylometric AI detection. It gives exact cryptographic proof when the document is unchanged and graded lineage evidence when the document is edited.

## Threat model

### In scope

- A user edits an Archolith-generated doc after signing.
- A third party removes the visible provenance block.
- A third party copies selected sections into a new document.
- A third party lightly paraphrases prose while preserving core claims.
- A reviewer wants to verify which claims and chunks still match the original signed artifact.
- A grant/credit reviewer wants evidence that results are tied to a concrete repo, commit, and harness.
- A document is laundered by removing the obvious provenance block but leaving subtle canary markers behind.

### Out of scope

- Proving that a generic document was written by an LLM.
- Preventing someone from fully rewriting a document by hand.
- Creating an invisible, unremovable watermark.
- Making adversarial payload text harder to remove from security fixtures.
- Framing an unauthored document as Archolith-authored.

The system should be honest: full rewrites can break soft fingerprints. Cryptography makes tampering detectable, not impossible.

## Design: layered provenance

### Layer 0 — canonicalization

Create a deterministic Markdown canonicalizer used by all later layers.

Rules for v0:

- normalize line endings to `\n`
- strip trailing whitespace
- collapse 3+ blank lines to 2
- remove the embedded `ARCHOLITH-PROVENANCE` block before hashing
- preserve heading text, list text, tables, and code blocks exactly except whitespace normalization
- write canonical bytes as UTF-8

Acceptance:

- same doc with CRLF vs LF verifies to the same canonical hash
- same doc with extra trailing spaces verifies to the same canonical hash
- changed prose produces a different canonical hash

### Layer 1 — exact signed manifest

Generate a manifest containing the exact canonical document hash and signing context.

Required fields:

```json
{
  "schema": "archolith-doc-provenance-v0",
  "doc_id": "s1-context-integrity-proposal",
  "created_at": "2026-06-17T00:00:00Z",
  "source_repo": "ctharvey/archolith-security",
  "source_commit": "<git sha>",
  "pipeline": "archolith-security",
  "canonical_sha256": "<hex>",
  "chunk_merkle_root": "<hex>",
  "claim_hashes": ["<hex>"],
  "soft_fingerprint_profile": "archolith-fp-v0",
  "external_watermarks": [],
  "canary_markers": [],
  "signature_alg": "ed25519",
  "signature": "<base64>"
}
```

Implementation notes:

- Sign the manifest bytes **excluding** the `signature` field.
- Use stable JSON serialization: sorted keys, compact separators.
- Support embedded Markdown comment and sidecar `.archolith-provenance.json`.
- Prefer sidecar for public grants and embedded comment for internal review docs.

Acceptance:

- `verify` reports `signature: valid` for an untouched signed doc.
- `verify` reports `canonical_hash: valid` for an untouched signed doc.
- changing one word makes `canonical_hash: mismatch` while `signature` still verifies the embedded/sidecar manifest.

### Layer 2 — chunk Merkle tree

Split the canonical Markdown into logical chunks and hash each chunk.

Chunking rules for v0:

- each heading starts a new chunk
- each paragraph under that heading is a child chunk
- each list item is a chunk
- each table row is a chunk
- each fenced code block is a chunk
- chunk identity is `heading_path + ordinal + normalized_text`

Compute:

- `chunk_hash = sha256(schema || heading_path || ordinal || normalized_text)`
- `chunk_merkle_root = merkle_root(sorted(chunk_hashes))`

Acceptance:

- editing one section changes that section's chunk hash but preserves unrelated chunk matches.
- `verify` reports chunk match count and changed heading paths.
- copied sections can still be recognized as descendants if the verifier has the original sidecar/manifest.

### Layer 3 — signed claim hashes

Extract a small set of explicit claims from the document and hash them independently.

For v0, claims are manually marked to avoid fragile automatic extraction:

```md
<!-- ARCHOLITH-CLAIM: S0 found GOVERNED=0 across the full deterministic grid. -->
```

The verifier canonicalizes claim text and compares claim hashes.

Acceptance:

- moving a claim does not break the claim hash.
- editing surrounding prose does not break the claim hash.
- changing the claim text causes a claim mismatch.
- `verify` reports `claim_match: n/m`.

### Layer 4 — keyed soft fingerprint

Use a secret key to generate a document-specific structural fingerprint profile.

Examples of profile choices:

- heading vocabulary family: `Purpose / Method / Findings / Honest caveats / Next`
- required phrase family: `EXPOSURE != attack success`
- metric style: uppercase `EXPOSURE` and `GOVERNED`
- table ordering: `degree | exposure | governed`
- caveat placement: after findings, before next steps
- numbered vs named findings
- stable anchor IDs or hidden HTML anchors

This is a secondary signal only. It is useful because someone can copy the visible pattern from one doc, but cannot predict the next document's expected keyed pattern without the key.

Acceptance:

- verifier produces `soft_fingerprint: strong | moderate | weak | absent`.
- verifier never treats soft fingerprint alone as cryptographic proof.
- the report clearly labels this as lineage evidence, not authorship proof.

### Layer 5 — decoy / honey-provenance canary

Add an optional defensive decoy layer: harmless, document-specific canary markers that make provenance stripping easier to detect.

This is the "decoy" idea, but it should be framed as a canary rather than a trap.

Allowed canary types:

- deterministic but innocuous HTML anchors, e.g. `<!-- archolith-canary: c17 -->`
- stable section anchor IDs, e.g. `{#a17-method-gap}` where the site renderer allows it
- harmless zero-risk phrasing variants selected from the keyed profile
- non-semantic table-column ordering choices
- claim IDs that do not affect meaning, e.g. `claim:s0-map-dose-response`

Disallowed canary types:

- invisible Unicode tricks that may corrupt text or accessibility
- fake citations
- fake author names
- false legal/provenance statements
- hidden hostile instructions
- anything that tries to frame a document not generated by Archolith

Verifier behavior:

- if the signed manifest was stripped but canaries remain, report: `manifest_absent_canary_present`.
- if canaries are missing but signature/sidecar verifies, report: `canary_removed_but_manifest_valid`.
- if canaries appear without a valid signature/sidecar, report: `canary_only_untrusted`.

Acceptance:

- removing the obvious provenance block while leaving canaries produces a useful warning.
- copying a paragraph with a canary into another doc can be detected as a possible descendant.
- canaries never count as cryptographic proof without the signed manifest or trusted sidecar.

### Layer 6 — optional external watermark adapters

Google/SynthID-style watermarking can be added as an adapter layer, not a dependency.

Reasoning:

- generation-time text watermarking can provide a useful additional signal
- it is model/provider-specific
- it may not survive heavy edits
- it does not replace signed provenance

Adapter interface:

```json
{
  "provider": "google-synthid-text",
  "mode": "generation-time-watermark",
  "available": false,
  "score": null,
  "verifier": null,
  "notes": "optional external signal; not required for local verification"
}
```

Implementation plan:

- v0: reserve `external_watermarks` field in the manifest.
- v1: add `--external-watermark google-synthid` metadata capture if generation path exposes it.
- v1: add verifier hook that can call a local/provider verifier if available.
- never block local verification on external watermark availability.

Acceptance:

- docs signed without external watermark still verify.
- external watermark result is reported as `supplemental`.
- absence of an external watermark never invalidates an Archolith signature.

## CLI proposal

Target file: `sec_doc_provenance.py`

Commands:

```bash
python sec_doc_provenance.py init-key --out .archolith/provenance-key.json
python sec_doc_provenance.py sign docs/S1-proposal.md \
  --doc-id s1-proposal \
  --source-repo ctharvey/archolith-security \
  --source-commit 907a166d \
  --embed

python sec_doc_provenance.py verify docs/S1-proposal.md
python sec_doc_provenance.py verify docs/S1-proposal.md --sidecar docs/S1-proposal.archolith-provenance.json
python sec_doc_provenance.py inspect docs/S1-proposal.md
```

Expected verify output:

```text
ARCHOLITH DOC PROVENANCE
manifest: present
signature: valid
canonical_hash: valid
chunk_merkle_root: valid
chunk_match: 23/23
claim_match: 5/5
soft_fingerprint: strong
canary_status: present_and_consistent
external_watermarks: none
result: authentic exact Archolith document
```

Edited document output:

```text
ARCHOLITH DOC PROVENANCE
manifest: present
signature: valid
canonical_hash: mismatch
chunk_merkle_root: mismatch
chunk_match: 19/23
claim_match: 5/5
soft_fingerprint: moderate
canary_status: partially_present
external_watermarks: none
result: edited descendant of signed Archolith document
```

Stripped manifest output:

```text
ARCHOLITH DOC PROVENANCE
manifest: absent
signature: unavailable
canonical_hash: unavailable
chunk_match: unavailable without sidecar/original manifest
claim_match: unavailable without sidecar/original manifest
soft_fingerprint: weak
canary_status: manifest_absent_canary_present
result: possible stripped descendant; not cryptographic proof
```

## Implementation phases

### Phase A — local cryptographic core

Deliver `sec_doc_provenance.py` with:

- canonicalize
- sha256 canonical text
- chunk split
- chunk hash list
- merkle root
- manifest creation
- embedded manifest block
- sidecar output
- verify exact doc

Acceptance:

- no network calls
- deterministic output
- works on README and RESULT-S0 markdown files
- unit self-checks run with `python sec_doc_provenance.py self-test`

### Phase B — partial lineage

Add:

- chunk match report
- changed heading paths
- manually marked claim hashes
- verify against sidecar even when embedded block is absent

Acceptance:

- removing one section reports partial match, not total failure
- moving claims preserves claim hash
- sidecar can verify a copied/edited doc

### Phase C — keyed fingerprint and canaries

Add:

- keyed profile generation from `HMAC(secret, doc_id)`
- optional canary insertion
- canary verifier
- soft fingerprint score

Acceptance:

- same key + doc_id produces same canary/profile plan
- different doc_id produces different profile plan
- canary-only result is reported as untrusted unless paired with signed manifest/sidecar

### Phase D — external watermark adapter

Add placeholder support for provider watermarks:

- `external_watermarks[]` manifest field
- optional provider score import
- Google/SynthID-style adapter interface

Acceptance:

- adapter absence does not break verification
- external watermark is displayed as supplemental signal only

## Safety notes

This repo contains adversarial IPI fixtures. Do not let provenance tooling ingest, index, or rewrite `sec_payloads.py` into a normal context corpus. The provenance tool should operate on selected Markdown docs by explicit path only.

Do not use canaries to hide hostile instructions. Do not use provenance claims to imply legal authorship or model authorship beyond what the signature actually proves.

## Next concrete task

Implement Phase A in `sec_doc_provenance.py` and run it against:

- `README.md`
- `RESULT-S0-context-integrity-surface.md`

Then commit the generated sidecars under a `provenance/` directory only if they do not contain private signing keys.

Never commit the private Ed25519 signing key.
