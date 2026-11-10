#!/usr/bin/env python3
"""Extrait les segments à traduire des TTL NVS -> i18n/work/<VOCAB>.jsonl

Chaque ligne : {"uri", "prop", "en"} — prop in {prefLabel, altLabel, definition}.
Déduplique les couples (prop, en) identiques dans un même fichier : la traduction
française est par texte source, injectée partout où le texte apparaît.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

TTL_DIR = Path(__file__).resolve().parent.parent / "ttl"
WORK_DIR = Path(__file__).resolve().parent / "work"
WORK_DIR.mkdir(exist_ok=True)

# ligne de propriété littérale : <pred>  "...."[@lang] <;/.>
LIT_RE = re.compile(
    r'^\s*(skos:(?:prefLabel|altLabel|definition|note)|dc:(?:title|description))\s+"((?:[^"\\]|\\.)*)"(@[a-zA-Z-]+)?\s*([;.])'
)
SUBJ_RE = re.compile(r'^<([^>]+)>\s*$')


def unescape(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "n":
                out.append("\n")
            elif n == "t":
                out.append("\t")
            elif n in '"\\/':
                out.append(n)
            elif n == "u" and i + 5 < len(s):
                out.append(chr(int(s[i + 2 : i + 6], 16)))
                i += 4
            else:
                out.append(n)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def extract_file(path: Path):
    """Retourne liste de segments {uri, prop, en} (dédupliqués par fichier)."""
    segments = {}
    current_uri = None
    in_vocab_meta = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SUBJ_RE.match(line)
        if m:
            current_uri = m.group(1)
            in_vocab_meta = "collection/" not in current_uri
            continue
        lm = LIT_RE.match(line)
        if not lm or current_uri is None:
            continue
        prop, raw, lang, _term = lm.groups()
        if prop == "skos:note":
            continue  # statut lifecycle (« accepted »…), pas du contenu
        if lang == "@fr":
            continue  # déjà traduit (re-extraction idempotente)
        if prop in ("skos:prefLabel", "skos:altLabel", "skos:definition"):
            key = (prop, norm(unescape(raw)))
            segments.setdefault(key, {"uri": current_uri, "prop": prop, "en": key[1]})
        elif in_vocab_meta and prop in ("dc:title", "dc:description") and lang == "@en":
            key = (prop, norm(unescape(raw)))
            segments.setdefault(key, {"uri": current_uri, "prop": prop, "en": key[1]})
    return list(segments.values())


KIND = {"skos:prefLabel": "label", "skos:altLabel": "label",
        "skos:definition": "definition", "dc:title": "meta", "dc:description": "meta"}


def extract_all():
    """Toutes les vocabulaires -> 3 fichiers globaux dédupliqués par (kind, en)."""
    seen = {"label": {}, "definition": {}, "meta": {}}
    for f in sorted(TTL_DIR.glob("*.ttl")):
        current_uri = None
        in_vocab_meta = False
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = SUBJ_RE.match(line)
            if m:
                current_uri = m.group(1)
                in_vocab_meta = "collection/" not in current_uri
                continue
            lm = LIT_RE.match(line)
            if not lm or current_uri is None:
                continue
            prop, raw, lang, _t = lm.groups()
            if prop == "skos:note" or lang == "@fr":
                continue
            kind = KIND.get(prop)
            if kind is None:
                continue
            if kind == "meta" and not in_vocab_meta:
                continue
            if kind == "meta" and lang != "@en":
                continue
            en = norm(unescape(raw))
            seen[kind].setdefault(en, {"en": en, "vocabs": set()})["vocabs"].add(f.stem)
    for kind, d in seen.items():
        out = WORK_DIR / f"_all_{kind}s.jsonl"
        with out.open("w", encoding="utf-8") as fh:
            for en, rec in sorted(d.items()):
                fh.write(json.dumps({"en": en, "vocabs": sorted(rec["vocabs"])},
                                    ensure_ascii=False) + "\n")
        print(f"{kind}: {len(d)} uniques -> {out.name}")


def main():
    if sys.argv[1:] == ["--all"]:
        extract_all()
        return
    only = set(sys.argv[1:])
    files = sorted(TTL_DIR.glob("*.ttl"))
    total = 0
    for f in files:
        vocab = f.stem
        if only and vocab not in only:
            continue
        segs = extract_file(f)
        out = WORK_DIR / f"{vocab}.jsonl"
        with out.open("w", encoding="utf-8") as fh:
            for s in segs:
                fh.write(json.dumps(s, ensure_ascii=False) + "\n")
        total += len(segs)
        print(f"{vocab:6} {len(segs):6} segments -> {out.name}")
    print(f"TOTAL {total} segments")


if __name__ == "__main__":
    main()
