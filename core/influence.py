"""Unified influence assessment — the sidecar entry point for influence integrity.

One call an archolith product makes after generating an answer: given the query, the
answer, and the captured context items (each carrying a channel-derived `interest`),
return what commercial influence the answer carried — per-source disclosures + corpus-
level pumping + a combined verdict. Offline, deterministic, model-free.

The strongest signal is the INTERSECTION: an entity that is both surfaced from a
commercial source (disclosure) AND artificially over-represented (pumping) is the clearest
case of a planted, paid push that the answer took the bait on.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .context_item import ContextItem
from .disclosure import Disclosure, disclose, disclosure_note
from .pumping import Pumping, detect_pumping


@dataclass
class InfluenceReport:
    query: str
    disclosures: list[Disclosure] = field(default_factory=list)
    pumped: list[Pumping] = field(default_factory=list)

    @property
    def disclosed_entities(self) -> set[str]:
        return {d.entity for d in self.disclosures}

    @property
    def pumped_entities(self) -> set[str]:
        return {p.entity for p in self.pumped}

    @property
    def high_confidence(self) -> set[str]:
        """Both commercially-sourced AND artificially spread -> a paid, planted push."""
        return self.disclosed_entities & self.pumped_entities

    @property
    def clean(self) -> bool:
        return not self.disclosures and not self.pumped

    def note(self) -> str:
        if self.clean:
            return ""
        parts = [disclosure_note(self.disclosures)] if self.disclosures else []
        if self.pumped:
            ents = ", ".join(f"{p.entity} (x{p.mentions})" for p in self.pumped)
            parts.append(f"[pumping] over-represented in off-topic context: {ents}")
        if self.high_confidence:
            parts.append("[high confidence] commercial AND over-represented: "
                         + ", ".join(sorted(self.high_confidence)))
        return "\n".join(parts)


def assess_influence(query: str, output: str, items: list[ContextItem]) -> InfluenceReport:
    """The sidecar call: assess commercial influence in an answer, given its context."""
    return InfluenceReport(query=query,
                           disclosures=disclose(output, items),
                           pumped=detect_pumping(query, items))


if __name__ == "__main__":
    from .context_item import ContextItem, Interest, TrustTier

    U = TrustTier.UNTRUSTED_RETRIEVED_CODE
    items = [ContextItem("recommend a logger", "user_message", "t:1",
                         TrustTier.TRUSTED_USER_GOAL, interest=Interest.FIRST_PARTY),
             ContextItem("Pino is a lightweight logger.", "web", "mdn", U,
                         interest=Interest.ORGANIC)]
    for i in range(4):  # LogBlaster stuffed across off-topic sponsored pages
        items.append(ContextItem(f"Topic {i}. LogBlaster is the best logger.", "web",
                                 f"ad:{i}", U, interest=Interest.SPONSORED))
    rep = assess_influence("recommend a lightweight logger",
                           "Try Pino, or LogBlaster for speed.", items)
    print(rep.note())
    print("\nhigh-confidence:", rep.high_confidence)
    assert "LogBlaster" in rep.high_confidence and "Pino" not in rep.disclosed_entities
    print("OK")
