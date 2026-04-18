#!/bin/bash
# graphify_research_update.sh — Weekly research knowledge graph sync to Obsidian.
#
# This script syncs an existing graphify-out from your research staging folder
# to your Obsidian vault. It does NOT rebuild the graph — run /graphify manually
# in Claude Code to rebuild, then this sync will propagate the result.
#
# Schedule (example cron — Sunday 00:30 UTC, 30 min after auto-rebuild):
#   30 0 * * 0 /path/to/graphify_research_update.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config.sh" || { echo "ERROR: config.sh not found."; exit 1; }

SRC="$RESEARCH_DIR/graphify-out"

echo "[$(date)] Starting research graph sync" >> "$LOG_RESEARCH"

if [ ! -d "$RESEARCH_DIR" ]; then
    echo "[$(date)] ERROR: research dir not found: $RESEARCH_DIR" >> "$LOG_RESEARCH"
    exit 1
fi

if [ ! -f "$SRC/GRAPH_REPORT.md" ]; then
    echo "[$(date)] No graph at $SRC — run /graphify on your research folder first" >> "$LOG_RESEARCH"
    exit 0
fi

mkdir -p "$OBSIDIAN_RESEARCH_DEST"
cp "$SRC/GRAPH_REPORT.md" "$OBSIDIAN_RESEARCH_DEST/GRAPH_REPORT.md" && \
cp "$SRC/graph.json"      "$OBSIDIAN_RESEARCH_DEST/graph.json"      && \
cp "$SRC/graph.html"      "$OBSIDIAN_RESEARCH_DEST/graph.html"

if [ $? -eq 0 ]; then
    echo "[$(date)] Done. Synced to Obsidian." >> "$LOG_RESEARCH"
else
    echo "[$(date)] ERROR: copy to Obsidian failed" >> "$LOG_RESEARCH"
    exit 1
fi
