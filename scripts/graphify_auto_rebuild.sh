#!/bin/bash
# graphify_auto_rebuild.sh — Weekly memory graph rebuild + Obsidian sync.
#
# Flow:
#   1. If the rebuild flag exists (set by the Stop hook), run /graphify
#      headlessly via `claude -p` to rebuild the memory knowledge graph.
#   2. On success, remove the flag.
#   3. Mirror graphify-out/ to the Obsidian vault regardless of rebuild outcome.
#
# Schedule (example cron — Sunday 00:00 UTC):
#   0 0 * * 0 /path/to/graphify_auto_rebuild.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config.sh" || { echo "ERROR: config.sh not found. Copy config.example.sh → config.sh and fill in your values."; exit 1; }

FLAG="$HOME/.claude/graphify-needs-rebuild.flag"
SRC="$MEMORY_DIR/graphify-out"

echo "[$(date)] === Auto-rebuild run start ===" >> "$LOG_MEMORY"

# Step 1+2: rebuild only if flagged
if [ -f "$FLAG" ]; then
    echo "[$(date)] Flag present — attempting headless graphify rebuild" >> "$LOG_MEMORY"

    if [ ! -x "$CLAUDE_BIN" ]; then
        echo "[$(date)] WARN: $CLAUDE_BIN not executable — skipping rebuild, run /graphify manually" >> "$LOG_MEMORY"
    else
        "$CLAUDE_BIN" -p "Run /graphify on $MEMORY_DIR to rebuild the memory knowledge graph. After completion, confirm what was updated." --output-format text >> "$LOG_MEMORY" 2>&1
        if [ $? -eq 0 ]; then
            echo "[$(date)] Rebuild succeeded — clearing flag" >> "$LOG_MEMORY"
            rm -f "$FLAG"
        else
            echo "[$(date)] WARN: claude -p failed — leaving flag in place, run /graphify manually" >> "$LOG_MEMORY"
        fi
    fi
else
    echo "[$(date)] No flag — skipping rebuild, syncing existing graph only" >> "$LOG_MEMORY"
fi

# Step 3: sync to Obsidian (always)
if [ ! -f "$SRC/GRAPH_REPORT.md" ]; then
    echo "[$(date)] ERROR: no graph at $SRC — run /graphify in Claude Code first" >> "$LOG_MEMORY"
    exit 1
fi

mkdir -p "$OBSIDIAN_MEMORY_DEST"
cp "$SRC/GRAPH_REPORT.md" "$OBSIDIAN_MEMORY_DEST/GRAPH_REPORT.md" && \
cp "$SRC/graph.json"      "$OBSIDIAN_MEMORY_DEST/graph.json"      && \
cp "$SRC/graph.html"      "$OBSIDIAN_MEMORY_DEST/graph.html"

if [ $? -eq 0 ]; then
    echo "[$(date)] Synced to Obsidian: GRAPH_REPORT.md, graph.json, graph.html" >> "$LOG_MEMORY"
else
    echo "[$(date)] ERROR: copy to Obsidian failed" >> "$LOG_MEMORY"
    exit 1
fi

echo "[$(date)] === Auto-rebuild run done ===" >> "$LOG_MEMORY"
