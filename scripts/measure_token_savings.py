#!/usr/bin/env python3
"""
measure_token_savings.py — Real token-savings experiment for second-brain-claude.

Methodology
-----------
We measure token efficiency using the ACTUAL memory files on this machine.

  tokens_without  =  all memory .md files loaded into context (naive approach)
  tokens_with     =  only the files the knowledge graph routes each query to

Token count proxy: characters / 4 (standard GPT-family approximation).
This is conservative — real tokenisation is slightly more efficient for
structured markdown, so actual savings may be slightly higher.

Query-to-file mapping is derived from the graphify community structure
(see graphify-out/GRAPH_REPORT.md): each query is routed to the 1–3 files
in the relevant community hub, matching what the graph would load at runtime.

Run:
    python3 scripts/measure_token_savings.py --memory-dir ~/.claude/projects/YOUR-PROJECT/memory
"""

import argparse
import os
import numpy as np
from pathlib import Path

# ── Token counting ────────────────────────────────────────────────────────────


def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def load_file_tokens(path: Path) -> int:
    try:
        return count_tokens(path.read_text(encoding="utf-8"))
    except Exception:
        return 0


# ── Query definitions ─────────────────────────────────────────────────────────
# Each query maps to the memory files the graph would route it to.
# Community source: graphify-out/GRAPH_REPORT.md (built 2026-04-13).
# Files not listed for a query would NOT be loaded by the graph.

QUERIES = [
    {
        "label": "active_research_projects",
        "query": "What are my active research projects and their current phase?",
        "relevant_files": [
            "user_profile.md",
            "reference_literature_search.md",
            "MEMORY.md",
        ],
        "community": "Research Literature Library + User Context",
    },
    {
        "label": "writing_style_sentence",
        "query": "Help me rewrite this sentence in my academic voice.",
        "relevant_files": ["writing_style_guide.md"],
        "community": "Writing Style Rules",
    },
    {
        "label": "stata_did_packages",
        "query": "Which Stata DiD packages should I use for staggered adoption?",
        "relevant_files": ["reference_stata_did_packages.md"],
        "community": "DiD Staggered Adoption Methods",
    },
    {
        "label": "csdid_syntax",
        "query": "Show me the csdid syntax with event-study plot.",
        "relevant_files": ["reference_stata_did_examples.md"],
        "community": "Callaway-Sant'Anna Implementations",
    },
    {
        "label": "file_storage_locations",
        "query": "Where are my data files and working files stored?",
        "relevant_files": ["user_profile.md", "MEMORY.md"],
        "community": "User Context & Preferences",
    },
    {
        "label": "r_did_vs_stata",
        "query": "Which R DiD packages match my Stata workflow?",
        "relevant_files": [
            "reference_r_did_packages.md",
            "reference_stata_did_packages.md",
        ],
        "community": "R DiD Packages + DiD Staggered Adoption",
    },
    {
        "label": "git_workflow",
        "query": "How do I prefer to handle git commits and pushes?",
        "relevant_files": ["feedback_git_workflow.md"],
        "community": "User Context & Preferences",
    },
    {
        "label": "python_did_packages",
        "query": "What Python DiD packages are available for Callaway-Sant'Anna?",
        "relevant_files": ["reference_python_did_packages.md"],
        "community": "Callaway-Sant'Anna Implementations",
    },
    {
        "label": "stata_visualization",
        "query": "What Stata visualization packages do I have installed?",
        "relevant_files": ["reference_stata_visualization_packages.md"],
        "community": "Stata Visualization Tools",
    },
    {
        "label": "mode_empirical_architecture",
        "query": "How does the /mode empirical architecture work?",
        "relevant_files": ["project_mode_architecture.md"],
        "community": "Claude Code Mode Architecture",
    },
    {
        "label": "tool_stack",
        "query": "What tools and software do I use for my research?",
        "relevant_files": ["user_profile.md"],
        "community": "User Context & Preferences",
    },
    {
        "label": "paper_writing_style",
        "query": "How should I structure my writing style for this economics paper?",
        "relevant_files": ["writing_style_guide.md", "user_profile.md"],
        "community": "Writing Style Rules + User Context",
    },
]

# ── Main experiment ───────────────────────────────────────────────────────────


def run_experiment(memory_dir: Path):
    # Load all files
    all_files = sorted(memory_dir.glob("*.md"))
    all_file_tokens = {f.name: load_file_tokens(f) for f in all_files}
    tokens_all = sum(all_file_tokens.values())

    print(f"\nMemory directory: {memory_dir}")
    print(f"Files found: {len(all_files)}")
    print(f"\nFile token counts (chars/4):")
    print("-" * 45)
    for name, toks in sorted(all_file_tokens.items(), key=lambda x: -x[1]):
        bar = "#" * (toks // 50)
        print(f"  {name:<42} {toks:>4}  {bar}")
    print(f"  {'TOTAL':<42} {tokens_all:>4}")
    print()

    # Per-query measurement
    results = []
    print("Per-query token savings")
    print("-" * 65)
    for q in QUERIES:
        missing = [f for f in q["relevant_files"] if f not in all_file_tokens]
        if missing:
            print(f"  WARNING: {q['label']} — missing files: {missing}")
            continue

        tokens_with = sum(all_file_tokens[f] for f in q["relevant_files"])
        ratio = tokens_all / tokens_with
        n_files = len(q["relevant_files"])
        print(
            f"  {q['label']:<30} {ratio:5.2f}x  "
            f"({n_files} of {len(all_files)} files)  [{q['community']}]"
        )
        results.append(
            {
                "label": q["label"],
                "tokens_without": tokens_all,
                "tokens_with": tokens_with,
                "ratio": ratio,
                "n_files_loaded": n_files,
            }
        )

    print()

    # Bootstrap
    ratios = np.array([r["ratio"] for r in results])
    rng = np.random.default_rng(seed=42)
    n = len(ratios)
    boot_means = np.array(
        [rng.choice(ratios, size=n, replace=True).mean() for _ in range(1_000)]
    )

    mean_ratio = ratios.mean()
    ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])

    print("Bootstrap results (1,000 resamples, seed=42)")
    print("-" * 45)
    print(f"  n queries:        {n}")
    print(f"  Total memory:     {tokens_all} tokens  ({len(all_files)} files)")
    print(f"  Observed mean:    {mean_ratio:.2f}x")
    print(f"  95% CI:           {ci_lo:.2f}x - {ci_hi:.2f}x")
    print()

    # Monthly estimate
    QUERIES_PER_DAY = 5
    DAYS = 30
    total_q = QUERIES_PER_DAY * DAYS
    saved = total_q * (tokens_all - tokens_all / mean_ratio)
    print("Monthly token estimate  (5 queries/day x 30 days)")
    print("-" * 45)
    print(f"  Saved per query:  {tokens_all - tokens_all / mean_ratio:.0f} tokens")
    print(f"  Saved per month:  {saved:,.0f} tokens  (~{saved / 1e6:.2f}M)")

    return mean_ratio, ci_lo, ci_hi, results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--memory-dir",
        default=os.path.expanduser("~/.claude/projects/YOUR-PROJECT/memory"),
    )
    args = parser.parse_args()
    run_experiment(Path(os.path.expanduser(args.memory_dir)))
