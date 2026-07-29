"""Shared Christian-persecution relevance filter for news/incident articles."""
from __future__ import annotations

import re

CHRISTIAN_MARKERS = (
    "christian",
    "christians",
    "christianity",
    "church",
    "churches",
    "pastor",
    "pastors",
    "priest",
    "priests",
    "bible",
    "bibles",
    "gospel",
    "jesus",
    "christ",
    "evangelical",
    "evangelicals",
    "catholic",
    "catholics",
    "protestant",
    "protestants",
    "orthodox",
    "congregation",
    "congregations",
    "missionary",
    "missionaries",
    "convert to christianity",
    "christian convert",
    "house church",
    "sunday service",
    "worship service",
    # French (Info Chrétienne and related)
    "chrétien",
    "chrétiens",
    "chrétienne",
    "chrétiennes",
    "christianisme",
    "église",
    "églises",
    "eglise",
    "eglises",
    "pasteur",
    "pasteurs",
    "prêtre",
    "prêtres",
    "catholique",
    "catholiques",
    "protestante",
    "protestantes",
    "évangélique",
    "évangéliques",
    "evangelique",
    "evangeliques",
    # Spanish (ACI Prensa and related)
    "cristiano",
    "cristianos",
    "cristiana",
    "cristianas",
    "cristianismo",
    "iglesia",
    "iglesias",
    "pastor",
    "pastores",
    "sacerdote",
    "sacerdotes",
    "católico",
    "católicos",
    "catolica",
    "catolicos",
    "protestante",
    "protestantes",
    "evangélico",
    "evangélicos",
    "evangelico",
    "evangelicos",
    "misionero",
    "misioneros",
    # Italian
    "cristiano",
    "cristiani",
    "cristiana",
    "cristiane",
    "cristianesimo",
    "chiesa",
    "chiese",
    "prete",
    "preti",
    "sacerdote",
    "sacerdoti",
    "cattolico",
    "cattolici",
    "cattolica",
    "cattoliche",
    "protestante",
    "protestanti",
    "evangelico",
    "evangelici",
    "missionario",
    "missionari",
    # Portuguese
    "cristão",
    "cristãos",
    "cristã",
    "cristãs",
    "cristao",
    "cristaos",
    "cristianismo",
    "igreja",
    "igrejas",
    "padre",
    "padres",
    "sacerdote",
    "sacerdotes",
    "católico",
    "católicos",
    "catolica",
    "catolicos",
    "protestante",
    "protestantes",
    "evangélico",
    "evangélicos",
    "missionário",
    "missionários",
    # German
    "christ",
    "christen",
    "christin",
    "christinnen",
    "christentum",
    "kirche",
    "kirchen",
    "pfarrer",
    "priester",
    "katholisch",
    "katholiken",
    "protestantisch",
    "evangelisch",
    "missionar",
    "missionare",
)

