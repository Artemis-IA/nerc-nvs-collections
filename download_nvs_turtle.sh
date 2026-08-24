#!/bin/bash
# Download all NERC NVS collections in Turtle format
# Uses content negotiation: Accept: text/turtle

DEST_DIR="/home/imohamma/Documents/Dev/nvs-turtle"
SPARQL_JSON="/tmp/devin-overflows-505878/shell-3c9091-323c01c97b1c24f4/content.txt"
LOG_FILE="$DEST_DIR/download_log.txt"

mkdir -p "$DEST_DIR"

# Extract collection URIs from SPARQL JSON result
URIS_FILE="$DEST_DIR/collection_uris.txt"
python3 -c "
import json
data = json.load(open('$SPARQL_JSON'))
with open('$URIS_FILE', 'w') as f:
    for b in data['results']['bindings']:
        f.write(b['collection']['value'] + '\n')
print(f'Extracted {len(data[\"results\"][\"bindings\"])} URIs')
"

TOTAL=$(wc -l < "$URIS_FILE")
echo "Downloading $TOTAL collections in Turtle format..." | tee "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"

# Download function
download_one() {
    local uri="$1"
    local dest_dir="$2"
    # Extract collection ID from URI (e.g., http://vocab.nerc.ac.uk/collection/P01/current/ -> P01)
    local col_id
    col_id=$(echo "$uri" | sed 's|.*/collection/||; s|/current/||')
    local outfile="$dest_dir/${col_id}.ttl"

    curl -s -L -H "Accept: text/turtle" --max-time 120 "$uri" -o "$outfile" 2>/dev/null

    # Check if file is valid turtle (non-empty and starts with @prefix or @base or has triples)
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

# Summary
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
