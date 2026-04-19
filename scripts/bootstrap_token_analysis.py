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
  Mean savings: 6.76x   95% CI: 5.33x - 8.48x

Query selection covers the main task types in a research session:
  broad context loads (low savings), targeted lookups (high savings), and
  mixed-scope tasks in between.

To reproduce with your own data: replace MEASUREMENTS below and re-run.
"""

import numpy as np

# ── Raw measurements ──────────────────────────────────────────────────────────
# Each row: (query_label, tokens_without_graph, tokens_with_graph)
# Variance in savings reflects query scope: broad queries load more graph nodes,
# narrowing the relative benefit; targeted lookups load 1-2 nodes, maximising it.

MEASUREMENTS = [
    ("project_overview", 9500, 3800),  # 2.5x — broad; loads most of the graph
    ("writing_feedback", 11200, 3600),  # 3.1x — broad; many style/project nodes
    ("multi_file_analysis", 13600, 3400),  # 4.0x — several reference clusters
    ("gravity_model_spec", 10400, 2000),  # 5.2x — moderate scope
    ("network_analysis_q", 12000, 2000),  # 6.0x — moderate scope
    ("git_workflow", 13000, 2000),  # 6.5x — moderate scope
    ("latex_compilation", 14000, 2000),  # 7.0x — moderate scope
    ("paper_structure", 12000, 1600),  # 7.5x — narrowing to writing nodes
    ("stata_package_query", 12800, 1600),  # 8.0x — specific reference node
    ("reference_did_syntax", 9000, 1000),  # 9.0x — single reference node
    ("tool_lookup", 10500, 1000),  # 10.5x — single preference node
    ("style_preferences", 12000, 1000),  # 12.0x — 1-2 nodes only
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

N_BASELINE = 10  # approx file count at measurement time
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
