#!/usr/bin/env python3
"""Injecte les traductions françaises @fr dans les fichiers TTL NVS.

Usage : python3 i18n/inject.py VOCAB [VOCAB...]

Lit i18n/trans/<VOCAB>.jsonl : {"i": <index dans i18n/work/<VOCAB>.jsonl>, "fr": "..."}
(work/<VOCAB>.jsonl fournit (prop, en) pour chaque index ; le mapping index->segment
est refait à l'injection, donc aucune ambiguïté de contenu.)

Pour chaque ligne TTL correspondant à un segment traduit, une ligne FR est
insérée juste après la ligne EN :
  - "..."@en ;  ->  "..."@en ;  +  skos:altLabel "..."@fr ;
  - "..."@en .  ->  "..."@en ;  +  skos:altLabel "..."@fr .
Les littéraux EN sont jamais modifiés ; relancer le script est idempotent
(les lignes @fr existantes sont ignorées).
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TTL_DIR = ROOT / "ttl"
WORK_DIR = Path(__file__).resolve().parent / "work"
TRANS_DIR = Path(__file__).resolve().parent / "trans"
TRANS_DIR.mkdir(exist_ok=True)

# même regex que extract.py
LIT_RE = re.compile(
    r'^(\s*)(skos:(?:prefLabel|altLabel|definition|note)|dc:(?:title|description))\s+"((?:[^"\\]|\\.)*)"(@[a-zA-Z-]+)?\s*([;.])(\s*)$'
)
SUBJ_RE = re.compile(r'^<([^>]+)>\s*$')

FR_PRED = {
    "skos:prefLabel": "skos:prefLabel",
    "skos:altLabel": "skos:altLabel",
    "skos:definition": "skos:definition",
    "dc:title": "dc:title",
    "dc:description": "dc:description",
}


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


def escape(s: str) -> str:
    out = []
    for c in s:
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        else:
            out.append(c)
    return "".join(out)


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def load_translations(vocab: str):
    """Retourne {(prop, en): fr} depuis trans/<vocab>.jsonl indexé sur work/<vocab>.jsonl."""
    work = WORK_DIR / f"{vocab}.jsonl"
    trans = TRANS_DIR / f"{vocab}.jsonl"
    if not work.exists():
        sys.exit(f"work/{vocab}.jsonl absent — lancer d'abord extract.py {vocab}")
    segs = [json.loads(l) for l in work.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = {}
    skipped = 0
    n = 0
    for line in trans.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        i, fr = rec.get("i"), rec.get("fr")
        if fr is None:
            skipped += 1
            continue
        if not (0 <= i < len(segs)):
            sys.exit(f"{vocab}: index {i} hors bornes (work a {len(segs)} segments)")
        seg = segs[i]
        out[(seg["prop"], seg["en"])] = fr
        n += 1
    return out, n, skipped, len(segs)


def inject(vocab: str):
    mapping, n_tr, n_skip, n_seg = load_translations(vocab)
    path = TTL_DIR / f"{vocab}.ttl"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out_lines = []
    n_hit = 0
    for line in lines:
        m = LIT_RE.match(line.rstrip("\n"))
        if m and m.group(4) != "@fr":
            indent, prop, raw, _lang, term, trail = m.groups()
            key = (prop, norm(unescape(raw)))
            fr = mapping.get(key)
            if fr is not None and key[0] in FR_PRED:
                # aligne le littéral FR sur la colonne du littéral EN
                quote_col = line.index('"', len(indent) + len(prop))
                pad = max(1, quote_col - len(indent) - len(FR_PRED[key[0]]))
                fr_line = (f'{indent}{FR_PRED[key[0]]}{" " * pad}"{escape(fr)}"@fr '
                           f'{";" if term == ";" else "."}\n')
                if term == ".":
                    # la ligne EN doit céder son point à la ligne FR
                    line = line[: line.rfind(".")] + ";" + line[line.rfind(".") + 1 :]
                out_lines.append(line)
                out_lines.append(fr_line)
                n_hit += 1
                continue
        out_lines.append(line)
    path.write_text("".join(out_lines), encoding="utf-8")
    print(f"{vocab}: {n_hit} lignes FR injectées "
          f"({n_tr} traduites / {n_seg} segments, {n_skip} skippées)")


if __name__ == "__main__":
    for v in sys.argv[1:]:
        inject(v)
