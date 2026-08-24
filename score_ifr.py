#!/usr/bin/env python3
"""Score NERC NVS collections by relevance to Ifremer projects (refined)."""
import os
import re

DIR = "/home/imohamma/Documents/Dev/nvs-turtle"

# Keywords with word boundaries and weights
# Grouped by Ifremer project/theme
THEMES = {
    "Ifremer (direct)": {
        "keywords": [r"\bifremer\b", r"\bcoriolis\b", r"\bgenavir\b", r"\bpelgas\b", r"french research institute for"],
        "weight": 10,
    },
    "Argo (Ifremer = DAC Coriolis)": {
        "keywords": [r"\bargo\b"],
        "weight": 5,
    },
    "SeaDataNet": {
        "keywords": [r"\bseadatanet\b"],
        "weight": 4,
    },
    "EMODnet": {
        "keywords": [r"\bemodnet\b"],
        "weight": 4,
    },
    "ICES (partenaire)": {
        "keywords": [r"\bICES\b"],
        "weight": 2,
    },
    "GOOS / OceanOPS": {
        "keywords": [r"\bgoos\b", r"\boceanops\b"],
        "weight": 4,
    },
    "OceanGliders": {
        "keywords": [r"\boceangliders?\b"],
        "weight": 5,
    },
    "GEBCO (bathymetrie)": {
        "keywords": [r"\bgebco\b"],
        "weight": 3,
    },
    "CF / Climate Forecast": {
        "keywords": [r"climate and forecast", r"cf-standard"],
        "weight": 3,
    },
    "MEDIN": {
        "keywords": [r"\bmedin\b"],
        "weight": 2,
    },
    "OSPAR / HELCOM": {
        "keywords": [r"\bospar\b", r"\bhelcom\b"],
        "weight": 2,
    },
    "SensorML / SWE": {
        "keywords": [r"sensorml", r"sensor web enablement"],
        "weight": 2,
    },
}

# Get titles
titles = {}
with open(os.path.join(DIR, "NVS_collections_list.md")) as f:
    for line in f:
        m = re.match(r'\| \d+ \| (\S+) \| http[^|]+ \| (.+?) \|', line)
        if m:
            titles[m.group(1)] = m.group(2).strip()

results = []
files = sorted([f for f in os.listdir(DIR) if f.endswith(".ttl")])

for fname in files:
    col_id = fname.replace(".ttl", "")
    fpath = os.path.join(DIR, fname)
    try:
        with open(fpath, "r", errors="replace") as f:
            content = f.read()
    except:
        continue

    total_score = 0
    theme_scores = {}
    for theme_name, theme_def in THEMES.items():
        theme_score = 0
        for kw in theme_def["keywords"]:
            matches = len(re.findall(kw, content, re.IGNORECASE))
            if matches > 0:
                theme_score += matches * theme_def["weight"]
        if theme_score > 0:
            theme_scores[theme_name] = theme_score
            total_score += theme_score

    if total_score > 0:
        title = titles.get(col_id, "")
        results.append((total_score, col_id, title, theme_scores))

results.sort(key=lambda x: x[0], reverse=True)

print(f"=== Collections NERC NVS les plus liees aux projets Ifremer ===")
print(f"({len(results)} collections pertinentes sur 311)\n")
print(f"{'Score':>6}  {'ID':<8} {'Titre':<58} Themes")
print(f"{'':->6}  {'':->8} {'':->58} {'':->40}")
for score, col_id, title, themes in results[:35]:
    top_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:3]
    th_str = ", ".join(f"{t.split('(')[0].strip()}({s})" for t, s in top_themes)
    print(f"{score:>6}  {col_id:<8} {title[:58]:<58} {th_str}")

# Group by Ifremer project
print(f"\n\n=== CLASSEMENT PAR PROJET IFREMER ===\n")
for theme_name in THEMES:
    themed = [(s, cid, t, th) for s, cid, t, th in results if theme_name in th]
    themed.sort(key=lambda x: x[3][theme_name], reverse=True)
    if themed:
        print(f"--- {theme_name} ({len(themed)} collections) ---")
        for score, col_id, title, themes in themed[:8]:
            print(f"  {col_id:<8} {title[:60]}  [score theme: {themes[theme_name]}]")
        print()