HARM_MARKERS = (
    "persecution",
    "persecuted",
    "persecute",
    "attack",
    "attacked",
    "attacks",
    "kill",
    "killed",
    "killing",
    "murder",
    "murdered",
    "martyr",
    "martyrdom",
    "arrest",
    "arrested",
    "detain",
    "detained",
    "detention",
    "imprison",
    "imprisoned",
    "prison",
    "sentence",
    "sentenced",
    "blasphemy",
    "apostasy",
    "forced conversion",
    "anti-conversion",
    "anticonversion",
    "religious minority",
    "religious minorities",
    "forb",
    "church closure",
    "church closed",
    "church demolition",
    "church demolished",
    "church attack",
    "church burned",
    "burned",
    "burnt",
    "destroyed",
    "vandalism",
    "vandalized",
    "kidnap",
    "kidnapped",
    "kidnapping",
    "abduct",
    "abducted",
    "abduction",
    "harassment",
    "harassed",
    "intimidation",
    "threat",
    "threatened",
    "discrimination",
    "discriminated",
    "religious freedom",
    "freedom of religion",
    "freedom of belief",
    "raid",
    "raided",
    "torture",
    "tortured",
    "expelled",
    "expulsion",
    "banned",
    "ban on",
    "illegal to",
    "violence",
    "violent",
    "massacre",
    "bombing",
    "bombed",
    # French
    "persécut",
    "persecut",
    "liberté religieuse",
    "liberte religieuse",
    "extrémistes",
    "extremistes",
    "passé à tabac",
    "passe a tabac",
    "fermeture",
    "fermée",
    "fermee",
    "fermé",
    "ferme la",
    "attentat",
    "attaque",
    "attaqué",
    "attaquee",
    "vandalisé",
    "vandalise",
    "martyre",
    "emprisonné",
    "emprisonne",
    "arrêté",
    "arrete",
    # Spanish
    "persecución",
    "persecucion",
    "perseguido",
    "perseguidos",
    "libertad religiosa",
    "ataque",
    "ataques",
    "asesinado",
    "asesinato",
    "martirio",
    "mártir",
    "martir",
    "detenido",
    "detenidos",
    "arrestado",
    "encarcelado",
    "secuestro",
    "secuestrado",
    "blasfemia",
    "apostasía",
    "apostasia",
    "quema",
    "quemada",
    "vandalismo",
    "vandalizado",
    "profanación",
    "profanacion",
    "incendio",
    "incendian",
    # Italian
    "persecuzione",
    "perseguitato",
    "perseguitati",
    "libertà religiosa",
    "liberta religiosa",
    "attacco",
    "attacchi",
    "assassinato",
    "omicidio",
    "martirio",
    "martire",
    "arrestato",
    "detenuto",
    "carcere",
    "rapimento",
    "rapito",
    "blasfemia",
    "apostasia",
    "vandali",
    "vandalismo",
    # Portuguese
    "perseguição",
    "perseguicao",
    "perseguido",
    "perseguidos",
    "liberdade religiosa",
    "ataque",
    "ataques",
    "assassinato",
    "assassinado",
    "martírio",
    "martirio",
    "mártir",
    "preso",
    "detido",
    "prisão",
    "prisao",
    "sequestro",
    "sequestrado",
    "blasfêmia",
    "blasfemia",
    "apostasia",
    # German
    "verfolgung",
    "verfolgt",
    "religionsfreiheit",
    "angriff",
    "angriffe",
    "ermordet",
    "mord",
    "märtyrer",
    "maertyrer",
    "martyrer",
    "verhaftet",
    "inhaftiert",
    "gefängnis",
    "gefangnis",
    "entführt",
    "entfuehrt",
    "entführung",
    "blasphemie",
    "abfall vom glauben",
    "kirchenschändung",
)

# Clear off-topic phrases even if keywords overlap loosely
REJECT_MARKERS = (
    "football",
    "soccer",
    "cricket score",
    "stock market",
    "recipe",
    "weather forecast",
    "box office",
)

# Trafficking / modern slavery — NOT in HARM_MARKERS. High-trust feeds must not
# pass on trafficking language alone; only victim-framed Christian/religious cases.
TRAFFICKING_MARKERS = (
    "trafficking",
    "trafficked",
    "human trafficking",
    "sex trafficking",
    "modern slavery",
    "forced labor",
    "forced labour",
    "forced marriage",
    "debt bondage",
    "bonded labor",
    "bonded labour",
    "enslaved",
    "enslavement",
    # French
    "traite des êtres",
    "traite des etres",
    "travail forcé",
    "travail force",
    "mariage forcé",
    "mariage force",
    # Spanish
    "trata de personas",
    "trata de blancas",
    "trabajo forzoso",
    "matrimonio forzado",
    # Italian
    "tratta di esseri",
    "lavoro forzato",
    "matrimonio forzato",
    # Portuguese
    "tráfico humano",
    "trafico humano",
    "trabalho forçado",
    "trabalho forcado",
    "casamento forçado",
    # German
    "menschenhandel",
    "zwangsarbeit",
    "zwangsheirat",
)

# Clergy / religious as persons appear in victim regexes below (word-bounded).
# Avoid bare "sister"/"sisters" — too noisy for bag-of-words matching.

TRAFFICKING_ADVOCACY_MARKERS = (
    "talitha kum",
    "annual report",
    "world day against trafficking",
    "world day against trafficking in persons",
    "fight against trafficking",
    "fight human trafficking",
    "fighting human trafficking",
    "end human trafficking",
    "ending human trafficking",
    "combat trafficking",
    "combatting trafficking",
    "combating trafficking",
    "anti-trafficking",
    "antitrafficking",
    "teaches against",
    "awareness campaign",
)

