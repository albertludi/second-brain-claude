#!/bin/bash
# config.example.sh — copy this to config.sh and fill in your values.
# config.sh is sourced by all scripts. Never commit config.sh.

# Path where Claude Code writes your memory .md files.
# Default: Claude Code global project memory (adjust to your actual project hash).
# Run: ls ~/.claude/projects/ to find your project folder.
MEMORY_DIR="$HOME/.claude/projects/YOUR-PROJECT-HASH/memory"

# Path to your research/knowledge staging folder (for the research graph).
# Create this folder and populate it with papers, notes, etc.
RESEARCH_DIR="$HOME/.claude/graphify-staging/research-knowledge"

# Obsidian vault destinations (where synced graph files are copied).
OBSIDIAN_MEMORY_DEST="$HOME/path/to/your/Obsidian/Graphify/Memory/graphify-out"
OBSIDIAN_RESEARCH_DEST="$HOME/path/to/your/Obsidian/Graphify/Research-Knowledge/graphify-out"

# Python binary inside your graphify virtual environment.
# After installing graphify (pip install graphify), find this with: which python3
GRAPHIFY_PYTHON="$HOME/.graphify-env/bin/python3"

# Absolute path to the claude CLI binary.
# Find with: which claude
CLAUDE_BIN="$HOME/.local/bin/claude"

# Log files
LOG_MEMORY="$HOME/.claude/graphify-auto-rebuild.log"
LOG_RESEARCH="$HOME/.claude/graphify-research-update.log"
