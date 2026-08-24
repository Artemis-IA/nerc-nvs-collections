#!/usr/bin/env python3
"""Add a 'Collection Type' column to NVS_collections_list.md based on title and content."""
import os
import re

DIR = "/home/imohamma/Documents/Dev/nvs-turtle"
TTL_DIR = os.path.join(DIR, "ttl")
INPUT_FILE = os.path.join(DIR, "NVS_collections_list.md")

# Read the existing file
with open(INPUT_FILE) as f:
    lines = f.readlines()

# Parse collections: (num, id, uri, title) - handle both old and new format
collections = []
for line in lines:
    # New format with Collection Type column
    m = re.match(r'\| (\d+) \| (\S+) \| (http[^|]+) \| (.+?) \| (.+?) \|', line)
    if m:
        collections.append({
            "num": int(m.group(1)),
            "id": m.group(2),
            "uri": m.group(3).strip(),
            "title": m.group(4).strip(),
        })
        continue
    # Old format without Collection Type
    m = re.match(r'\| (\d+) \| (\S+) \| (http[^|]+) \| (.+?) \|', line)
    if m:
        collections.append({
            "num": int(m.group(1)),
            "id": m.group(2),
            "uri": m.group(3).strip(),
            "title": m.group(4).strip(),
        })

print(f"Parsed {len(collections)} collections")