_TRAFFICKING_VICTIM_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"traffick\w*\s+of\s+christians?",
        r"christians?\s+(?:are\s+|were\s+|been\s+)?traffick",
        r"christian\s+(?:girls?|women|woman|children|child|families?|converts?|"
        r"boys?|men|man)\b.{0,80}(?:traffick|forced\s+marriage|forced\s+labou?r|"
        r"bonded|modern\s+slavery|enslav|sold\s+into)",
        r"(?:traffick|forced\s+marriage|forced\s+labou?r|bonded|modern\s+slavery|"
        r"enslav|sold\s+into).{0,80}christian\s+(?:girls?|women|woman|children|"
        r"child|families?|converts?|boys?|men|man)\b",
        r"(?:nuns?|monks?|pastors?|priests?|religious\s+sisters?)\b.{0,80}"
        r"(?:traffick|enslav|bonded|forced\s+labou?r|forced\s+marriage|sold\s+into)",
        r"(?:traffick|enslav|bonded|forced\s+labou?r|sold\s+into).{0,80}"
        r"(?:nuns?|monks?|pastors?|priests?|religious\s+sisters?)\b",
        r"(?:pastor|priest|christian).{0,40}famil(?:y|ies).{0,40}"
        r"(?:sold|bonded|traffick|enslav|forced)",
        r"forced\s+marriage\s+of\s+christian",
        r"christian.{0,40}forced\s+marriage",
    )
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(t in text for t in terms)


def _combined_article_text(
    title: str | None = None,
    description: str | None = None,
    categories: list[str] | None = None,
) -> str:
    parts = [title or "", description or ""]
    if categories:
        parts.extend(categories)
    text = " ".join(parts).lower()
    return re.sub(r"\s+", " ", text).strip()


def is_christian_trafficking_victim(
    title: str | None = None,
    description: str | None = None,
    categories: list[str] | None = None,
) -> bool:
    """True when Christians or religious are trafficking / slavery victims.

    Church or secular anti-trafficking advocacy without Christian/religious
    victims does not count. Trafficking markers are intentionally excluded from
    HARM_MARKERS so high-trust feeds cannot pass on trafficking alone.
    """
    text = _combined_article_text(title, description, categories)
    if not text or not _contains_any(text, TRAFFICKING_MARKERS):
        return False

    if any(p.search(text) for p in _TRAFFICKING_VICTIM_PATTERNS):
        return True

    # Secondary bag-of-words path: Christian marker + trafficking + a clear
    # victim cue, excluding advocacy-only framing. Religious-person cases are
    # covered by the regex patterns above (word-bounded).
    has_christian = _contains_any(text, CHRISTIAN_MARKERS)
    victim_cues = (
        "girl",
        "girls",
        "woman",
        "women",
        "child",
        "children",
        "convert",
        "converts",
        "victim",
        "victims",
        "family",
        "families",
        "sold into",
        "rescued from",
    )
    if (
        has_christian
        and _contains_any(text, victim_cues)
        and not _contains_any(text, TRAFFICKING_ADVOCACY_MARKERS)
    ):
        return True

    return False


def is_christian_persecution(
    title: str | None = None,
    description: str | None = None,
    categories: list[str] | None = None,
    *,
    high_trust_source: bool = False,
) -> bool:
    """Return True if the item is about Christian persecution / related harm.

    Requires both a Christian marker and a harm/restriction marker in the
    combined text (title + description + categories), unless *high_trust_source*
    is True and categories alone clearly indicate persecution coverage.

    Trafficking, forced labor, and forced marriage count only when Christians
    or religious persons are the victims (see is_christian_trafficking_victim).
    """
    text = _combined_article_text(title, description, categories)
    if not text:
        return False

    if _contains_any(text, REJECT_MARKERS):
        return False

    if is_christian_trafficking_victim(
        title=title, description=description, categories=categories
    ):
        return True

    has_christian = _contains_any(text, CHRISTIAN_MARKERS)
    has_harm = _contains_any(text, HARM_MARKERS)

    if has_christian and has_harm:
        return True

    # High-trust FoRB / persecution specialist outlets: accept clear FoRB-harm
    # language even when the headline does not name Christians explicitly
    # (e.g. anti-conversion laws, freedom of religion rulings).
    # Trafficking is not in HARM_MARKERS — trafficking-only high-trust items fail.
    if high_trust_source and has_harm:
        return True

    if high_trust_source and categories:
        cat_blob = " ".join(categories).lower()
        persecution_cats = (
            "persecution",
            "religious freedom",
            "christianity",
            "apostasy",
            "blasphemy",
            "forced conversion",
            "church attack",
            "martyrdom",
            "imprisonment",
            "kidnapping",
            "church closure",
            "freedom of religion",
            "forb",
        )
        if any(c in cat_blob for c in persecution_cats):
            return True

    return False


# Back-compat alias used by older fetchers
def is_persecution_article(text: str) -> bool:
    return is_christian_persecution(title=text, description="")
