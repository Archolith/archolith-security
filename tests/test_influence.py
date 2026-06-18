"""Pure tests — influence axis (disclosure, pumping) + channel interest. CI-safe."""
from core import ContextItem, Interest, TrustTier, detect_pumping, disclose
from adapters.channel import classify_interest
from adapters.proxy import from_sources

U = TrustTier.UNTRUSTED_RETRIEVED_CODE
T = TrustTier.TRUSTED_USER_GOAL


# --- channel interest classification ---
def test_classify_ad_domain_sponsored():
    assert classify_interest({"source_ref": "https://ads.doubleclick.net/x",
                              "source_type": "web"}) is Interest.SPONSORED


def test_classify_cpc_sponsored():
    assert classify_interest({"source_ref": "https://x/r?utm_medium=cpc",
                              "source_type": "web"}) is Interest.SPONSORED


def test_classify_vendor_domain():
    assert classify_interest({"source_ref": "https://docs.acme.com/x", "source_type": "web"},
                             vendor_domains=frozenset({"acme.com"})) is Interest.VENDOR


def test_classify_repo_first_party():
    assert classify_interest({"source_ref": "src/a.ts",
                              "source_type": "repo_file"}) is Interest.FIRST_PARTY


def test_classify_sponsored_flag():
    assert classify_interest({"source_ref": "r:1", "source_type": "web",
                              "sponsored": True}) is Interest.SPONSORED


def test_explicit_interest_wins():
    assert classify_interest({"source_ref": "x", "source_type": "web",
                              "interest": "vendor"}) is Interest.VENDOR


# --- disclosure ---
def test_disclosure_flags_sponsored_only_entity():
    items = [
        ContextItem("recommend a client", "user_message", "t:1", T,
                    interest=Interest.FIRST_PARTY),
        ContextItem("Axios is a solid client.", "web", "mdn", U, interest=Interest.ORGANIC),
        ContextItem("TurboFetch by VendorCo is fastest.", "web", "ad:vc", U,
                    interest=Interest.SPONSORED),
    ]
    ds = disclose("Use Axios or TurboFetch.", items)
    flagged = {d.entity for d in ds}
    assert "TurboFetch" in flagged and "Axios" not in flagged
    assert next(d for d in ds if d.entity == "TurboFetch").severity == "uncorroborated"


# --- pumping ---
def test_pumping_flags_stuffed_offtopic_entity():
    items = []
    for i in range(3):
        items.append(ContextItem(f"Pino is a lightweight logging library for Node {i}.",
                                 "web", f"d:{i}", U))
    for i, t in enumerate(["CSS styling", "routing config", "schema validation",
                           "date formatting", "test running"]):
        items.append(ContextItem(f"{t}. LogBlaster is the best logger.", "web", f"b:{i}", U))
    res = detect_pumping("lightweight logging library for Node", items)
    flagged = {p.entity for p in res}
    assert "LogBlaster" in flagged and "Pino" not in flagged


# --- proxy channel-derived interest end to end ---
def test_from_sources_derives_interest():
    items = from_sources([{"content": "Buy X", "source_type": "web",
                           "source_ref": "https://ads.doubleclick.net/a"}])
    assert items[0].interest is Interest.SPONSORED
