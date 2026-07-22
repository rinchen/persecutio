import os
import shutil
import json
import time
from urllib.parse import quote
from pathlib import Path

import yaml
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COUNTRIES = ROOT / "countries"
FETCHED = DATA / "fetched"
FETCHED.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
COUNTRIES.mkdir(parents=True, exist_ok=True)


def backup(path: Path):
    if not path.exists():
        return path
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    dest = path.with_suffix(f".bak-{ts}{path.suffix}")
    shutil.copy2(path, dest)
    return dest


backup((DATA / "countries.yml"))
backup((ROOT / "assets/data/geojson.json"))
backup((ROOT / "assets/data/search.json"))


def fetch_json(url: str, path: Path, skip: bool = False):
    try:
        if path.exists() and skip:
            return json.loads(path.read_text(encoding="utf-8"))
        import urllib.request
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = resp.read().decode("utf-8", errors="ignore")
        path.write_text(payload, encoding="utf-8")
        return json.loads(payload)
    except Exception:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}


natural_earth_geojson = fetch_json(
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/refs/heads/master/geojson/ne_110m_admin_0_countries.geojson",
    FETCHED / "natural_earth_110m.geojson",
    skip=False,
)


def country_polygons_from_geojson(geojson):
    by_iso = {}
    features = geojson.get("features", []) if isinstance(geojson, dict) else []
    for feature in features:
        props = feature.get("properties", {}) or {}
        iso = props.get("ISO_A3") or props.get("iso_3") or props.get("ADM0_A3")
        geo = feature.get("geometry")
        if not iso or not geo:
            continue
        by_iso[str(iso).upper()] = geo
    return by_iso


country_polygons = country_polygons_from_geojson(natural_earth_geojson)


def wikipedia_summary(title: str):
    key = title.replace(" ", "_").replace("/", "_")
    cached = FETCHED / "wiki" / f"{quote(key, safe='')}.json"
    cached.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(key, safe='')}"
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = resp.read().decode("utf-8", errors="ignore")
        cached.write_text(payload, encoding="utf-8")
        return json.loads(payload)
    except Exception:
        if cached.exists():
            try:
                return json.loads(cached.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}


