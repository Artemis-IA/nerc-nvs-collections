#!/usr/bin/env python3
"""Génère i18n/trans/<VOCAB>.jsonl depuis la base globale i18n/trans/_global.jsonl.

Usage : python3 i18n/gen_trans.py VOCAB [VOCAB...] | --all | --report

Pour chaque work/<VOCAB>.jsonl, émet trans/<VOCAB>.jsonl = {"i","fr"} pour les
segments déjà traduits dans _global.jsonl, et work/<VOCAB>.todo.jsonl listant
les segments restant à traduire manuellement (index, prop, en).
--report : couverture par vocabulaire sans rien écrire.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
TRANS = ROOT / "trans"

KIND = {"skos:prefLabel": "label", "skos:altLabel": "label",
        "skos:definition": "definition", "dc:title": "meta",
        "dc:description": "meta"}


def load_db():
    db = {}
    for line in (TRANS / "_global.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            db[(r["k"], r["en"])] = r["fr"]
    return db


def gen(vocab: str, db: dict, write: bool = True):
    work = WORK / f"{vocab}.jsonl"
    segs = [json.loads(l) for l in work.read_text(encoding="utf-8").splitlines() if l.strip()]
    trans_lines, todo = [], []
    for i, s in enumerate(segs):
        if not s["en"].strip():
            continue  # segment vide -> rien à traduire ni à injecter
        fr = db.get((KIND[s["prop"]], s["en"]))
        if fr is None:
            todo.append({"i": i, "prop": s["prop"], "en": s["en"]})
        else:
            trans_lines.append({"i": i, "fr": fr})
    if write:
        (TRANS / f"{vocab}.jsonl").write_text(
            "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in trans_lines),
            encoding="utf-8")
        (WORK / f"{vocab}.todo.jsonl").write_text(
            "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in todo),
            encoding="utf-8")
    return len(segs), len(trans_lines), len(todo)


def report(db: dict):
    done_vocab = {"P02", "L05", "C77", "OD1"}
    full, partial, empty = [], [], []
    total_todo = 0
    for f in sorted(WORK.glob("*.jsonl")):
        v = f.stem
        if v.startswith("_") or v in done_vocab:
            continue
        n, ok, todo = gen(v, db, write=False)
        total_todo += todo
        if todo == 0 and ok:
            full.append((n, v))
        elif ok == 0:
            empty.append((n, v))
        else:
            partial.append((todo, n, v))
    print(f"COUVERTS ({len(full)}) : {sum(n for n,_ in full)} segs")
    print(f"PARTIELS ({len(partial)}) : {sum(t for t,_,_ in partial)} segs à traduire")
    print(f"VIDES   ({len(empty)}) : {sum(n for n,_ in empty)} segs (rien à faire)")
    print(f"TOTAL à traduire (occurrences) : {total_todo}")
    print("\n=== partiels par ordre de todo ===")
    for todo, n, v in sorted(partial)[:40]:
        print(f"  {v:6} {todo:5}/{n}")
    if len(partial) > 40:
        print(f"  ... et {len(partial)-40} autres")


if __name__ == "__main__":
    args = sys.argv[1:]
    db = load_db()
    if not args or args == ["--report"]:
        report(db)
    elif args == ["--all"]:
        for f in sorted(WORK.glob("*.jsonl")):
            v = f.stem
            if v.startswith("_"):
                continue
            n, ok, todo = gen(v, db)
            print(f"{v:6} {ok:6}/{n} couverts, {todo} à faire")
    else:
        for v in args:
            n, ok, todo = gen(v, db)
            print(f"{v:6} {ok:6}/{n} couverts, {todo} à faire")
