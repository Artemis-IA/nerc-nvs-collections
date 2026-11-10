#!/usr/bin/env python3
"""Fusionne les traductions manuelles dans i18n/trans/_global.jsonl.

Usage : python3 i18n/learn.py VOCAB FRAG.jsonl [VOCAB FRAG.jsonl ...]
       python3 i18n/learn.py --scan i18n/frag/

FRAG.jsonl : {"i": <index de ligne dans work/<VOCAB>.todo.jsonl>, "fr": "..."}
(null = sauté). Pour chaque fragment, retrouve (prop, en) dans le todo,
déduit le kind, et ajoute {"k","en","fr"} à _global.jsonl (dédupliqué ;
conflit = avertissement, la nouvelle valeur écrase l'ancienne).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
TRANS = ROOT / "trans"
DB = TRANS / "_global.jsonl"

KIND = {"skos:prefLabel": "label", "skos:altLabel": "label",
        "skos:definition": "definition", "dc:title": "meta",
        "dc:description": "meta"}


def load_db():
    db = {}
    order = []
    if DB.exists():
        for line in DB.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                db[(r["k"], r["en"])] = r["fr"]
                order.append((r["k"], r["en"]))
    return db, order


def learn(vocab: str, frag_path: str):
    todo_file = WORK / f"{vocab}.todo.jsonl"
    if not todo_file.exists():
        print(f"{vocab}: pas de todo — lancer gen_trans.py {vocab}")
        return 0, 0
    todo = [json.loads(l) for l in todo_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    db, order = load_db()
    added = conflicts = skipped = 0
    new_entries = []
    for line in Path(frag_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        i, fr = rec.get("i"), rec.get("fr")
        if fr is None:
            skipped += 1
            continue
        if not (0 <= i < len(todo)):
            print(f"{vocab}: index {i} hors bornes (todo a {len(todo)})")
            continue
        t = todo[i]
        key = (KIND[t["prop"]], t["en"])
        if key in db:
            if db[key] != fr:
                conflicts += 1
                print(f"  CONFLIT {vocab}[{i}] {t['en'][:60]!r}: {db[key]!r} -> {fr!r}")
            else:
                skipped += 1
                continue
        else:
            added += 1
        db[key] = fr
        new_entries.append({"k": key[0], "en": key[1], "fr": fr})
    # réécrit la base complète (dédup + ordre stable)
    seen = set()
    lines = []
    for k, en in order:
        if (k, en) in seen:
            continue
        seen.add((k, en))
        lines.append(json.dumps({"k": k, "en": en, "fr": db[(k, en)]}, ensure_ascii=False))
    for e in new_entries:
        key = (e["k"], e["en"])
        if key not in seen:
            seen.add(key)
            lines.append(json.dumps(e, ensure_ascii=False))
    DB.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{vocab}: +{added} entrées DB ({conflicts} conflits, {skipped} déjà présents/null)")
    return added, conflicts


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--scan":
        frag_dir = Path(args[1]) if len(args) > 1 else ROOT / "frag"
        total = 0
        for frag in sorted(frag_dir.glob("*.jsonl")):
            vocab = frag.name.split(".")[0]
            total += learn(vocab, str(frag))[0]
        print(f"TOTAL +{total} entrées")
    else:
        it = iter(args)
        for vocab, frag in zip(it, it):
            learn(vocab, frag)