COUNTRIES_DATA = [
  {
    "title": "Afghanistan",
    "slug": "afghanistan",
    "iso3": "AFG",
    "status": "severe",
    "persecution_level": "Extreme",
    "lat": 33.93,
    "lng": 67.70,
    "modern": (
        "After the Taliban's return to power in August 2021, Afghanistan became one of "
        "the most restrictive places for Christians in the world. Christian converts from "
        "Islam risk death, abduction, or expulsion. House churches operate in extreme "
        "secrecy. Bibles, Christian media, and public worship are illegal. Aid agencies "
        "with religious ties face surveillance and expulsion."
    ),
    "historical": (
        "Christianity has a long but small presence in Afghanistan, from ancient Silk Road "
        "churches in the north to modern Catholic and Protestant missionary activity. After "
        "years of war in the 1980s and 1990s, the 2001-2021 period saw small but "
        "increasing Christian communities, especially among foreign workers and a few indigenous "
        "converts. Post-2021 Taliban rule reversed what little space had opened."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Afghanistan", "url": "https://www.uscirf.gov/countries/afghanistan", "date": "2023"},
      {"title": "BBC News - Afghanistan Christians 2021", "url": "https://www.bbc.com/news/world-asia-58293018", "date": "2021"}
    ],
    "source_ids": {
        "historical": ["bbc2021", "odwwl2024"],
        "modern": ["uscirf2023afghanistan", "odwwl2024"]
    },
    "pew_slug": ""
  },
  {
    "title": "China",
    "slug": "china",
    "iso3": "CHN",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 35.86,
    "lng": 104.19,
    "modern": (
        "China ranks among the world's most restrictive environments for Christians. The "
        "government controls official churches through state associations, while unregistered "
        "house churches face raids, demolition, surveillance, and detention. Regulations have "
        "tightened cross-border religious ties, youth religious activity is restricted, and "
        "online religious content is censored."
    ),
    "historical": (
        "Christianity first arrived in China by the Tang dynasty through Nestorian missionaries. "
        "Catholic and Protestant missions expanded from the 16th century onward, then were "
        "curtailed after 1949. The Cultural Revolution targeted churches and religious leaders "
        "severely; limited revival occurred after 1979, followed by new state-control measures "
        "from the 2010s onward."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - China", "url": "https://www.uscirf.gov/countries/china", "date": "2023"},
      {"title": "Pew Research - Religion in China", "url": "https://www.pewresearch.org/religion/2023/08/30/religion-in-china/", "date": "2023"}
    ],
    "source_ids": {
        "historical": ["pew2023china", "odwwl2024"],
        "modern": ["uscirf2023china", "odwwl2024"]
    },
    "pew_slug": "china"
  },
  {
    "title": "Colombia",
    "slug": "colombia",
    "iso3": "COL",
    "status": "warning",
    "persecution_level": "Moderate",
    "lat": 4.57,
    "lng": -74.30,
    "modern": (
        "Catholic clergy, Protestant pastors, and Christian human rights defenders continue to be "
        "targeted by guerrillas, paramilitaries, and criminal gangs, especially in Caqueta, "
        "Narino, and Norte de Santander. Killings and threats persist despite the 2016 peace "
        "agreement, and indigenous and Afro-Colombian Christian communities are especially vulnerable."
    ),
    "historical": (
        "Catholicism arrived with 16th-century Spanish colonization and shaped civic and cultural "
        "life for centuries. Political violence between Liberals and Conservatives in the 19th and "
        "20th centuries sometimes targeted churches and their leaders, and church-state conflict "
        "recurred through constitutional and agrarian disputes."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Colombia", "url": "https://www.uscirf.gov/countries/colombia", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023colombia", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Cuba",
    "slug": "cuba",
    "iso3": "CUB",
    "status": "restricted",
    "persecution_level": "Moderate",
    "lat": 21.52,
    "lng": -77.78,
    "modern": (
        "Religious freedom has improved since the 1990s but remains uneven. The Catholic Church "
        "provides social services yet cannot register new churches freely, import materials without "
        "restriction, or access state media easily. Independent Protestant house churches still "
        "report occasional harassment and economic pressure."
    ),
    "historical": (
        "Catholicism dominated colonial Cuba for centuries. After 1959, the revolutionary "
        "government confiscated church property, expelled clergy, and banned Christian education. "
        "The Soviet period enforced atheistic ideology almost absolutely; reforms began in the late "
        "1980s and 1990s, allowing greater religious expression."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Cuba", "url": "https://www.uscirf.gov/countries/cuba", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023cuba", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Eritrea",
    "slug": "eritrea",
    "iso3": "ERI",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 15.17,
    "lng": 39.78,
    "modern": (
        "The government controls all recognized religious communities and effectively banned "
        "unregistered evangelical churches in 2002. Hundreds of unregistered Christians remain "
        "detained without charge, and children are interrogated about home worship. Military "
        "conscription is enforced under harsh conditions and can affect religious practice."
    ),
    "historical": (
        "Christianity arrived in the 4th century and made Eritrea one of Africa's oldest Christian "
        "regions. Italian, British, and later Ethiopian rule shaped modern denominations. Since "
        "independence, restrictive religious policy has increased state oversight of worship."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Eritrea", "url": "https://www.uscirf.gov/countries/eritrea", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023eritrea", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "India",
    "slug": "india",
    "iso3": "IND",
    "status": "warning",
    "persecution_level": "Moderate/High",
    "lat": 20.59,
    "lng": 78.96,
    "modern": (
        "Christians face rising violence and legal restrictions linked to anti-conversion laws in "
        "multiple states. Vigilante groups have forced re-conversions and attacked churches; pastors "
        "are sometimes jailed under these laws. Religious minorities report increasing societal "
        "intimidation and educational pressure."
    ),
    "historical": (
        "Tradition holds that Thomas the Apostle evangelized southern India in the first century. "
        "Portuguese, Catholic, and Protestant missions expanded from the 15th century onwards. "
        "Anti-Christian violence and legislation recurred during colonial, princely-state, and "
        "post-independence eras."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - India", "url": "https://www.uscirf.gov/countries/india", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023india", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Indonesia",
    "slug": "indonesia",
    "iso3": "IDN",
    "status": "warning",
    "persecution_level": "Moderate",
    "lat": 0.79,
    "lng": 113.92,
    "modern": (
        "Indonesia is religiously plural but Christians in some provinces face official restrictions "
        "on building churches, societal pressure, and occasional mob violence. Blasphemy-related "
        "prosecutions and local regulations can target minority Christians, especially in Aceh and "
        "some Javanese districts."
    ),
    "historical": (
        "Christianity arrived in the form of Portuguese Catholic missions and later Dutch Protestant "
        "missions in the Moluccas, Papua, and Batak lands. Communities in Flores and East Timor "
        "have long Catholic traditions, while Post-independence Pancasila ideology limited some "
        "religious expressions and generated periodic communal conflict."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Indonesia", "url": "https://www.uscirf.gov/countries/indonesia", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023indonesia", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Iran",
    "slug": "iran",
    "iso3": "IRN",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 32.42,
    "lng": 53.68,
    "modern": (
        "Converts from Islam to Christianity face imprisonment, surveillance, and coerced "
        "re-education. House churches are raided and leaders sentenced to long prison terms. "
        "Armenian and Assyrian communities retain limited state recognition but still face pressure "
        "over property transfer and educational rights."
    ),
    "historical": (
        "Assyrian Christianity in Persia dates to the 1st century, with Armenian communities from "
        "the 4th century onward. After the 1979 Islamic Revolution, evangelistic institutions closed "
        "while officially recognized minorities kept restricted rights; apostasy charges grew in the "
        "2000s."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Iran", "url": "https://www.uscirf.gov/countries/iran", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023iran", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Iraq",
    "slug": "iraq",
    "iso3": "IRQ",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 33.22,
    "lng": 43.67,
    "modern": (
        "The 2014-2017 ISIS advance devastated Assyrian, Chaldean, and Armenian communities in "
        "Mosul and the Nineveh Plains. Many remain displaced. Returning Christians face militia "
        "pressure, land disputes, and fragile security. Church bombings and threats still recur."
    ),
    "historical": (
        "Mesopotamia is the cradle of Eastern Christianity, with communities dating to the 1st-2nd "
        "centuries. These communities thrived under the Abbasids, endured Timurid and Mongol raids, "
        "and continued under the Ottoman millet system, only to face existential threat in the 21st "
        "century from jihadist violence and mass displacement."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Iraq", "url": "https://www.uscirf.gov/countries/iraq", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023iraq", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Laos",
    "slug": "laos",
    "iso3": "LAO",
    "status": "restricted",
    "persecution_level": "High",
    "lat": 19.85,
    "lng": 102.49,
    "modern": (
        "The Lao state oversees all religious activity, restricting church construction, religious "
        "education and training, and material imports. Protestant and Catholic groups face local "
        "harassment and surveillance; some Christians remain imprisoned, especially in remote villages."
    ),
    "historical": (
        "Catholic missionaries arrived in the 17th century; French colonial rule expanded Protestant "
        "and Catholic presence. After 1975, the communist government restricted religious life to "
        "state-sanctioned bodies and drove many churches underground."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Laos", "url": "https://www.uscirf.gov/countries/laos", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023laos", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Mexico",
    "slug": "mexico",
    "iso3": "MEX",
    "status": "warning",
    "persecution_level": "Moderate",
    "lat": 23.63,
    "lng": -102.55,
    "modern": (
        "Organized crime and local power disputes drive much anti-Christian violence. Priests have "
        "been kidnapped and killed, churches burned or extorted, and indigenous Catholic communities "
        "displaced in Chiapas, Michoacan, and Guerrero. Clergy defending migrants are also at risk."
    ),
    "historical": (
        "Catholicism shaped colonial New Spain for three centuries. After independence, Mexico enacted "
        "restrictive constitutions and fought the Cristero War (1926-1929), which killed thousands. "
        "Religious freedom was restored through late-20th-century legal reforms."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Mexico", "url": "https://www.uscirf.gov/countries/mexico", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023mexico", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Nicaragua",
    "slug": "nicaragua",
    "iso3": "NIC",
    "status": "restricted",
    "persecution_level": "Moderate/High",
    "lat": 12.86,
    "lng": -85.20,
    "modern": (
        "Since 2018 and accelerating after 2021, the Ortega government has arrested, exiled, and "
        "criminalized opposition clergy. Catholic media and schools have been closed or seized, and "
        "bishops and priests face charges and house arrest. Religious institutions are under severe "
        "state scrutiny."
    ),
    "historical": (
        "Catholicism dominated Nicaraguan civic life from the 16th century through the 1979 "
        "revolution. The Sandinista period initially tolerated, then restricted, religious "
        "expression; after peace accords in the 1990s the church regained public stature before "
        "being again targeted in the 2020s."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Nicaragua", "url": "https://www.uscirf.gov/countries/nicaragua", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023nicaragua", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Nigeria",
    "slug": "nigeria",
    "iso3": "NGA",
    "status": "persecution",
    "persecution_level": "High",
    "lat": 9.08,
    "lng": 8.68,
    "modern": (
        "Boko Haram, ISWAP, and criminal bandits have killed, kidnapped, and displaced Christian "
        "villagers and pastors across northern Nigeria. Hundreds of churches have been destroyed. "
        "In the Middle Belt, communal violence often carries religious dimensions along farmer-herder "
        "lines near the Jos Plateau."
    ),
    "historical": (
        "Christianity arrived through Portuguese traders in the 15th century and expanded through "
        "19th-century missions and colonial education. Post-independence political tensions, the "
        "1967-1970 Biafran War, and the late-20th-century spread of Salafi-jihadist ideology in "
        "the Sahel created fertile ground for present-day violence."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Nigeria", "url": "https://www.uscirf.gov/countries/nigeria", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023nigeria", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "North Korea",
    "slug": "north-korea",
    "iso3": "PRK",
    "status": "severe",
    "persecution_level": "Extreme",
    "lat": 40.34,
    "lng": 127.51,
    "modern": (
        "Possessing a Bible, attending a house church, or displaying Christian symbols can result in "
        "imprisonment in political prison camps. Defectors report systematic suppression of religion "
        "and enforced loyalty to the Juche ideology. No legal Christian practice is possible."
    ),
    "historical": (
        "Before 1945, Pyongyang was known as the Jerusalem of the East. After the Korean War, "
        "the DPRK closed churches, purged clergy, and criminalized public religion. Small underground "
        "activity survived through refugees and defectors."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - North Korea", "url": "https://www.uscirf.gov/countries/north-korea", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023northkorea", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Pakistan",
    "slug": "pakistan",
    "iso3": "PAK",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 30.37,
    "lng": 69.34,
    "modern": (
        "Blasphemy laws can carry life imprisonment or death and have been used against Christians. "
        "Forced conversions and marriages of Christian girls remain common. Churches are occasionally "
        "attacked during holidays or communal tensions, and security for worship remains weak."
    ),
    "historical": (
        "Catholicism arrived with Portuguese traders; Protestant missions expanded under British rule "
        "in Punjab and Sindh. Partition created a Muslim-majority state with large Christian minorities "
        "centered in Punjab. Anti-blasphemy legislation hardened under Zia-ul-Haq in the 1980s, and "
        "since then legal and societal pressures have increased."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Pakistan", "url": "https://www.uscirf.gov/countries/pakistan", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023pakistan", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Saudi Arabia",
    "slug": "saudi-arabia",
    "iso3": "SAU",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 23.88,
    "lng": 45.07,
    "modern": (
        "Conversion from Islam can carry the death penalty. Organized Christian fellowship and public "
        "worship by Muslims-turned-Christians are illegal. Expatriate Christians sometimes worship "
        "discreetly in private homes, while importing or distributing Bibles remains criminalized."
    ),
    "historical": (
        "Christian communities once existed in Arabia but were largely extinguished after Islam's rise. "
        "19th- and 20th-century Catholic and Protestant missions operated under Ottoman and later Saudi "
        "administration, but eventually all organized Christian community activity was restricted."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Saudi Arabia", "url": "https://www.uscirf.gov/countries/saudi-arabia", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023saudiarabia", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Somalia",
    "slug": "somalia",
    "iso3": "SOM",
    "status": "severe",
    "persecution_level": "Extreme",
    "lat": 5.15,
    "lng": 46.19,
    "modern": (
        "Al-Shabaab executes or violently expels suspected Christians. The weak federal government "
        "cannot protect religious minorities. Foreign Christian aid workers face surveillance, threats, "
        "and expulsion for religious activity, and no church buildings are operational."
    ),
    "historical": (
        "Byzantine and Ethiopian trade linked early coastal Christian communities to wider Christian "
        "networks. European Catholic and Anglican missions grew in the late 19th and early 20th "
        "centuries, then were expelled or closed under Siad Barre's secular socialist rule after 1969. "
        "Civil war destroyed remaining institutions in the 1990s."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Somalia", "url": "https://www.uscirf.gov/countries/somalia", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023somalia", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Syria",
    "slug": "syria",
    "iso3": "SYR",
    "status": "severe",
    "persecution_level": "Very High",
    "lat": 34.80,
    "lng": 38.99,
    "modern": (
        "ISIS control from 2014 to 2017 devastated ancient Christian communities across the Khabour "
        "valley, Homs, and Qamishli. Many Assyrian, Armenian, and Greek Orthodox Christians fled abroad, "
        "and returning civilians face property disputes, militia pressure, and occasional targeted attacks."
    ),
    "historical": (
        "Damascus and Antioch are central to early Christianity. Syriac Orthodoxy, Eastern Catholicism, "
        "and Greek Orthodoxy have deep roots. From late Ottoman rule through French mandate and Baathist "
        "secularism, communal power and religious courts were progressively restricted."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Syria", "url": "https://www.uscirf.gov/countries/syria", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023syria", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Vietnam",
    "slug": "vietnam",
    "iso3": "VNM",
    "status": "restricted",
    "persecution_level": "Moderate/High",
    "lat": 14.05,
    "lng": 108.27,
    "modern": (
        "Religious activity requires state registration, and unregistered groups face surveillance and "
        "harassment. Catholic and Protestant communities are monitored, and land disputes over church "
        "property remain frequent, especially in the central highlands."
    ),
    "historical": (
        "French colonial rule introduced Catholic and Protestant missions; after division and reunification "
        "under communist rule, religious life was restricted to government-approved bodies. Economic "
        "reform in the 1980s allowed some reopening, but controls remain."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Vietnam", "url": "https://www.uscirf.gov/countries/vietnam", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023vietnam", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Yemen",
    "slug": "yemen",
    "iso3": "YEM",
    "status": "severe",
    "persecution_level": "Extreme",
    "lat": 15.55,
    "lng": 48.51,
    "modern": (
        "Civil war and Houthi authority have made Yemen unsafe for organized Christianity. Suspected "
        "converts face death or expulsion, foreign religious workers are expelled, and humanitarian aid "
        "access may be restricted when religious affiliation is discovered."
    ),
    "historical": (
        "Ancient southern Arabian Christianity declined after the rise of Islam; the Himyarite kingdom "
        "saw a brief Christian period in the 5th-6th centuries. Ottoman and British colonial contact "
        "renewed small Catholic and Protestant communities that later contracted during 20th-century "
        "conflicts."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
      {"title": "USCIRF 2023 Annual Report - Yemen", "url": "https://www.uscirf.gov/countries/yemen", "date": "2023"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023yemen", "odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "United States",
    "slug": "united-states",
    "iso3": "USA",
    "status": "open",
    "persecution_level": "Low",
    "lat": 37.09,
    "lng": -95.71,
    "modern": (
        "The United States constitutionally protects religious freedom, and Christians generally worship "
        "openly. Concerns remain in the form of occasional hate crimes, zoning disputes over church "
        "construction, and broader cultural polarization rather than state-sponsored restrictions."
    ),
    "historical": (
        "Catholicism arrived in Spanish Florida and French Louisiana, while Protestant groups shaped "
        "British colonies from the 17th century onward. First Amendment protections made religious "
        "freedom a national principle, though 19th-century nativist movements sometimes targeted "
        "Catholics and new immigrant churches."
    ),
    "sources": [
      {"title": "USCIRF 2023 Annual Report - United States", "url": "https://www.uscirf.gov/countries/united-states", "date": "2023"},
      {"title": "Pew Research - Religion in America", "url": "https://www.pewresearch.org/religion/religious-landscape-study/", "date": "2023"}
    ],
    "source_ids": {"historical": ["pew2023america"], "modern": ["uscirf2023unitedstates", "pew2023america"]},
    "pew_slug": "america"
  },
  {
    "title": "Brazil",
    "slug": "brazil",
    "iso3": "BRA",
    "status": "open",
    "persecution_level": "Low",
    "lat": -14.23,
    "lng": -51.92,
    "modern": (
        "Brazil guarantees religious freedom and has one of the world's largest Christian populations. "
        "Occasional incidents of vandalism or anti-Christian rhetoric occur, but large-scale or state-led "
        "persecution is not present."
    ),
    "historical": (
        "Catholicism dominated Brazil after Portuguese colonization, and evangelical Protestantism expanded "
        "rapidly in the 20th century. Religious competition sometimes triggers local tension, especially "
        "among indigenous communities and in favelas, but these have not reached systematic persecution."
    ),
    "sources": [
      {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"}
    ],
    "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
    "pew_slug": ""
  },
  {
    "title": "Uganda",
    "slug": "uganda",
    "iso3": "UGA",
    "status": "open",
    "persecution_level": "Low",
    "lat": 1.37,
    "lng": 32.29,
    "modern": (
        "Uganda has generally respected Christian worship, though Muslim minorities in some regions "
        "report local friction and occasional attacks. Anti-LGBTQ laws have raised international concern, "
        "and some faith leaders have been targeted from multiple sides, but this is not systematic "
        "state persecution of Christians."
    ),
    "historical": (
        "Catholic and Protestant missions shaped Ugandan education and society from the 19th century "
        "onward. The Uganda Martyrs became a powerful Catholic and Anglican symbol, and churches remained "
        "influential through colonialism and independence."
    ),
    "sources": [
      {"title": "USCIRF 2023 Annual Report - Uganda", "url": "https://www.uscirf.gov/countries/uganda", "date": "2023"}
    ],
    "source_ids": {"historical": ["uscirf2023uganda"], "modern": ["uscirf2023uganda"]},
    "pew_slug": ""
  }
]

sources = {
  "odwwl2024": {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
  "uscirf2023afghanistan": {"title": "USCIRF 2023 Annual Report - Afghanistan", "url": "https://www.uscirf.gov/countries/afghanistan", "date": "2023"},
  "bbc2021": {"title": "BBC News - Afghanistan Christians 2021", "url": "https://www.bbc.com/news/world-asia-58293018", "date": "2021"},
  "uscirf2023china": {"title": "USCIRF 2023 Annual Report - China", "url": "https://www.uscirf.gov/countries/china", "date": "2023"},
  "pew2023china": {"title": "Pew Research - Religion in China", "url": "https://www.pewresearch.org/religion/2023/08/30/religion-in-china/", "date": "2023"},
  "uscirf2023colombia": {"title": "USCIRF 2023 Annual Report - Colombia", "url": "https://www.uscirf.gov/countries/colombia", "date": "2023"},
  "uscirf2023cuba": {"title": "USCIRF 2023 Annual Report - Cuba", "url": "https://www.uscirf.gov/countries/cuba", "date": "2023"},
  "uscirf2023eritrea": {"title": "USCIRF 2023 Annual Report - Eritrea", "url": "https://www.uscirf.gov/countries/eritrea", "date": "2023"},
  "uscirf2023india": {"title": "USCIRF 2023 Annual Report - India", "url": "https://www.uscirf.gov/countries/india", "date": "2023"},
  "uscirf2023indonesia": {"title": "USCIRF 2023 Annual Report - Indonesia", "url": "https://www.uscirf.gov/countries/indonesia", "date": "2023"},
  "uscirf2023iran": {"title": "USCIRF 2023 Annual Report - Iran", "url": "https://www.uscirf.gov/countries/iran", "date": "2023"},
  "uscirf2023iraq": {"title": "USCIRF 2023 Annual Report - Iraq", "url": "https://www.uscirf.gov/countries/iraq", "date": "2023"},
  "uscirf2023laos": {"title": "USCIRF 2023 Annual Report - Laos", "url": "https://www.uscirf.gov/countries/laos", "date": "2023"},
  "uscirf2023mexico": {"title": "USCIRF 2023 Annual Report - Mexico", "url": "https://www.uscirf.gov/countries/mexico", "date": "2023"},
  "uscirf2023nicaragua": {"title": "USCIRF 2023 Annual Report - Nicaragua", "url": "https://www.uscirf.gov/countries/nicaragua", "date": "2023"},
  "uscirf2023nigeria": {"title": "USCIRF 2023 Annual Report - Nigeria", "url": "https://www.uscirf.gov/countries/nigeria", "date": "2023"},
  "uscirf2023northkorea": {"title": "USCIRF 2023 Annual Report - North Korea", "url": "https://www.uscirf.gov/countries/north-korea", "date": "2023"},
  "uscirf2023pakistan": {"title": "USCIRF 2023 Annual Report - Pakistan", "url": "https://www.uscirf.gov/countries/pakistan", "date": "2023"},
  "uscirf2023saudiarabia": {"title": "USCIRF 2023 Annual Report - Saudi Arabia", "url": "https://www.uscirf.gov/countries/saudi-arabia", "date": "2023"},
  "uscirf2023somalia": {"title": "USCIRF 2023 Annual Report - Somalia", "url": "https://www.uscirf.gov/countries/somalia", "date": "2023"},
  "uscirf2023syria": {"title": "USCIRF 2023 Annual Report - Syria", "url": "https://www.uscirf.gov/countries/syria", "date": "2023"},
  "uscirf2023vietnam": {"title": "USCIRF 2023 Annual Report - Vietnam", "url": "https://www.uscirf.gov/countries/vietnam", "date": "2023"},
  "uscirf2023yemen": {"title": "USCIRF 2023 Annual Report - Yemen", "url": "https://www.uscirf.gov/countries/yemen", "date": "2023"},
  "uscirf2023unitedstates": {"title": "USCIRF 2023 Annual Report - United States", "url": "https://www.uscirf.gov/countries/united-states", "date": "2023"},
  "uscirf2023uganda": {"title": "USCIRF 2023 Annual Report - Uganda", "url": "https://www.uscirf.gov/countries/uganda", "date": "2023"},
  "pew2023america": {"title": "Pew Research - Religion in America", "url": "https://www.pewresearch.org/religion/religious-landscape-study/", "date": "2023"}
}

for c in COUNTRIES_DATA:
    iso = str(c.get("iso3", "")).upper()
    resolved = []
    for sid_template in c.get("source_ids", {}).get("modern", []):
        sid = sid_template.format(slug=c.get("slug", ""), pew_slug=c.get("pew_slug", ""))
        if sid in sources and sid not in resolved:
            resolved.append(sid)
    wiki = wikipedia_summary(c.get("title", ""))
    c.setdefault("metadata", {})
    c["metadata"]["sources"] = [sources[sid] for sid in resolved]
    c["metadata"]["source_ids"] = resolved
    c["metadata"]["shape_geo"] = country_polygons.get(iso)
    c["metadata"]["wiki_url"] = wiki.get("content_urls", {}).get("desktop", {}).get("page") if isinstance(wiki, dict) else None
    c["metadata"]["wiki_extract"] = wiki.get("extract") if isinstance(wiki, dict) else None
    c["metadata"]["country_polygon"] = True if iso in country_polygons else False

countries_data = {"countries": COUNTRIES_DATA, "sources": sources, "fetched": {
    "natural_earth_geojson": "data/fetched/natural_earth_110m.geojson",
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
}}
(DATA / "countries.yml").write_text(
    yaml.safe_dump(countries_data, allow_unicode=True, sort_keys=False),
    encoding="utf-8",
)

print("collect ok")
