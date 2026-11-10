#!/usr/bin/env python3
"""Vérifie que les index frag = numéros de ligne du todo (pas le champ i affiché).
Usage: python3 i18n/check_frag.py VOCAB [VOCAB...]"""
import json, sys
from pathlib import Path
W, F = Path("i18n/work"), Path("i18n/frag")
bad = 0
for v in sys.argv[1:]:
    tf, ff = W/f"{v}.todo.jsonl", F/f"{v}.jsonl"
    if not ff.exists(): print(f"{v}: pas de frag"); continue
    todo = [json.loads(l) for l in tf.read_text().splitlines() if l.strip()] if tf.exists() else []
    frag = [json.loads(l) for l in ff.read_text().splitlines() if l.strip()]
    cov = {r.get("i") for r in frag if r.get("fr") is not None}
    miss = [i for i in range(len(todo)) if i not in cov]
    oob = [i for i in cov if not (0 <= i < len(todo))]
    # heuristique forme : définition -> fr trop court, label -> fr phrase
    sus = []
    for r in frag:
        i, fr = r.get("i"), r.get("fr")
        if fr is None or not (0 <= i < len(todo)): continue
        prop = todo[i]["prop"].split(":")[-1]
        if prop == "definition" and len(fr) < 25: sus.append(f"i={i} DEF->court {fr!r}")
        if prop in ("prefLabel","altLabel") and len(fr) > 140 and fr.rstrip().endswith("."): sus.append(f"i={i} {prop}->phrase {fr[:50]!r}")
    flag = "OK" if not (miss or oob or sus) else "A VERIFIER"
    if miss or oob or sus: bad += 1
    print(f"{v}: todo={len(todo)} frag={len(frag)} manquants={miss or '-'} hors-bornes={sorted(oob) or '-'} {flag}")
    for s in sus: print("   ", s)
sys.exit(1 if bad else 0)
