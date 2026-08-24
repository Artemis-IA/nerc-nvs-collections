#!/usr/bin/env python3
"""Validate all Turtle files in the nvs-turtle directory using rdflib."""
import os
import sys
import time
from rdflib import Graph
from rdflib.exceptions import ParserError

DIR = "/home/imohamma/Documents/Dev/nvs-turtle"
results = {"ok": [], "fail": []}

files = sorted([f for f in os.listdir(DIR) if f.endswith(".ttl")])
total = len(files)
print(f"Validating {total} Turtle files with rdflib...\n")

for i, fname in enumerate(files, 1):
    fpath = os.path.join(DIR, fname)
    size = os.path.getsize(fpath)
    try:
        g = Graph()
        g.parse(fpath, format="turtle")
        triples = len(g)
        results["ok"].append((fname, size, triples))
        status = "OK"
    except Exception as e:
        results["fail"].append((fname, size, str(e)[:200]))
        status = f"FAIL: {str(e)[:100]}"
    # Progress every 50 files
    if i % 50 == 0 or i == total:
        print(f"  [{i}/{total}] ...")

print(f"\n=== RESULTATS ===")
print(f"Valides   : {len(results['ok'])} / {total}")
print(f"Invalides : {len(results['fail'])} / {total}")

if results["fail"]:
    print("\n--- Fichiers invalides ---")
    for fname, size, err in results["fail"]:
        print(f"  {fname} ({size} bytes): {err}")
else:
    print("\nTous les fichiers sont au format Turtle valide!")

# Stats on valid files
if results["ok"]:
    total_triples = sum(t for _, _, t in results["ok"])
    print(f"\n--- Statistiques ---")
    print(f"Total triples RDF: {total_triples:,}")
    print(f"\nTop 10 par nombre de triples:")
    sorted_ok = sorted(results["ok"], key=lambda x: x[2], reverse=True)
    print(f"  {'Fichier':<15} {'Taille':>10} {'Triples':>10}")
    for fname, size, triples in sorted_ok[:10]:
        print(f"  {fname:<15} {size:>10,} {triples:>10,}")
    print(f"\nTop 10 par plus petit nombre de triples:")
    for fname, size, triples in sorted_ok[-10:]:
        print(f"  {fname:<15} {size:>10,} {triples:>10,}")

# Write full report
report_path = os.path.join(DIR, "validation_report.txt")
with open(report_path, "w") as f:
    f.write(f"Rapport de validation Turtle - {total} fichiers\n")
    f.write(f"Valides: {len(results['ok'])} / {total}\n")
    f.write(f"Invalides: {len(results['fail'])} / {total}\n")
    f.write(f"Total triples: {total_triples:,}\n\n")
    f.write("=== Fichiers valides ===\n")
    for fname, size, triples in sorted(results["ok"], key=lambda x: x[0]):
        f.write(f"  {fname}\t{size} bytes\t{triples} triples\n")
    if results["fail"]:
        f.write("\n=== Fichiers invalides ===\n")
        for fname, size, err in results["fail"]:
            f.write(f"  {fname}\t{size} bytes\t{err}\n")
print(f"\nRapport complet: {report_path}")