# Categorization rules based on title and TTL content
# Order matters: first match wins (most specific first)
RULES = [
    # Argo - all Rxx collections
    (lambda cid, title, content: re.match(r'^R\d|^RD\d|^RP\d|^RR\d|^RTV|^RMC', cid) or "argo" in title.lower(),
     "Argo"),

    # EMODnet (before SeaDataNet car BQ1/BQ2/BQ3 ont les deux dans leur contenu)
    (lambda cid, title, content: "emodnet" in title.lower() or re.match(r'^BQ|^EPL|^H0|^HA2|^P33|^P35|^P36', cid),
     "EMODnet"),

    # SeaDataNet (title-based prioritaire, puis contenu)
    (lambda cid, title, content: "seadatanet" in title.lower() or re.match(r'^L0[2-9]|^L1[0-9]|^L2[0-9]|^L3[0-9]|^V12|^V22|^V23|^C86|^C77|^F0[2-9]', cid) or "seadatanet" in content.lower()[:3000],
     "SeaDataNet"),

    # GEBCO / Bathymetrie
    (lambda cid, title, content: "gebco" in title.lower() or re.match(r'^GG|^GGB|^GGS|^GGT', cid) or "bathymetr" in title.lower() or "seafloor depth" in title.lower(),
     "GEBCO / Bathymetrie"),

    # ICES (title-based uniquement, mot entier pour eviter "practICES", "servICES", "matrICES")
    (lambda cid, title, content: re.search(r'\bICES\b', title) or re.match(r'^C17', cid),
     "ICES"),

    # DAC Coriolis / Coriolis (collection dediee, pas juste mention)
    (lambda cid, title, content: "coriolis" in title.lower(),
     "DAC Coriolis"),

    # GOOS / OceanOPS (title-based uniquement)
    (lambda cid, title, content: "goos" in title.lower() or "oceanops" in title.lower() or "global ocean observing" in title.lower() or re.match(r'^O01|^EXV', cid),
     "GOOS / OceanOPS"),

    # OceanGliders
    (lambda cid, title, content: "oceanglider" in title.lower() or re.match(r'^OG1', cid) or "seaglider" in title.lower(),
     "OceanGliders"),

    # CF / Climate and Forecast
    (lambda cid, title, content: "climate and forecast" in title.lower() or "cf standard" in title.lower() or re.match(r'^P07|^P15|^P29|^P30|^P31|^P37|^P38', cid),
     "CF / Climate Forecast"),

    # GCMD (Global Change Master Directory)
    (lambda cid, title, content: "global change master directory" in title.lower() or re.match(r'^P04|^P10|^P11|^P12|^P13|^P14|^P18|^P19|^P20|^P64', cid),
     "GCMD"),

    # BODC Parameter Semantic Model (S-series)
    (lambda cid, title, content: re.match(r'^S\d', cid) and ("bodc" in title.lower() or "semantic model" in title.lower()),
     "BODC Semantic Model"),

    # BODC Parameters (P-series: P01-P04, P06 - P05 est ISO 19115)
    (lambda cid, title, content: re.match(r'^P0[1-4]|^P06', cid),
     "BODC Parameters"),

    # ISO 19115 / ISO 19119 Topic Categories (P05, P26)
    (lambda cid, title, content: re.match(r'^P05|^P26', cid) or "iso19115 topic" in title.lower() or "iso19119" in title.lower(),
     "ISO 19115"),

    # BODC Organisations / Governance (B-series)
    (lambda cid, title, content: re.match(r'^B\d', cid) and ("organisation" in title.lower() or "governance" in title.lower() or "people" in title.lower() or "roles" in title.lower() or "integrity" in title.lower() or "reference material" in title.lower() or "operating procedures" in title.lower() or "measurement" in title.lower() or "platform models" in title.lower()),
     "BODC Organisation"),

    # BODC Governance (C30 - governance authorities)
    (lambda cid, title, content: re.match(r'^C30', cid) or "governance authorities" in title.lower(),
     "BODC Governance"),

    # MEDIN (title-based prioritaire)
    (lambda cid, title, content: "medin" in title.lower() or re.match(r'^C48|^M0[1-9]|^M1[0-9]', cid) and "crown estate" not in title.lower() and "habitat" not in title.lower() and "ramsar" not in title.lower() and "jncc" not in title.lower() and "ospar" not in title.lower() and "helcom" not in title.lower(),
     "MEDIN"),

    # OSPAR (title-based uniquement)
    (lambda cid, title, content: "ospar" in title.lower() or re.match(r'^M14|^M15|^M22', cid),
     "OSPAR"),

    # HELCOM (title-based uniquement)
    (lambda cid, title, content: "helcom" in title.lower() or re.match(r'^M23', cid),
     "HELCOM"),

    # INSPIRE (title-based uniquement)
    (lambda cid, title, content: "inspire" in title.lower() or re.match(r'^I1[0-5]', cid),
     "INSPIRE"),

    # SensorML / SWE
    (lambda cid, title, content: re.match(r'^W\d', cid) or "sensorml" in title.lower() or "sensor web enablement" in title.lower(),
     "SensorML / SWE"),

    # ISO 19115 code lists (G-series)
    (lambda cid, title, content: re.match(r'^G\d', cid) and ("iso" in title.lower() or "code" in title.lower() or re.match(r'^[A-Z]{2}_', title)),
     "ISO 19115"),

    # Geo-Seas
    (lambda cid, title, content: "geo-seas" in title.lower() or re.match(r'^GS', cid),
     "Geo-Seas"),

    # Coastal Atlas
    (lambda cid, title, content: "coastal atlas" in title.lower() or "coastal erosion" in title.lower(),
     "Coastal Atlas"),

    # ODATIS (avant Essential Variables car OD1 contient "essential variable" dans son titre)
    (lambda cid, title, content: "odatis" in title.lower() or re.match(r'^OD1', cid),
     "ODATIS"),

    # Essential Variables
    (lambda cid, title, content: "essential variable" in title.lower(),
     "Essential Variables"),

    # Movebank
    (lambda cid, title, content: "movebank" in title.lower(),
     "Movebank"),

    # OBIS
    (lambda cid, title, content: "obis" in title.lower(),
     "OBIS"),

    # NERC DataGrid
    (lambda cid, title, content: "nerc datagrid" in title.lower() or re.match(r'^N0', cid),
     "NERC DataGrid"),

    # EDS (Environmental Data Service)
    (lambda cid, title, content: "environmental data service" in title.lower() or "eds" in title.lower(),
     "EDS"),

    # Ocean Practices
    (lambda cid, title, content: "ocean practices" in title.lower(),
     "Ocean Practices"),

    # Ramsar
    (lambda cid, title, content: "ramsar" in title.lower(),
     "Ramsar"),

    # JNCC
    (lambda cid, title, content: "jncc" in title.lower(),
     "JNCC"),

    # Crown Estate
    (lambda cid, title, content: "crown estate" in title.lower(),
     "Crown Estate"),

    # Marine Habitat Classification
    (lambda cid, title, content: "marine habitat classification" in title.lower(),
     "Marine Habitat"),

    # MSFD (Marine Strategy Framework Directive)
    (lambda cid, title, content: "marine strategy framework" in title.lower() or "msfd" in title.lower(),
     "MSFD"),

    # Celtic Seas Partnership
    (lambda cid, title, content: "celtic seas" in title.lower(),
     "Celtic Seas"),

    # SeaVoX
    (lambda cid, title, content: "seavox" in title.lower(),
     "SeaVoX"),

    # NETMAR
    (lambda cid, title, content: "netmar" in title.lower(),
     "NETMAR"),

    # WMO
    (lambda cid, title, content: "world meteorological" in title.lower() or re.match(r'^L33', cid),
     "WMO"),

    # GRIB
    (lambda cid, title, content: "grib" in title.lower(),
     "GRIB"),

    # POGO
    (lambda cid, title, content: "partnership for observation of the global ocean" in title.lower(),
     "POGO"),

    # ESEAS
    (lambda cid, title, content: "eseas" in title.lower(),
     "ESEAS"),

    # MEDATLAS
    (lambda cid, title, content: "medatlas" in title.lower(),
     "MEDATLAS"),

    # EDIOS
    (lambda cid, title, content: "edios" in title.lower(),
     "EDIOS"),

    # Bonn Agreement
    (lambda cid, title, content: "bonn agreement" in title.lower(),
     "Bonn Agreement"),

    # i18n
    (lambda cid, title, content: "i18n" in title.lower(),
     "i18n"),

    # British Antarctic Survey
    (lambda cid, title, content: "british antarctic survey" in title.lower(),
     "British Antarctic Survey"),

    # BODC general (C-series with BODC in title, not already categorized)
    (lambda cid, title, content: re.match(r'^C\d', cid) and "bodc" in title.lower(),
     "BODC General"),

    # BODC Organisation Histories / roles
    (lambda cid, title, content: "organisation" in title.lower() or "organisation histories" in title.lower() or "organisation roles" in title.lower() or "project roles" in title.lower() or "dataset roles" in title.lower() or "organisation categories" in title.lower(),
     "BODC Organisation"),

    # BODC data model / series
    (lambda cid, title, content: "bodc series" in title.lower() or "bodc data model" in title.lower() or "bodc core failure" in title.lower(),
     "BODC General"),

    # BODC flags / quality
    (lambda cid, title, content: "bodc water sample" in title.lower() or "qualification flags" in title.lower() or "bodc measurement" in title.lower(),
     "BODC Quality"),

    # BODC pollution
    (lambda cid, title, content: "bodc marine pollution" in title.lower() or "bodc oilspill" in title.lower() or "oil spill" in title.lower() or "cedre pollution" in title.lower(),
     "BODC Pollution"),

    # BODC gazetteer / geography
    (lambda cid, title, content: "post town" in title.lower() or "administrative region" in title.lower() or "marsden squares" in title.lower() or "sea regions" in title.lower() or "charting progress" in title.lower() or "sea areas" in title.lower() or "ports gazetteer" in title.lower() or "salt and fresh water" in title.lower(),
     "BODC Gazetteer"),

    # IOC (Intergovernmental Oceanographic Commission)
    (lambda cid, title, content: "intergovernmental oceanographic commission" in title.lower(),
     "IOC"),

    # ISO countries
    (lambda cid, title, content: "international standards organisation countries" in title.lower() or "iso19115 topic" in title.lower(),
     "ISO 19115"),

    # EUNIS / Habitats
    (lambda cid, title, content: "european nature information system" in title.lower(),
     "EUNIS Habitats"),

    # Monitoring / Activity
    (lambda cid, title, content: "activity purpose" in title.lower() or "monitoring activity" in title.lower() or "legislative drivers" in title.lower(),
     "Monitoring"),

    # Vocabulary Server meta
    (lambda cid, title, content: "vocabulary server" in title.lower() or "subject categories" in title.lower(),
     "NVS Meta"),

    # EOS / Processing Levels
    (lambda cid, title, content: "processing levels" in title.lower() and "emodnet" not in title.lower(),
     "EOS Processing Levels"),

    # Flow Cytometry
    (lambda cid, title, content: "flow cytometry" in title.lower(),
     "Flow Cytometry"),

    # Matrix / IODE
    (lambda cid, title, content: "matrix categories" in title.lower() or "iode" in title.lower(),
     "IODE"),

    # Geotechnical
    (lambda cid, title, content: "geotechnical" in title.lower(),
     "Geotechnical"),

    # Units of measure
    (lambda cid, title, content: "units of measure" in title.lower(),
     "Units"),

    # Marisaurus
    (lambda cid, title, content: "marisaurus" in title.lower(),
     "Marisaurus"),

    # BODC semantic model (catch remaining S-series)
    (lambda cid, title, content: re.match(r'^S\d', cid) and "bodc" in title.lower(),
     "BODC Semantic Model"),

    # Sampling
    (lambda cid, title, content: "sampling net" in title.lower() or "sampling" in title.lower(),
     "Sampling"),

    # Research Vessel
    (lambda cid, title, content: "research vessel" in title.lower(),
     "Research Vessel"),
]

