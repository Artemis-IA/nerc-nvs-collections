#!/bin/bash
# Download all NERC NVS collections in Turtle format
# Uses content negotiation: Accept: text/turtle
# Self-contained: queries the NVS SPARQL endpoint to discover all collections
#
# Usage: bash download_nvs_turtle.sh [DEST_DIR]
# Default DEST_DIR: ttl/ subdirectory of the script's location

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="${1:-$SCRIPT_DIR/ttl}"
SPARQL_ENDPOINT="https://vocab.nerc.ac.uk/sparql/sparql"
LOG_FILE="$DEST_DIR/download_log.txt"

mkdir -p "$DEST_DIR"

# Step 1: Query SPARQL endpoint to get all collection URIs
echo "Querying NVS SPARQL endpoint for all collection URIs..."
SPARQL_QUERY="PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?collection ?title WHERE {
  ?collection a skos:Collection .
  OPTIONAL { ?collection dcterms:title ?title }
}
ORDER BY ?collection"

# URL-encode the query and fetch results as JSON
URIS_FILE="$DEST_DIR/.collection_uris.txt"
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$SPARQL_QUERY'''))")

curl -s -L -H "Accept: application/sparql-results+json" \
  "${SPARQL_ENDPOINT}?query=${ENCODED_QUERY}" \
  -o "$DEST_DIR/.sparql_result.json"

# Extract URIs from JSON
python3 -c "
import json
data = json.load(open('$DEST_DIR/.sparql_result.json'))
with open('$URIS_FILE', 'w') as f:
    for b in data['results']['bindings']:
        f.write(b['collection']['value'] + '\n')
print(f'Found {len(data[\"results\"][\"bindings\"])} collections')
"

# Clean up temp SPARQL result
rm -f "$DEST_DIR/.sparql_result.json"

TOTAL=$(wc -l < "$URIS_FILE")
echo "Downloading $TOTAL collections in Turtle format..." | tee "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"

# Step 2: Download each collection in parallel
download_one() {
    local uri="$1"
    local dest_dir="$2"
    # Extract collection ID from URI (e.g., http://vocab.nerc.ac.uk/collection/P01/current/ -> P01)
    local col_id
    col_id=$(echo "$uri" | sed 's|.*/collection/||; s|/current/||')
    local outfile="$dest_dir/${col_id}.ttl"

    curl -s -L -H "Accept: text/turtle" --max-time 120 "$uri" -o "$outfile" 2>/dev/null

    if [ -s "$outfile" ]; then
        local size
        size=$(wc -c < "$outfile")
        echo "OK   $col_id ($size bytes)" >> "$dest_dir/download_log.txt"
    else
        echo "FAIL $col_id (empty or error)" >> "$dest_dir/download_log.txt"
    fi
}

export -f download_one

# Download in parallel (10 at a time)
xargs -a "$URIS_FILE" -I {} -P 10 bash -c 'download_one "$@" "$0"' "$DEST_DIR" {}

# Step 3: Summary
echo "" | tee -a "$LOG_FILE"
echo "Finished at: $(date)" | tee -a "$LOG_FILE"
OK_COUNT=$(grep -c "^OK" "$LOG_FILE" || true)
FAIL_COUNT=$(grep -c "^FAIL" "$LOG_FILE" || true)
echo "Success: $OK_COUNT / $TOTAL" | tee -a "$LOG_FILE"
echo "Failed:  $FAIL_COUNT / $TOTAL" | tee -a "$LOG_FILE"
echo ""
echo "Files downloaded:"
ls -1 "$DEST_DIR"/*.ttl 2>/dev/null | wc -l
echo "Total size:"
du -sh "$DEST_DIR"/*.ttl 2>/dev/null | tail -1

# Clean up temp files
rm -f "$URIS_FILE"
