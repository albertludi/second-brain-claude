# second-brain-claude

A lightweight "second brain" system for [Claude Code](https://claude.ai/code) that gives Claude persistent, relational memory across sessions — without any external services.

## How it works

Three layers:

```
Claude Code session
  → Claude writes memory files (automatic, reactive)

You run /graphify on memory folder (periodic, manual)
  → builds knowledge graph: how memories relate

Sunday cron
  → syncs graph output to Obsidian vault (automatic)

Next session
  → Claude reads both flat memories + relational graph
  → stale-graph reminder fires if new files added since last /graphify
```

**Layer 1 — Memory files**: Claude quietly writes `.md` files during sessions when it learns something worth keeping (preferences, project facts, feedback). These are read at session start.

**Layer 2 — Graphify**: Reads all memory files and builds a knowledge graph showing cross-connections. The output `GRAPH_REPORT.md` is also loaded at session start, giving Claude the relational map, not just isolated facts.

**Layer 3 — Obsidian sync**: Weekly cron copies the graph output to your Obsidian vault so you can browse it visually.

## Requirements

- [Claude Code](https://claude.ai/code) CLI installed
- [graphify](https://github.com/graphify-ai/graphify) installed in a Python virtual env
- Obsidian (optional — for the visual graph browser)
- macOS or Linux (cron-based)

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/second-brain-claude
cd second-brain-claude
chmod +x install.sh
./install.sh
```

The installer will:
1. Ask for your memory folder, Obsidian paths, and binary locations
2. Write a `config.sh` (gitignored — contains your personal paths)
3. Optionally add Sunday cron jobs

## Manual step: add hooks to Claude Code

After running `install.sh`, add the hooks from `hooks/claude-settings-additions.json` to your `~/.claude/settings.json`. These enable:

- **Stop hook**: detects when memory files have changed since the last graph build → sets a flag
- **SessionStart hook**: if flag is set, reminds Claude that the memory graph is stale
- **PreToolUse hook**: when searching files, hints Claude to check `GRAPH_REPORT.md` first

See `hooks/claude-settings-additions.json` for the exact JSON. Replace `YOUR_MEMORY_DIR` with your actual memory folder path.

## First run

After setup, build the initial graph:

1. Open Claude Code in any session
2. Run: `/graphify /path/to/your/memory/folder`
3. Claude builds `graphify-out/graph.json`, `graph.html`, `GRAPH_REPORT.md`

From then on, the Sunday cron syncs the graph to Obsidian, and the Stop hook flags when a rebuild is needed.

## Weekly automation

The cron schedule (set by `install.sh`):

| Time (UTC) | Job |
|---|---|
| Sunday 00:00 | Auto-rebuild: if flagged, run `claude -p` to rebuild graph, then sync to Obsidian |
| Sunday 00:30 | Research graph sync to Obsidian |

> **Note**: The `claude -p` headless rebuild requires Claude Code auth to be valid at cron time. If it fails, the flag stays set and you'll see a reminder at the next session start. Run `/graphify` manually if needed.

## File structure

```
second-brain-claude/
├── install.sh                          # interactive setup
├── config.example.sh                   # template — copy to config.sh
├── config.sh                           # your paths (gitignored)
├── scripts/
│   ├── graphify_auto_rebuild.sh        # weekly rebuild + Obsidian sync
│   └── graphify_research_update.sh     # research graph sync
├── hooks/
│   └── claude-settings-additions.json  # hook config for settings.json
├── LICENSE                             # MIT
└── README.md
```

## How memory files work

Claude Code has a built-in auto-memory system. When Claude learns something during a session — a preference, a project fact, feedback — it writes a small `.md` file to your project's memory folder. You don't need to do anything. The memory folder is typically at:

```
~/.claude/projects/YOUR-PROJECT-HASH/memory/
```

To find it: `ls ~/.claude/projects/`

## MEMORY.md index

The memory folder should contain a `MEMORY.md` index file that Claude reads to know which files to load. After running `/graphify`, add an entry for `graphify-out/GRAPH_REPORT.md` so Claude also reads the relational synthesis:

```markdown
| [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md) | reference | Relational graph of all memory files — community hubs, cross-connections. Rebuild via `/graphify`. |
```

## License

MIT