# Cache content for collections that need it
content_cache = {}

def get_content(col_id):
    if col_id not in content_cache:
        fpath = os.path.join(TTL_DIR, f"{col_id}.ttl")
        if os.path.exists(fpath):
            with open(fpath, "r", errors="replace") as f:
                content_cache[col_id] = f.read()
        else:
            content_cache[col_id] = ""
    return content_cache[col_id]

# Categorize each collection
for col in collections:
    cid = col["id"]
    title = col["title"]
    content = get_content(cid)

    col_type = "Autre"
    for rule_fn, type_name in RULES:
        try:
            if rule_fn(cid, title, content):
                col_type = type_name
                break
        except:
            pass

    col["type"] = col_type

# Count types
from collections import Counter
type_counts = Counter(col["type"] for col in collections)
print("\n=== Repartition par type ===")
for t, c in type_counts.most_common():
    print(f"  {t:<30} {c:>3} collections")

# Write the new file with the added column
with open(INPUT_FILE, "w") as f:
    f.write("# NERC NVS - Liste complete des collections (311)\n\n")
    f.write("| # | ID | URI | Titre | Collection Type |\n")
    f.write("|---|-----|-----|-------|-----------------|\n")
    for col in collections:
        f.write(f"| {col['num']} | {col['id']} | {col['uri']} | {col['title']} | {col['type']} |\n")

print(f"\nFichier mis a jour: {INPUT_FILE}")
print(f"Colonne 'Collection Type' ajoutee pour {len(collections)} collections")
