import os
import shutil
import json
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


def fetch_json(url: str, path: Path, name: str, skip: bool = False):
    status = {
        "name": name,
        "url": url,
        "status": "ok",
        "fetched_at": None,
        "message": None,
    }
    try:
        if path.exists() and skip:
            status["status"] = "cached"
            status["fetched_at"] = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            return json.loads(path.read_text(encoding="utf-8")), status
        import urllib.request
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = resp.read().decode("utf-8", errors="ignore")
        path.write_text(payload, encoding="utf-8")
        status["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return json.loads(payload), status
    except Exception as e:
        status["status"] = "failed"
        status["message"] = str(e)
        if path.exists():
            try:
                status["status"] = "partial"
                return json.loads(path.read_text(encoding="utf-8")), status
            except Exception:
                pass
        return {}, status


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
    },
    {
        "title": "Algeria",
        "slug": "algeria",
        "iso3": "DZA",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 28.03,
        "lng": 1.66,
        "modern": (
            "Authorities have closed Protestant churches, detained Christian leaders, "
            "and pressured house churches under restrictive worship laws. Evangelical "
            "Christians especially report fear of arrest and surveillance."
        ),
        "historical": (
            "Christianity survived in North Africa through late antiquity, then receded "
            "after Arab conquest and Ottoman rule. Modern Catholic and Protestant "
            "missions expanded in colonial Algeria before post-independence restrictions "
            "limited organized Christian presence."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023algeria", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Bangladesh",
        "slug": "bangladesh",
        "iso3": "BGD",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 23.68,
        "lng": 90.35,
        "modern": (
            "Christians, especially converts and tribal communities, face violence, "
            "kidnapping, and pressure from Islamist actors. Anti-conversion narratives "
            "and blasphemy-related tensions put churches and leaders at risk."
        ),
        "historical": (
            "Catholic and Protestant missions operated largely among tribal and remote "
            "communities and later expanded urban ministries. Communal violence and "
            "new legal restrictions in the late 20th and early 21st centuries "
            "increasingly targeted Christian minorities."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023bangladesh", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Central African Republic",
        "slug": "central-african-republic",
        "iso3": "CAF",
        "status": "persecution",
        "persecution_level": "High",
        "lat": 6.61,
        "lng": 20.93,
        "modern": (
            "Armed groups attack churches, kill clergy, and displace Christian villages, "
            "while religious leaders are sometimes targeted for mobilizing peacebuilding. "
            "Militia violence and communal tensions remain acute."
        ),
        "historical": (
            "Catholic and Protestant missions expanded in the late 19th and 20th "
            "centuries, but decades of coups, rebellions, and foreign intervention "
            "have repeatedly destabilized Christian communities and displaced populations."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023car", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Egypt",
        "slug": "egypt",
        "iso3": "EGY",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 26.82,
        "lng": 30.01,
        "modern": (
            "Egyptian Christians, especially Coptic Orthodox and evangelical communities, "
            "face sectarian violence, discrimination in church licensing, and periodic "
            "suicide bombings and shootings by jihadist groups."
        ),
        "historical": (
            "Egypt is the cradle of early monastic Christianity. Coptic tradition traces "
            "its origins to St. Mark; centuries of Islamic rule brought fluctuating "
            "protection, persecution, and coexistence before modern nationalist changes."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023egypt", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Haiti",
        "slug": "haiti",
        "iso3": "HTI",
        "status": "persecution",
        "persecution_level": "High",
        "lat": 18.97,
        "lng": -72.28,
        "modern": (
            "Gang violence and kidnapping target clergy, church workers, and congregations, "
            "while humanitarian collapse hampers worship, education, and relief. Priests "
            "and religious sisters have been abducted or killed."
        ),
        "historical": (
            "Catholicism arrived with French colonization, followed by Protestant and "
            "independent missions. Haitian Vodou blended African and Catholic elements, "
            "while 20th and 21st-century instability undermined church life and safety."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023haiti", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Libya",
        "slug": "libya",
        "iso3": "LBY",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 26.34,
        "lng": 17.22,
        "modern": (
            "Instability, Islamist armed groups, and fragmented governance expose "
            "Christians to detention, violence, and forced displacement. Foreign "
            "Christian migrants and converts face especially high risks."
        ),
        "historical": (
            "Libya preserves ancient Christian sites from the Roman and Byzantine eras, "
            "but communities shrank after Arab invasions and Ottoman rule. Modern "
            "mission activity ended as restrictive regimes centralized religious control."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023libya", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Malaysia",
        "slug": "malaysia",
        "iso3": "MYS",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 4.21,
        "lng": 101.97,
        "modern": (
            "Christians face local restrictions on church construction, religious education, "
            "and proselytization while societal tensions sometimes turn violent on "
            "the Malay peninsula and in East Malaysian states."
        ),
        "historical": (
            "Christian missions operated among indigenous peoples in Sabah, Sarawak, "
            "and the peninsula from the 19th century onward. Modern pluralism coexists "
            "with Islamic legal frameworks limiting public Christian witness."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023malaysia", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Myanmar",
        "slug": "myanmar",
        "iso3": "MMR",
        "status": "persecution",
        "persecution_level": "High",
        "lat": 21.91,
        "lng": 95.95,
        "modern": (
            "Both military rule and ethnic armed conflict expose Christians, especially "
            "Chin and Kachin communities, to village destruction, forced displacement, "
            "and conscription. Junta-era pressure intensified after the 2021 coup."
        ),
        "historical": (
            "Baptist, Catholic, and other missions expanded Christian education and "
            "health services in hill and border areas during the colonial period, with "
            "conversion later used to justify ethnic and political discrimination."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023myanmar", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Sudan",
        "slug": "sudan",
        "iso3": "SDN",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 12.86,
        "lng": 30.21,
        "modern": (
            "Post-Bashiri transition eased some restrictions, but violence in the Nuba "
            "Mountains and Blue Nile and periodic militia threats still imperil Christian "
            "communities, schools, and churches."
        ),
        "historical": (
            "Christianity in Sudan traces back to ancient Nubian kingdoms and continued "
            "under centuries of Islamic sultanates. Late-20th-century missionary activity "
            "expanded churches in the south and among displaced communities."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023sudan", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Turkey",
        "slug": "turkey",
        "iso3": "TUR",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 38.96,
        "lng": 35.24,
        "modern": (
            "Christians experience state restrictions on worship, property, and clergy, "
            "including closures of churches and detentions, alongside occasional societal "
            "harassment and hostility across the countryside and major cities."
        ),
        "historical": (
            "Ancient Christian communities in Anatolia produced ecumenical councils and "
            "monastic movements, then declined through Byzantine-Muslim frontier raiding, "
            "the Ottoman millet system, and the Republic's secular nationalism."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023turkey", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Venezuela",
        "slug": "venezuela",
        "iso3": "VEN",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 6.42,
        "lng": -66.58,
        "modern": (
            "Economic collapse, state hostility, and armed groups constrain church "
            "operations, while clergy defending social services face harassment. "
            "Catholic aid networks provide vital relief and remain under political pressure."
        ),
        "historical": (
            "Catholic missions accompanied Spanish colonization, with independence-era "
            "tensions and 20th-century secularism shaping church-state relations, while "
            "recent authoritarian pressure has revived clerical confrontation."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023venezuela", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Zimbabwe",
        "slug": "zimbabwe",
        "iso3": "ZWE",
        "status": "open",
        "persecution_level": "Low",
        "lat": -19.01,
        "lng": 29.15,
        "modern": (
            "Christians generally worship freely in Zimbabwe, but occasional threats "
            "and land disputes target apostolic and marginalized groups, and some "
            "churches face pressure when leaders speak out on political issues."
        ),
        "historical": (
            "Protestant and Catholic missions expanded education and health services "
            "during the colonial era, while post-independence politics sometimes clashed "
            "with outspoken bishops and missions aligned with labor and rights movements."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["uscirf2023zimbabwe", "odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Mali",
        "slug": "mali",
        "iso3": "MLI",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 17.57,
        "lng": -4.00,
        "modern": (
            "Jihadist groups including JNIM and ISIS-Sahel target Christian "
            "communities in northern and central Mali, carrying out church "
            "attacks, kidnappings, and forced displacement. Converts from Islam "
            "face death threats and social ostracism."
        ),
        "historical": (
            "Christianity arrived through French colonization in the 19th century. "
            "Mali's Christian minority remains small, concentrated in southern "
            "regions. Since 2012, jihadist insurgency has devastated Christian "
            "communities in the north."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Burkina Faso",
        "slug": "burkina-faso",
        "iso3": "BFA",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 12.37,
        "lng": -1.52,
        "modern": (
            "Islamic militant groups attack churches and Christian villages "
            "across northern and eastern Burkina Faso. Hundreds of Christians "
            "have been killed, and thousands displaced. Church leaders receive "
            "death threats and some have been assassinated."
        ),
        "historical": (
            "Catholic and Protestant missions expanded during the colonial period. "
            "Christians remain a minority in a predominantly Muslim country. "
            "Since 2015, jihadist violence has escalated dramatically."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Maldives",
        "slug": "maldives",
        "iso3": "MDV",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 3.20,
        "lng": 73.22,
        "modern": (
            "Conversion from Islam is illegal and can be punished by death. "
            "The few Christian converts practice in extreme secrecy. No church "
            "buildings exist, and Christian worship is entirely underground. "
            "Tourism workers face surveillance for religious activity."
        ),
        "historical": (
            "The Maldives has been Muslim since the 12th century. Portuguese "
            "colonial rule in the 16th century briefly reintroduced Christianity, "
            "but it was quickly suppressed. Modern Christianity exists only among "
            "secret converts and foreign workers."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Mauritania",
        "slug": "mauritania",
        "iso3": "MRT",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 21.01,
        "lng": -10.94,
        "modern": (
            "Apostasy from Islam carries the death penalty under Mauritanian law. "
            "Christian converts live in extreme secrecy. No churches are permitted, "
            "and any Christian activity is closely monitored by authorities."
        ),
        "historical": (
            "Mauritania has been exclusively Muslim since its founding. Christian "
            "presence has always been minimal, limited to a handful of foreign "
            "workers and secret converts."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Morocco",
        "slug": "morocco",
        "iso3": "MAR",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 31.79,
        "lng": -7.09,
        "modern": (
            "Proselytizing Muslims is illegal and can result in imprisonment. "
            "Christian converts face family pressure, surveillance, and social "
            "ostracism. House churches operate with caution, and foreign "
            "Christians are monitored for religious activity."
        ),
        "historical": (
            "Morocco was once home to vibrant Christian communities during the "
            "Roman and Vandal periods. Islam arrived in the 7th century, and "
            "Christianity gradually disappeared. Modern Christian presence dates "
            "to French and Spanish colonization."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Uzbekistan",
        "slug": "uzbekistan",
        "iso3": "UZB",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 41.38,
        "lng": 64.59,
        "modern": (
            "Religious activity requires state registration, and unregistered "
            "groups face raids and fines. Church leaders are detained, religious "
            "materials confiscated, and children under 16 banned from services. "
            "Evangelism is effectively criminalized."
        ),
        "historical": (
            "Christianity existed in Central Asia from early centuries. Russian "
            "Orthodox and Protestant missions expanded under 19th-century "
            "imperial rule. Soviet atheism suppressed all religion; post-independence "
            "Uzbekistan maintained tight controls."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Niger",
        "slug": "niger",
        "iso3": "NER",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 17.61,
        "lng": 8.08,
        "modern": (
            "Islamic militant groups attack Christian communities and churches "
            "in border regions. Converts from Islam face severe family and "
            "community pressure. Proselytizing is legally restricted, and "
            "security conditions limit Christian activity in many areas."
        ),
        "historical": (
            "Christianity arrived through French colonization. The Christian "
            "minority remains small, concentrated in southern and western regions. "
            "Since 2015, jihadist violence from Nigeria and Mali has spread into "
            "Niger's border areas."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Turkmenistan",
        "slug": "turkmenistan",
        "iso3": "TKM",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 38.97,
        "lng": 59.56,
        "modern": (
            "The government tightly controls all religious activity. Unregistered "
            "churches face raids, fines, and detention of leaders. Religious "
            "literature import is restricted, and foreign worship services are "
            "monitored. Underground churches operate under constant threat."
        ),
        "historical": (
            "Russian Orthodox and Protestant missions operated during imperial "
            "and Soviet eras. Turkmenistan's 1991 independence brought a nominally "
            "secular state with heavy restrictions on minority religions, "
            "continuing Soviet-era patterns of control."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Oman",
        "slug": "oman",
        "iso3": "OMN",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 21.47,
        "lng": 55.98,
        "modern": (
            "Non-Muslim worship is permitted only in private or designated areas. "
            "Proselytizing Muslims is illegal. Christian expatriates worship "
            "quietly, but any public display or outreach is prohibited. Convert "
            "families face social pressure."
        ),
        "historical": (
            "Ancient Christianity existed in Oman through the Church of the East. "
            "Islam became dominant from the 7th century. Modern Christian presence "
            "is largely due to expatriate workers from South Asia and the West."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Ethiopia",
        "slug": "ethiopia",
        "iso3": "ETH",
        "status": "warning",
        "persecution_level": "Moderate/High",
        "lat": 9.15,
        "lng": 40.49,
        "modern": (
            "Ethiopia has ancient Christian roots but faces growing tensions. "
            "Orthodox, Protestant, and Catholic communities experience periodic "
            "violence, especially in Oromia and Amhara regions. Religious "
            "restrictions have increased under the current government."
        ),
        "historical": (
            "Ethiopia is one of the oldest Christian nations, with traditions "
            "dating to the 4th century. The Ethiopian Orthodox Tewahedo Church "
            "has shaped national identity for centuries. Political and ethnic "
            "conflicts sometimes take on religious dimensions."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Tunisia",
        "slug": "tunisia",
        "iso3": "TUN",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 33.89,
        "lng": 9.54,
        "modern": (
            "Christian converts face social ostracism and family pressure. "
            "Proselytizing is illegal, and church activities are monitored. "
            "The small Christian community exercises caution in worship and "
            "public religious expression."
        ),
        "historical": (
            "Tunisia was a major center of early Christianity. Vandal and Byzantine "
            "rule maintained Christian communities until the Arab conquest. Modern "
            "Christianity is mostly limited to foreign workers and a few converts."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Democratic Republic of Congo",
        "slug": "democratic-republic-of-congo",
        "iso3": "COD",
        "status": "persecution",
        "persecution_level": "High",
        "lat": -4.04,
        "lng": 21.76,
        "modern": (
            "The Allied Democratic Forces (ADF) and other armed groups attack "
            "Christian communities in eastern Congo, destroying churches and "
            "displacing thousands. Church leaders are targeted for peacebuilding "
            "efforts, and religious institutions face extortion."
        ),
        "historical": (
            "Catholic and Protestant missions played central roles in education "
            "and healthcare during the colonial period. Churches remain influential "
            "in Congolese society, and religious leaders have historically been "
            "voices for peace and democracy."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Bhutan",
        "slug": "bhutan",
        "iso3": "BTN",
        "status": "restricted",
        "persecution_level": "Moderate/High",
        "lat": 27.51,
        "lng": 90.43,
        "modern": (
            "Proselytizing is illegal under Bhutanese law. Christians face "
            "social pressure from the Buddhist majority and restrictions on "
            "worship. The small Christian community practices privately, and "
            "religious education for children is prohibited."
        ),
        "historical": (
            "Bhutan has been predominantly Buddhist for centuries. Christianity "
            "arrived through Tibetan and Indian influences in the 20th century. "
            "The government promotes Buddhism as the national religion and "
            "restricts other faiths."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Mozambique",
        "slug": "mozambique",
        "iso3": "MOZ",
        "status": "persecution",
        "persecution_level": "High",
        "lat": -18.67,
        "lng": 35.53,
        "modern": (
            "ISIS-affiliated insurgents in Cabo Delgado province attack Christian "
            "villages, churches, and humanitarian workers. Thousands have been "
            "killed or displaced since 2017. Church buildings are targeted and "
            "religious leaders face threats."
        ),
        "historical": (
            "Catholic and Protestant missions expanded during Portuguese colonial "
            "rule. Christianity grew significantly in the 20th century. The "
            "insurgency in the north has created a humanitarian crisis affecting "
            "Christian communities."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Kazakhstan",
        "slug": "kazakhstan",
        "iso3": "KAZ",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 48.02,
        "lng": 66.92,
        "modern": (
            "Religious registration requirements restrict unregistered churches. "
            "Police raids on worship services occur, and religious literature "
            "imports are controlled. Evangelism and proselytizing face legal "
            "limitations."
        ),
        "historical": (
            "Russian Orthodox and Soviet-era atheism shaped Kazakhstan's religious "
            "landscape. Post-independence, Islam and Orthodox Christianity coexist "
            "under state regulation. Protestant and Catholic communities remain "
            "small."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Tajikistan",
        "slug": "tajikistan",
        "iso3": "TJK",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": 38.86,
        "lng": 71.28,
        "modern": (
            "The government restricts all religious activity outside state-approved "
            "bodies. Unregistered churches face fines and closure. Children under "
            "18 are banned from religious services, and religious education is "
            "heavily regulated."
        ),
        "historical": (
            "Tajikistan's religious landscape reflects Soviet-era atheism and "
            "traditional Sunni Islam. Small Orthodox and Protestant communities "
            "exist, but post-independence laws have tightened religious control."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Qatar",
        "slug": "qatar",
        "iso3": "QAT",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 25.35,
        "lng": 51.18,
        "modern": (
            "Proselytizing Muslims is illegal. Non-Muslim worship is permitted "
            "only in designated areas. Christian expatriates worship with caution, "
            "and convert families face social and legal pressure."
        ),
        "historical": (
            "Qatar has been Muslim since the 7th century. Modern Christian "
            "presence is largely due to expatriate workers. The government "
            "allows limited non-Muslim worship but restricts public expression."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Comoros",
        "slug": "comoros",
        "iso3": "COM",
        "status": "severe",
        "persecution_level": "Very High",
        "lat": -11.65,
        "lng": 43.33,
        "modern": (
            "Christianity is virtually illegal. Conversion from Islam can result "
            "in loss of citizenship. No churches exist, and any Christian "
            "activity is conducted in extreme secrecy. Social pressure against "
            "converts is intense."
        ),
        "historical": (
            "Comoros has been Muslim since the 15th century. Portuguese colonizers "
            "briefly introduced Christianity, but it was quickly suppressed. "
            "Modern Christianity exists only among a handful of secret converts."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Cameroon",
        "slug": "cameroon",
        "iso3": "CMR",
        "status": "persecution",
        "persecution_level": "High",
        "lat": 7.37,
        "lng": 12.35,
        "modern": (
            "Boko Haram and ISWAP attacks in the Far North target Christian "
            "villages and churches. The Anglophone crisis in the Northwest "
            "and Southwest has displaced thousands of Christians, and church "
            "leaders are caught in the crossfire."
        ),
        "historical": (
            "Catholic and Protestant missions expanded during German, British, "
            "and French colonial rule. Christianity is a major religion in "
            "Cameroon, but regional conflicts have created new vulnerabilities."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Brunei",
        "slug": "brunei",
        "iso3": "BRN",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 4.54,
        "lng": 114.73,
        "modern": (
            "Brunei's implementation of Sharia law restricts non-Muslim worship. "
            "Proselytizing is illegal, and Christian communities worship "
            "privately. Public religious displays by non-Muslims are limited."
        ),
        "historical": (
            "Brunei has been Muslim since the 15th century. Christianity arrived "
            "through British colonization and modern expatriate communities. "
            "Sharia implementation in 2019 increased restrictions on non-Muslim "
            "religious expression."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Kyrgyzstan",
        "slug": "kyrgyzstan",
        "iso3": "KGZ",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 41.20,
        "lng": 74.77,
        "modern": (
            "Anti-cult laws restrict religious minorities. Unregistered churches "
            "face pressure, and religious education for minors is limited. "
            "Social pressure from the Muslim majority affects Christian converts."
        ),
        "historical": (
            "Russian Orthodox and Soviet-era atheism shaped Kyrgyzstan's "
            "religious landscape. Post-independence, Islam has resurged, and "
            "Protestant and Catholic communities remain small and sometimes "
            "face social hostility."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Jordan",
        "slug": "jordan",
        "iso3": "JOR",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 30.59,
        "lng": 36.24,
        "modern": (
            "Conversion from Islam is restricted and socially dangerous. Christian "
            "worship is generally permitted, but proselytizing Muslims is illegal. "
            "Convert families face honor-related threats, and churches avoid "
            "public outreach."
        ),
        "historical": (
            "Jordan has ancient Christian roots from the early church. Arab "
            "Christian communities have existed for centuries. Modern Jordan "
            "maintains relative tolerance, but legal and social restrictions "
            "affect converts from Islam."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Russia",
        "slug": "russia",
        "iso3": "RUS",
        "status": "warning",
        "persecution_level": "Moderate/High",
        "lat": 61.52,
        "lng": 105.32,
        "modern": (
            "Anti-evangelism laws restrict religious activity outside registered "
            "sites. Protestant and Catholic communities face raids, fines, and "
            "denial of registration. Jehovah's Witnesses are banned, and foreign "
            "religious workers are expelled."
        ),
        "historical": (
            "Russian Orthodoxy dominated for centuries. Soviet atheism suppressed "
            "all religion; post-Soviet revival favored Orthodoxy. Recent laws "
            "restricting proselytization and foreign religious ties have increased "
            "pressure on minority faiths."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Azerbaijan",
        "slug": "azerbaijan",
        "iso3": "AZE",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 40.14,
        "lng": 47.58,
        "modern": (
            "Religious activity requires registration. Unregistered groups face "
            "raids and fines. Non-Muslim worship is restricted, and foreign "
            "religious workers are monitored. Christian converts from Islam "
            "face family and community pressure."
        ),
        "historical": (
            "Azerbaijan has been Muslim since the medieval period. Small Orthodox "
            "and Protestant communities exist, but post-independence laws "
            "tightened religious control."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Sri Lanka",
        "slug": "sri-lanka",
        "iso3": "LKA",
        "status": "warning",
        "persecution_level": "Moderate/High",
        "lat": 7.87,
        "lng": 80.77,
        "modern": (
            "Buddhist nationalist groups attack churches and Christian "
            "converts. Anti-conversion laws are proposed or enforced in some "
            "areas. Church construction faces opposition, and pastors receive "
            "threats."
        ),
        "historical": (
            "Catholicism arrived with Portuguese colonization in the 16th century. "
            "Dutch and British rule added Protestant missions. Post-independence "
            "Buddhist nationalism has periodically targeted Christian minorities."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Philippines",
        "slug": "philippines",
        "iso3": "PHL",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 12.88,
        "lng": 121.77,
        "modern": (
            "Muslim separatist groups in Mindanao target Christian communities. "
            "Churches and pastors are caught in the conflict between government "
            "forces and insurgents. Kidnappings and attacks on Christian workers "
            "occur periodically."
        ),
        "historical": (
            "Catholicism arrived with Spanish colonization in the 16th century. "
            "The Philippines is predominantly Catholic, but Muslim communities "
            "in the south have long sought autonomy, creating regional tensions."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Guinea",
        "slug": "guinea",
        "iso3": "GIN",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 9.95,
        "lng": -11.86,
        "modern": (
            "Christian converts from Islam face family pressure and social "
            "ostracism. Proselytizing is restricted, and church activities are "
            "monitored. The small Christian community exercises caution."
        ),
        "historical": (
            "French colonization introduced Catholicism and Protestantism. "
            "Christians remain a minority in a predominantly Muslim country. "
            "Post-independence governments have generally maintained religious "
            "tolerance, but social pressure on converts persists."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
    {
        "title": "Bahrain",
        "slug": "bahrain",
        "iso3": "BHR",
        "status": "warning",
        "persecution_level": "Moderate",
        "lat": 26.07,
        "lng": 50.55,
        "modern": (
            "Christian worship is permitted in designated areas but proselytizing "
            "Muslims is illegal. Expatriate Christians worship freely, but "
            "converts from Islam face social and legal pressure."
        ),
        "historical": (
            "Bahrain has ancient Christian communities from the Church of the East. "
            "Islam became dominant from the 7th century. Modern Christian presence "
            "is largely due to expatriate workers."
        ),
        "source_ids": {"historical": ["odwwl2024"], "modern": ["odwwl2024"]},
        "pew_slug": ""
    },
]

sources = {
    "natural_earth_110m": {"title": "Natural Earth map boundaries", "url": "https://www.naturalearthdata.com/", "date": "2024"},
    "odwwl2024": {"title": "Open Doors World Watch List 2024", "url": "https://www.opendoorsusa.org/christian-persecution/world-watch-list/", "date": "2024"},
    "acn2024": {"title": "ACN Persecuted and Forgotten? ACN report on Christians oppressed for their Faith 2022-24 / Report on Christian persecution", "url": "https://acninternational.org/new-acn-report-persecution-of-christians-has-worsened-around-the-globe/", "date": "2024"},
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
    "pew2023america": {"title": "Pew Research - Religion in America", "url": "https://www.pewresearch.org/religion/religious-landscape-study/", "date": "2023"},
    "uscirf2023algeria": {"title": "USCIRF 2023 Annual Report - Algeria", "url": "https://www.uscirf.gov/countries/algeria", "date": "2023"},
    "uscirf2023bangladesh": {"title": "USCIRF 2023 Annual Report - Bangladesh", "url": "https://www.uscirf.gov/countries/bangladesh", "date": "2023"},
    "uscirf2023car": {"title": "USCIRF 2023 Annual Report - Central African Republic", "url": "https://www.uscirf.gov/countries/central-african-republic", "date": "2023"},
    "uscirf2023egypt": {"title": "USCIRF 2023 Annual Report - Egypt", "url": "https://www.uscirf.gov/countries/egypt", "date": "2023"},
    "uscirf2023haiti": {"title": "USCIRF 2023 Annual Report - Haiti", "url": "https://www.uscirf.gov/countries/haiti", "date": "2023"},
    "uscirf2023libya": {"title": "USCIRF 2023 Annual Report - Libya", "url": "https://www.uscirf.gov/countries/libya", "date": "2023"},
    "uscirf2023malaysia": {"title": "USCIRF 2023 Annual Report - Malaysia", "url": "https://www.uscirf.gov/countries/malaysia", "date": "2023"},
    "uscirf2023myanmar": {"title": "USCIRF 2023 Annual Report - Myanmar", "url": "https://www.uscirf.gov/countries/myanmar", "date": "2023"},
    "uscirf2023sudan": {"title": "USCIRF 2023 Annual Report - Sudan", "url": "https://www.uscirf.gov/countries/sudan", "date": "2023"},
    "uscirf2023turkey": {"title": "USCIRF 2023 Annual Report - Turkey", "url": "https://www.uscirf.gov/countries/turkey", "date": "2023"},
    "uscirf2023venezuela": {"title": "USCIRF 2023 Annual Report - Venezuela", "url": "https://www.uscirf.gov/countries/venezuela", "date": "2023"},
    "uscirf2023zimbabwe": {"title": "USCIRF 2023 Annual Report - Zimbabwe", "url": "https://www.uscirf.gov/countries/zimbabwe", "date": "2023"},
    "freedomhouse2024": {"title": "Freedom House Freedom in the World 2024", "url": "https://freedomhouse.org/report/freedom-world", "date": "2024"},
    "statedepartment2023": {"title": "U.S. State Department International Religious Freedom Report 2023", "url": "https://www.state.gov/international-religious-freedom-reports/", "date": "2023"},
    "ohchr2024": {"title": "OHCHR Universal Human Rights Index", "url": "https://uhri.ohchr.org/", "date": "2024"},
    "gdelt2025": {"title": "GDELT Global Database of Events, Language, and Tone", "url": "https://www.gdeltproject.org/", "date": "2025"},
    "owid2024": {"title": "Our World in Data - Religious Composition (Pew Research)", "url": "https://ourworldindata.org/grapher/religious-composition", "date": "2024"},
    "odwwl2026": {"title": "Open Doors World Watch List 2026", "url": "https://www.opendoors.org/en-US/persecution/countries/", "date": "2026"},
    "uscirf2025russia": {"title": "USCIRF 2025 Annual Report - Russia", "url": "https://www.uscirf.gov/countries/russia", "date": "2025"},
    "uscirf2025azerbaijan": {"title": "USCIRF 2025 Annual Report - Azerbaijan", "url": "https://www.uscirf.gov/countries/azerbaijan", "date": "2025"},
    "uscirf2025srilanka": {"title": "USCIRF 2025 Annual Report - Sri Lanka", "url": "https://www.uscirf.gov/countries/sri-lanka", "date": "2025"},
    "uscirf2025kazakhstan": {"title": "USCIRF 2025 Annual Report - Kazakhstan", "url": "https://www.uscirf.gov/countries/kazakhstan", "date": "2025"},
    "uscirf2025kyrgyzstan": {"title": "USCIRF 2025 Annual Report - Kyrgyzstan", "url": "https://www.uscirf.gov/countries/kyrgyzstan", "date": "2025"},
    "uscirf2025turkmenistan": {"title": "USCIRF 2025 Annual Report - Turkmenistan", "url": "https://www.uscirf.gov/countries/turkmenistan", "date": "2025"},
    "uscirf2025uzbekistan": {"title": "USCIRF 2025 Annual Report - Uzbekistan", "url": "https://www.uscirf.gov/countries/uzbekistan", "date": "2025"},
    "uscirf2025tajikistan": {"title": "USCIRF 2025 Annual Report - Tajikistan", "url": "https://www.uscirf.gov/countries/tajikistan", "date": "2025"},
    "morningstarnews2026": {"title": "Morning Star News - Christian Persecution Reports", "url": "https://morningstarnews.org/", "date": "2026"},
    "vid2026": {"title": "Violent Incidents Database (IIRF/GCR)", "url": "https://violentincidents.plataformac.org/", "date": "2026"},
    "gcr2026": {"title": "Global Christian Relief - Persecution Statistics 2026", "url": "https://globalchristianrelief.org/stories/christian-persecution-statistics", "date": "2026"},
    "acn2025": {"title": "Aid to the Church in Need - Religious Freedom Report 2025", "url": "https://acninternational.org/religiousfreedomreport/", "date": "2025"},
    "csw2026": {"title": "Christian Solidarity Worldwide - Persecution Reports", "url": "https://www.csw.org.uk/", "date": "2026"},
    "icc2026": {"title": "International Christian Concern - Global Persecution Reports", "url": "https://www.persecution.org/", "date": "2026"},
}


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


natural_earth_geojson, natural_earth_status = fetch_json(
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/refs/heads/master/geojson/ne_110m_admin_0_countries.geojson",
    FETCHED / "natural_earth_110m.geojson",
    "natural_earth_110m",
    skip=False,
)
country_polygons = country_polygons_from_geojson(natural_earth_geojson)


def wikipedia_summary(title: str):
    key = title.replace(" ", "_").replace("/", "_")
    cached = FETCHED / "wiki" / f"{quote(key, safe='')}.json"
    cached.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(key, safe='')}"
    data, status = fetch_json(url, cached, f"wikipedia:{key}", skip=False)
    return data, status


def load_fetched_json(filename):
    path = FETCHED / filename
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


freedom_house = load_fetched_json("freedom_house.json")
opendoors_data = load_fetched_json("opendoors.json")
gdelt_data = load_fetched_json("gdelt.json")
owid_data = load_fetched_json("owid_religion.json")
morningstarnews_data = load_fetched_json("morningstarnews.json")
vid_data = load_fetched_json("vid.json")
gcr_data = load_fetched_json("gcr_stats.json")
acn_data = load_fetched_json("acn_report.json")
csw_data = load_fetched_json("csw.json")
icc_data = load_fetched_json("icc.json")


for c in COUNTRIES_DATA:
    iso = str(c.get("iso3", "")).upper()
    title = c.get("title", "")
    resolved = []
    for sid in c.get("source_ids", {}).get("modern", []):
        if sid in sources and sid not in resolved:
            resolved.append(sid)
    wiki, wiki_status = wikipedia_summary(title)
    c.setdefault("metadata", {})
    c["metadata"]["sources"] = [sources[sid] for sid in resolved]
    c["metadata"]["source_ids"] = resolved
    c["metadata"]["shape_geo"] = country_polygons.get(iso)
    c["metadata"]["wiki_url"] = wiki.get("content_urls", {}).get("desktop", {}).get("page") if isinstance(wiki, dict) else None
    c["metadata"]["wiki_extract"] = wiki.get("extract") if isinstance(wiki, dict) else None
    c["metadata"]["country_polygon"] = bool(iso in country_polygons)

    fh_countries = freedom_house.get("countries", {}) if isinstance(freedom_house, dict) else {}
    fh = fh_countries.get(title, {})
    if fh:
        c["metadata"]["freedom_house_status"] = fh.get("status")
        c["metadata"]["freedom_house_pr"] = fh.get("pr_score")
        c["metadata"]["freedom_house_cl"] = fh.get("cl_score")

    od_countries = opendoors_data.get("countries", {}) if isinstance(opendoors_data, dict) else {}
    od = od_countries.get(title, {})
    if od:
        c["metadata"]["opendoors_ranking"] = od.get("ranking")
        c["metadata"]["opendoors_score"] = od.get("score")

    gdelt_countries = gdelt_data.get("countries", {}) if isinstance(gdelt_data, dict) else {}
    gdelt_articles = gdelt_countries.get(title, [])
    if gdelt_articles:
        c["metadata"]["gdelt_recent_articles"] = len(gdelt_articles)
        c["metadata"]["gdelt_sample_urls"] = [a.get("url", "") for a in gdelt_articles[:3]]

    owid_countries = owid_data.get("countries", {}) if isinstance(owid_data, dict) else {}
    owid = owid_countries.get(title, {})
    if owid:
        c["metadata"]["christian_population"] = owid.get("christian_population")
        c["metadata"]["christian_percentage"] = owid.get("christian_percentage")

    msn_countries = morningstarnews_data.get("countries", {}) if isinstance(morningstarnews_data, dict) else {}
    msn_articles = msn_countries.get(title, [])
    if msn_articles:
        c["metadata"]["morningstarnews_articles"] = len(msn_articles)
        c["metadata"]["morningstarnews_samples"] = [
            {"title": a.get("title", ""), "url": a.get("url", ""), "date": a.get("date", "")}
            for a in msn_articles[:3]
        ]

    vid_countries = vid_data.get("countries", {}) if isinstance(vid_data, dict) else {}
    vid_entry = vid_countries.get(title, {})
    if vid_entry:
        c["metadata"]["vid_incidents_total"] = vid_entry.get("total_incidents")
        c["metadata"]["vid_killings"] = vid_entry.get("killings")
        c["metadata"]["vid_breakdown"] = {k: v for k, v in vid_entry.items() if k != "total_incidents" and v}

    gcr_countries = gcr_data.get("countries", {}) if isinstance(gcr_data, dict) else {}
    gcr_entry = gcr_countries.get(title, {})
    if gcr_entry:
        if gcr_entry.get("killed"):
            c["metadata"]["gcr_killed"] = gcr_entry["killed"]
        if gcr_entry.get("persecution_score"):
            c["metadata"]["gcr_persecution_score"] = gcr_entry["persecution_score"]
        if gcr_entry.get("notes"):
            c["metadata"]["gcr_notes"] = gcr_entry["notes"]

    acn_countries = acn_data.get("countries", {}) if isinstance(acn_data, dict) else {}
    acn_entry = acn_countries.get(title, {})
    if acn_entry:
        c["metadata"]["acn_classification"] = acn_entry.get("classification")
        if acn_entry.get("key_findings"):
            c["metadata"]["acn_key_findings"] = acn_entry["key_findings"][:2]

    csw_countries = csw_data.get("countries", {}) if isinstance(csw_data, dict) else {}
    csw_articles = csw_countries.get(title, [])
    if csw_articles:
        c["metadata"]["csw_articles"] = len(csw_articles)
        c["metadata"]["csw_samples"] = [
            {"title": a.get("title", ""), "url": a.get("url", ""), "date": a.get("date", "")}
            for a in csw_articles[:3]
        ]

    icc_countries = icc_data.get("countries", {}) if isinstance(icc_data, dict) else {}
    icc_articles = icc_countries.get(title, [])
    if icc_articles:
        c["metadata"]["icc_articles"] = len(icc_articles)
        c["metadata"]["icc_samples"] = [
            {"title": a.get("title", ""), "url": a.get("url", ""), "date": a.get("date", "")}
            for a in icc_articles[:3]
        ]

def load_fetch_statuses():
    statuses = []
    if not FETCHED.exists():
        return statuses
    for p in sorted(FETCHED.glob("*_status.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(s, dict) and s.get("name"):
                statuses.append(s)
        except Exception:
            pass
    return statuses


source_statuses = [natural_earth_status] + load_fetch_statuses()

countries_data = {
    "countries": COUNTRIES_DATA,
    "sources": sources,
    "fetched": {
        "natural_earth_geojson": "data/fetched/natural_earth_110m.geojson",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source_statuses": source_statuses,
        "data_sources": {
            "freedom_house": "data/fetched/freedom_house.json",
            "opendoors": "data/fetched/opendoors.json",
            "gdelt": "data/fetched/gdelt.json",
            "owid_religion": "data/fetched/owid_religion.json",
            "morningstarnews": "data/fetched/morningstarnews.json",
            "vid": "data/fetched/vid.json",
            "gcr_stats": "data/fetched/gcr_stats.json",
            "acn_report": "data/fetched/acn_report.json",
            "csw": "data/fetched/csw.json",
            "icc": "data/fetched/icc.json",
        },
    },
}
(DATA / "countries.yml").write_text(
    yaml.safe_dump(countries_data, allow_unicode=True, sort_keys=False),
    encoding="utf-8",
)
(DATA / "sources.yml").write_text(
    yaml.safe_dump({"sources": sources}, allow_unicode=True, sort_keys=False),
    encoding="utf-8",
)

print("collect ok")
