"""Single source of truth for pipeline sources (fetch, footer, news, RSS)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tier = Literal["primary", "secondary", "archived", "infra"]

# Custom fetchers own these; keep rss_url on SourceDef for fallback scripts only.
_HYBRID_RSS_OWNERS = frozenset({"adf", "csi", "ippforb"})

_FORB_REQUIRE_ANY = (
    "religion",
    "religious",
    "christian",
    "church",
    "blasphemy",
    "apostasy",
    "faith",
    "worship",
    "forb",
)

_UNSR_REQUIRE_ANY = (
    "religion",
    "belief",
    "forb",
    "christian",
    "church",
    "blasphemy",
    "apostasy",
    "religious",
    "special rapporteur",
)

# NEWS_SOURCES historically used short display names for a few orgs.
_NEWS_DISPLAY = {
    "csw": "CSW",
    "icc": "ICC",
    "osce": "OSCE / ODIHR",
    "gdelt": "GDELT",
}


@dataclass(frozen=True)
class SourceDef:
    key: str
    label: str
    title: str
    tier: Tier
    quality: str
    fetch_script: str | None
    status_name: str | None
    homepage: str | None
    rss_url: str | None
    high_trust: bool = False
    require_any: tuple[str, ...] | None = None
    news_source_id: str | None = None
    news_fetch_key: str | None = None
    about_description: str | None = None


SOURCES: list[SourceDef] = [
    SourceDef(
        key="uscirf",
        label="UC",
        title="USCIRF Annual Reports",
        tier="primary",
        quality="A",
        fetch_script="fetch_uscirf.py",
        status_name="uscirf",
        homepage="https://www.uscirf.gov/",
        rss_url=None,
        about_description="U.S. Commission on International Religious Freedom country reports",
    ),
    SourceDef(
        key="opendoors",
        label="OD",
        title="Open Doors World Watch List",
        tier="primary",
        quality="A",
        fetch_script="fetch_opendoors.py",
        status_name="opendoors",
        homepage="https://www.opendoors.org/en-US/persecution/countries/",
        rss_url=None,
        about_description="Annual ranking of countries where Christians face the most persecution",
    ),
    SourceDef(
        key="pew",
        label="Pew",
        title="Pew Research",
        tier="archived",
        quality="B",
        fetch_script=None,
        status_name=None,
        homepage="https://www.pewresearch.org/religion/",
        rss_url=None,
        about_description="Religious landscape and restriction studies",
    ),
    SourceDef(
        key="natural_earth",
        label="NE",
        title="Natural Earth map boundaries",
        tier="infra",
        quality="Infra",
        fetch_script=None,
        status_name="natural_earth_110m",
        homepage="https://www.naturalearthdata.com/",
        rss_url=None,
        about_description="Public domain map boundaries for the interactive map",
    ),
    SourceDef(
        key="freedomhouse",
        label="FH",
        title="Freedom House Freedom in the World",
        tier="primary",
        quality="B",
        fetch_script="fetch_freedom_house.py",
        status_name="freedomhouse",
        homepage="https://freedomhouse.org/report/freedom-world",
        rss_url=None,
        about_description="Political rights and civil liberties ratings",
    ),
    SourceDef(
        key="statedepartment",
        label="SD",
        title="U.S. State Dept IRF Reports",
        tier="primary",
        quality="A",
        fetch_script="fetch_state_dept.py",
        status_name="statedepartment",
        homepage="https://www.state.gov/international-religious-freedom-reports/",
        rss_url=None,
        about_description="International Religious Freedom country reports",
    ),
    SourceDef(
        key="ohchr",
        label="OHCHR",
        title="OHCHR Universal Human Rights Index",
        tier="secondary",
        quality="B",
        fetch_script="fetch_ohchr.py",
        status_name="ohchr",
        homepage="https://uhri.ohchr.org/",
        rss_url=None,
        about_description="UN human rights recommendations related to religion",
    ),
    SourceDef(
        key="vdem",
        label="VD",
        title="V-Dem FoRB Indicators",
        tier="archived",
        quality="A",
        fetch_script=None,
        status_name=None,
        homepage="https://www.v-dem.net/data/the-v-dem-dataset/",
        rss_url=None,
        about_description="FoRB indicators (CC BY-SA); country subset archived under data/archives/vdem/",
    ),
    SourceDef(
        key="gdelt",
        label="GDELT",
        title="GDELT Global Database of Events",
        tier="secondary",
        quality="C",
        fetch_script="fetch_gdelt.py",
        status_name="gdelt",
        homepage="https://www.gdeltproject.org/",
        rss_url=None,
        news_source_id="gdelt2025",
        about_description="Recent news events mentioning Christian persecution",
    ),
    SourceDef(
        key="owid",
        label="OWID",
        title="Our World in Data - Religious Composition",
        tier="primary",
        quality="B",
        fetch_script="fetch_owid.py",
        status_name="owid",
        homepage="https://ourworldindata.org/grapher/religious-composition",
        rss_url=None,
        about_description="Christian population share and counts (Pew-based)",
    ),
    SourceDef(
        key="acn",
        label="ACN",
        title="ACN Persecuted and Forgotten",
        tier="secondary",
        quality="A",
        fetch_script="fetch_acn.py",
        status_name="acn",
        homepage="https://acninternational.org/",
        rss_url=None,
        about_description="Religious freedom and Persecuted and Forgotten reporting",
    ),
    SourceDef(
        key="bbc",
        label="BBC",
        title="BBC News",
        tier="archived",
        quality="C",
        fetch_script=None,
        status_name=None,
        homepage="https://www.bbc.com/news",
        rss_url=None,
        about_description="Documented news reporting on persecution events",
    ),
    SourceDef(
        key="morningstarnews",
        label="MSN",
        title="Morning Star News",
        tier="secondary",
        quality="A",
        fetch_script="fetch_morningstarnews.py",
        status_name="morningstarnews",
        homepage="https://morningstarnews.org/",
        rss_url="https://morningstarnews.org/feed/",
        high_trust=True,
        news_source_id="morningstarnews2026",
        about_description="Incident reporting focused on Christian persecution",
    ),
    SourceDef(
        key="vid",
        label="VID",
        title="Violent Incidents Database",
        tier="secondary",
        quality="A",
        fetch_script="fetch_vid.py",
        status_name="vid",
        homepage="https://iirf.global/vid/",
        rss_url=None,
        about_description="Aggregated violence statistics against Christians",
    ),
    SourceDef(
        key="gcr",
        label="GCR",
        title="Global Christian Relief",
        tier="secondary",
        quality="B",
        fetch_script="fetch_gcr_stats.py",
        status_name="gcr",
        homepage="https://globalchristianrelief.org/",
        rss_url=None,
        about_description="Persecution statistics and advocacy reporting",
    ),
    SourceDef(
        key="csw",
        label="CSW",
        title="Christian Solidarity Worldwide",
        tier="secondary",
        quality="A",
        fetch_script="fetch_csw.py",
        status_name="csw",
        homepage="https://www.csw.org.uk/",
        rss_url=None,
        news_source_id="csw2026",
        about_description="Freedom of religion or belief advocacy and incident reports",
    ),
    SourceDef(
        key="icc",
        label="ICC",
        title="International Christian Concern",
        tier="secondary",
        quality="A",
        fetch_script="fetch_icc.py",
        status_name="icc",
        homepage="https://www.persecution.org/",
        rss_url=None,
        news_source_id="icc2026",
        about_description="Global persecution news and Global Persecution Index",
    ),
    SourceDef(
        key="forum18",
        label="F18",
        title="Forum 18",
        tier="secondary",
        quality="A",
        fetch_script="fetch_forum18.py",
        status_name="forum18",
        homepage="https://www.forum18.org/",
        rss_url="https://www.forum18.org/syndication/forum18.xml",
        high_trust=False,
        news_source_id="forum18",
        about_description="Freedom of religion or belief news, focused on former Soviet and related regions",
    ),
    SourceDef(
        key="mec",
        label="MEC",
        title="Middle East Concern",
        tier="secondary",
        quality="A",
        fetch_script="fetch_mec.py",
        status_name="mec",
        homepage="https://www.meconcern.org/",
        rss_url="https://www.meconcern.org/feed/",
        high_trust=True,
        news_source_id="mec",
        about_description="FoRB advocacy and incident reporting for the Middle East and North Africa",
    ),
    SourceDef(
        key="bitterwinter",
        label="BW",
        title="Bitter Winter",
        tier="secondary",
        quality="A",
        fetch_script="fetch_bitterwinter.py",
        status_name="bitterwinter",
        homepage="https://bitterwinter.org/",
        rss_url="https://bitterwinter.org/feed/",
        high_trust=False,
        news_source_id="bitterwinter",
        about_description="FoRB news with coverage of China and related repression",
    ),
    SourceDef(
        key="releaseintl",
        label="RI",
        title="Release International",
        tier="secondary",
        quality="A",
        fetch_script="fetch_releaseintl.py",
        status_name="releaseintl",
        homepage="https://www.releaseinternational.org/",
        rss_url="https://releaseinternational.org/feed/",
        high_trust=True,
        news_source_id="releaseintl",
        about_description="Advocacy and news for persecuted Christians worldwide",
    ),
    SourceDef(
        key="vom",
        label="VOM",
        title="Voice of the Martyrs",
        tier="secondary",
        quality="A",
        fetch_script="fetch_vom.py",
        status_name="vom",
        homepage="https://www.persecution.com/",
        rss_url="https://www.persecution.com/stories/feed/",
        high_trust=True,
        news_source_id="vom2026",
        about_description="Persecution news, prisoner alerts, and country stories",
    ),
    SourceDef(
        key="chinaaid",
        label="CA",
        title="ChinaAid",
        tier="secondary",
        quality="A",
        fetch_script="fetch_chinaaid.py",
        status_name="chinaaid",
        homepage="https://www.chinaaid.org/",
        rss_url="https://www.chinaaid.org/feeds/posts/default",
        high_trust=True,
        news_source_id="chinaaid",
        about_description="Christian persecution and FoRB monitoring focused on China",
    ),
    SourceDef(
        key="infochretienne",
        label="IC",
        title="Info Chrétienne",
        tier="secondary",
        quality="B",
        fetch_script="fetch_infochretienne.py",
        status_name="infochretienne",
        homepage="https://www.infochretienne.com/",
        rss_url="https://www.infochretienne.com/flux-rss.rss",
        high_trust=True,
        news_source_id="infochretienne",
        about_description="French Christian news covering FoRB / persecution incidents",
    ),
    SourceDef(
        key="osce",
        label="OSCE",
        title="OSCE / ODIHR FoRB",
        tier="secondary",
        quality="A",
        fetch_script="fetch_osce.py",
        status_name="osce",
        homepage="https://www.osce.org/odihr/freedom-of-religion-or-belief",
        rss_url=None,
        news_source_id="osce",
        about_description="Hate-crime and freedom of religion or belief monitoring in the OSCE region",
    ),
    SourceDef(
        key="unsrforb",
        label="SR",
        title="UN Special Rapporteur on FoRB",
        tier="secondary",
        quality="A",
        fetch_script="fetch_unsrforb.py",
        status_name="unsrforb",
        homepage="https://www.ohchr.org/en/special-procedures/sr-religion-or-belief",
        rss_url=None,  # HTML-only hub; do not advertise OHCHR site RSS
        high_trust=True,
        require_any=_UNSR_REQUIRE_ANY,
        news_source_id="unsrforb",
        about_description="UN Special Rapporteur country and thematic FoRB reporting (distinct from UHRI)",
    ),
    SourceDef(
        key="hrw",
        label="HRW",
        title="Human Rights Watch",
        tier="secondary",
        quality="A",
        fetch_script="fetch_hrw.py",
        status_name="hrw",
        homepage="https://www.hrw.org/",
        rss_url="https://www.hrw.org/rss",
        high_trust=True,
        require_any=_FORB_REQUIRE_ANY,
        news_source_id="hrw",
        about_description="Global human-rights reporting including FoRB (CC BY-NC-ND; link + short excerpt only)",
    ),
    SourceDef(
        key="amnesty",
        label="AI",
        title="Amnesty International",
        tier="secondary",
        quality="A",
        fetch_script="fetch_amnesty.py",
        status_name="amnesty",
        homepage="https://www.amnesty.org/",
        rss_url="https://www.amnesty.org/en/latest/rss/",
        high_trust=True,
        require_any=_FORB_REQUIRE_ANY,
        news_source_id="amnesty",
        about_description="Global human-rights research including FoRB (CC BY-NC-ND; link + short excerpt only)",
    ),
    SourceDef(
        key="barnabas",
        label="BA",
        title="Barnabas Aid",
        tier="secondary",
        quality="B",
        fetch_script="fetch_barnabas.py",
        status_name="barnabas",
        homepage="https://www.barnabasaid.org/",
        rss_url=None,
        news_source_id="barnabas",
        about_description="Persecuted-church news and aid reporting",
    ),
    SourceDef(
        key="csi",
        label="CSI",
        title="Christian Solidarity International",
        tier="secondary",
        quality="B",
        fetch_script="fetch_csi.py",
        status_name="csi",
        homepage="https://www.csi-int.org/",
        rss_url="https://csi-usa.org/feed/",
        high_trust=True,
        news_source_id="csi",
        about_description="FoRB campaigning and country reporting (distinct from CSW)",
    ),
    SourceDef(
        key="cna",
        label="CNA",
        title="Catholic News Agency",
        tier="secondary",
        quality="B",
        fetch_script="fetch_cna.py",
        status_name="cna",
        homepage="https://www.catholicnewsagency.com/",
        rss_url="https://www.catholicnewsagency.com/rss/news.xml",
        high_trust=False,
        news_source_id="cna",
        about_description="Catholic news wire including persecution reporting",
    ),
    SourceDef(
        key="fides",
        label="Fides",
        title="Agenzia Fides",
        tier="secondary",
        quality="A",
        fetch_script="fetch_fides.py",
        status_name="fides",
        homepage="https://www.fides.org/en",
        rss_url="https://www.fides.org/en/news/rss",
        high_trust=True,
        news_source_id="fides",
        about_description="Pontifical Mission Societies news; missionary-territory FoRB / persecution reporting",
    ),
    SourceDef(
        key="aciprensa",
        label="ACI",
        title="ACI Prensa",
        tier="secondary",
        quality="B",
        fetch_script="fetch_aciprensa.py",
        status_name="aciprensa",
        homepage="https://www.aciprensa.com/",
        rss_url="https://www.aciprensa.com/rss/news",
        high_trust=False,
        news_source_id="aciprensa",
        about_description="Spanish Catholic news wire including LatAm persecution reporting",
    ),
    SourceDef(
        key="hrwf",
        label="HRWF",
        title="Human Rights Without Frontiers",
        tier="secondary",
        quality="B",
        fetch_script="fetch_hrwf.py",
        status_name="hrwf",
        homepage="https://hrwf.eu/",
        rss_url="https://hrwf.eu/feed/",
        high_trust=True,
        news_source_id="hrwf",
        about_description="Brussels FoRB monitoring and newsletters",
    ),
    SourceDef(
        key="adf",
        label="ADF",
        title="ADF International",
        tier="secondary",
        quality="B",
        fetch_script="fetch_adf.py",
        status_name="adf",
        homepage="https://adfinternational.org/",
        rss_url="https://www.adfinternational.org/feed/",
        high_trust=True,
        news_source_id="adf",
        about_description="Legal FoRB advocacy and related reporting",
    ),
    SourceDef(
        key="wea",
        label="WEA",
        title="WEA Religious Liberty Commission",
        tier="secondary",
        quality="B",
        fetch_script="fetch_wea.py",
        status_name="wea",
        homepage="https://worldea.org/",
        rss_url="https://worldea.org/feed/",
        high_trust=True,
        news_source_id="wea",
        about_description="Global evangelical FoRB advocacy",
    ),
    SourceDef(
        key="jubilee",
        label="JC",
        title="Jubilee Campaign",
        tier="secondary",
        quality="C",
        fetch_script="fetch_jubilee.py",
        status_name="jubilee",
        homepage="https://jubileecampaign.org/",
        rss_url="https://jubileecampaign.org/feed/",
        high_trust=True,
        news_source_id="jubilee",
        about_description="UK/US FoRB advocacy reporting",
    ),
    SourceDef(
        key="ippforb",
        label="IPP",
        title="IPPFoRB",
        tier="secondary",
        quality="C",
        fetch_script="fetch_ippforb.py",
        status_name="ippforb",
        homepage="https://ippforb.com/",
        rss_url="https://ippforb.com/feed/",
        high_trust=True,
        news_source_id="ippforb",
        about_description="Parliamentarians' network for freedom of religion or belief",
    ),
]

# Preserve historical NEWS_SOURCES order (not SOURCES list order).
_NEWS_ORDER = (
    "morningstarnews",
    "csw",
    "icc",
    "forum18",
    "mec",
    "bitterwinter",
    "releaseintl",
    "vom",
    "chinaaid",
    "infochretienne",
    "osce",
    "unsrforb",
    "hrw",
    "amnesty",
    "barnabas",
    "csi",
    "cna",
    "fides",
    "aciprensa",
    "hrwf",
    "adf",
    "wea",
    "jubilee",
    "ippforb",
    "gdelt",
)

SOURCES_BY_KEY: dict[str, SourceDef] = {s.key: s for s in SOURCES}


def primary_keys() -> list[str]:
    return [s.key for s in SOURCES if s.tier == "primary"]


def secondary_keys() -> list[str]:
    return [s.key for s in SOURCES if s.tier == "secondary"]


def news_sources() -> list[tuple[str, str, str]]:
    """Return (fetch_key, display_label, source_id) matching collect_enrich NEWS_SOURCES."""
    out: list[tuple[str, str, str]] = []
    for key in _NEWS_ORDER:
        s = SOURCES_BY_KEY[key]
        if not s.news_source_id:
            continue
        fetch_key = s.news_fetch_key or s.key
        display = _NEWS_DISPLAY.get(s.key, s.title)
        out.append((fetch_key, display, s.news_source_id))
    return out


def indicator_org_ids() -> frozenset[str]:
    """Org-index / news homepage ids that belong in citation indicators."""
    return frozenset(s.news_source_id for s in SOURCES if s.news_source_id)


def rss_feeds() -> dict[str, dict]:
    """RSS_FEEDS shape for run_rss_fetcher (excludes hybrid-owned and HTML-only)."""
    out: dict[str, dict] = {}
    for s in SOURCES:
        if not s.rss_url or s.key in _HYBRID_RSS_OWNERS:
            continue
        entry: dict = {
            "source_label": s.title,
            "rss_url": s.rss_url,
            "high_trust": s.high_trust,
        }
        if s.require_any:
            entry["require_any"] = list(s.require_any)
        out[s.key] = entry
    return out


def footer_groups() -> dict[str, dict]:
    """SOURCE_GROUP_DEFS shape for footer chips."""
    out: dict[str, dict] = {}
    for s in SOURCES:
        prefixes = ("odwwl",) if s.key == "opendoors" else (s.key,)
        out[s.key] = {"prefixes": prefixes, "label": s.label, "title": s.title}
    return out


def status_key_map() -> dict[str, str | None]:
    """STATUS_KEY_MAP: footer group key → *_status.json name (or None)."""
    # Match historical map: every footer group except archived vdem (no status file).
    return {s.key: s.status_name for s in SOURCES if s.key != "vdem"}


def fetch_script_for(key: str) -> str | None:
    src = SOURCES_BY_KEY.get(key)
    return src.fetch_script if src else None
