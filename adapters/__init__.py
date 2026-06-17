"""Producers that convert native context into the portable `ContextItem` contract.

Exactly two adapters:
  - `archolith`  (#1, read-only): the archolith-context `SessionBriefing` -> items.
                 Reference adapter; depends on the briefing TYPES, never on the
                 assembler working.
  - `proxy`      (#2, proxy-only): an inline proxy / gateway sitting at the model-API
                 boundary -> items. The decoupled, product path: needs no archolith.
"""
