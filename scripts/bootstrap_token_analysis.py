#!/usr/bin/env python3
"""
bootstrap_token_analysis.py — Token-savings measurement for second-brain-claude.

Methodology
-----------
For each of 12 representative queries, we measured:
  - tokens_without: tokens consumed loading all memory files into context
  - tokens_with:    tokens consumed when the knowledge graph directs Claude
                    to load only the relevant subset of nodes

We then bootstrapped 1,000 resamples from the 12 per-query ratios to estimate
the mean savings and a 95% confidence interval.

Reported results (README):
  Mean savings: 11.96x   95% CI: 8.61x - 15.34x

Data source: REAL measurements from actual memory files.
Token counts = file size in characters / 4 (standard GPT-family approximation).
tokens_without = all 11 memory files loaded (6,096 tokens total).
tokens_with    = only the files the graph routes each query to.
Query-to-file mapping derived from graphify community structure
(see graphify-out/GRAPH_REPORT.md, built 2026-04-13).

See scripts/measure_token_savings.py for the live version (reads files directly).
"""

import numpy as np

# ── Real measurements (chars/4 token counts from actual memory files) ─────────
# Each row: (query_label, tokens_without_graph, tokens_with_graph)
# tokens_without is always 6096 (all 11 files).
# tokens_with = sum of chars/4 for the files the graph routes to.

MEASUREMENTS = [
    (
        "active_research_projects",
        6096,
        1412,
    ),  # 4.32x — 3 files: user + literature + index
    ("writing_style_sentence", 6096, 613),  # 9.94x — 1 file: writing_style_guide
    ("stata_did_packages", 6096, 525),  # 11.61x — 1 file: reference_stata_did_packages
    ("csdid_syntax", 6096, 521),  # 11.70x — 1 file: reference_stata_did_examples
    ("file_storage_locations", 6096, 823),  # 7.41x — 2 files: MEMORY + user_profile
    (
        "r_did_vs_stata",
        6096,
        2047,
    ),  # 2.98x — 2 files: r_did + stata_did (cross-community)
    ("git_workflow", 6096, 300),  # 20.32x — 1 file: feedback_git_workflow
    (
        "python_did_packages",
        6096,
        328,
    ),  # 18.59x — 1 file: reference_python_did_packages
    (
        "stata_visualization",
        6096,
        433,
    ),  # 14.08x — 1 file: reference_stata_visualization
    (
        "mode_empirical_architecture",
        6096,
        442,
    ),  # 13.79x — 1 file: project_mode_architecture
    ("tool_stack", 6096, 278),  # 21.93x — 1 file: user_profile
    ("paper_writing_style", 6096, 891),  # 6.84x — 2 files: writing_style + user_profile
]

# ── Compute per-query savings ratios ─────────────────────────────────────────

labels = [m[0] for m in MEASUREMENTS]
without = np.array([m[1] for m in MEASUREMENTS], dtype=float)
with_ = np.array([m[2] for m in MEASUREMENTS], dtype=float)
ratios = without / with_

print("Per-query token savings ratios")
print("-" * 44)
for label, w_out, w_in, ratio in zip(labels, without, with_, ratios):
    bar = "#" * int(ratio)
    print(f"  {label:<25} {ratio:5.2f}x  {bar}")
print()

# ── Bootstrap ────────────────────────────────────────────────────────────────

rng = np.random.default_rng(seed=42)
N_BOOTSTRAP = 1_000
n = len(ratios)

boot_means = np.array(
    [rng.choice(ratios, size=n, replace=True).mean() for _ in range(N_BOOTSTRAP)]
)

mean_ratio = ratios.mean()
ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])

print("Bootstrap results (1,000 resamples, seed=42)")
print("-" * 44)
print(f"  n queries:      {n}")
print(f"  Observed mean:  {mean_ratio:.2f}x")
print(f"  95% CI:         {ci_lo:.2f}x - {ci_hi:.2f}x")
print()

# ── Scaling projection ────────────────────────────────────────────────────────
# Naive loading is O(n_files); graph traversal stays bounded by subgraph size.
# Projection: savings(n) = mean_ratio * log(n) / log(n_baseline)

N_BASELINE = 11  # actual file count at measurement time
FILE_COUNTS = [10, 20, 30, 50, 75, 100]

print("Projected savings vs. memory size")
print("-" * 44)
for n_files in FILE_COUNTS:
    projected = mean_ratio * np.log(n_files) / np.log(N_BASELINE)
    print(f"  {n_files:>4} files  ->  {projected:.1f}x")
print()

# ── Monthly token estimate ────────────────────────────────────────────────────

QUERIES_PER_DAY = 5  # adjust to your typical session cadence
DAYS_PER_MONTH = 30
AVG_TOKENS_NAIVE = without.mean()

total_queries = QUERIES_PER_DAY * DAYS_PER_MONTH
tokens_naive_month = total_queries * AVG_TOKENS_NAIVE
tokens_graph_month = tokens_naive_month / mean_ratio
tokens_saved_month = tokens_naive_month - tokens_graph_month

print("Monthly token estimate")
print("-" * 44)
print(f"  Queries / month:      {total_queries:,}")
print(f"  Tokens (naive):       {tokens_naive_month:,.0f}")
print(f"  Tokens (with graph):  {tokens_graph_month:,.0f}")
print(
    f"  Saved:                {tokens_saved_month:,.0f}  (~{tokens_saved_month / 1e6:.2f}M)"
)
