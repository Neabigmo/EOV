# Project history

The milestones are recorded in the order they happened, **including the ones
that ended in a negative result**. This is a deliberate choice: the credibility
of the positive results depends on the reader being able to see that the
confirmatory test was frozen before the data were touched, and that the
confirmatory dataset was selected by a rule written down in advance.

| milestone | question | outcome |
|---|---|---|
| **M0** | Which landscapes exist, and what may we legally use? | 25 datasets registered with per-artifact licenses; `PROVENANCE_LEDGER.csv` |
| **M1** | Schema, measurement states, dataset roles | schema v1.1 → v1.4; four measurement states; `graph_eligible` hard guard |
| **M2** | Build the unified measurement table | 3.4 M rows; independent QC |
| **M3** | Task panels and modality controls | QC + closeout |
| **M4** | Is starting-point value stable across **budgets**? | **YES** — cross-budget ρ = 0.833 / 0.929 / 0.994; four-layer decomposition; TrpB/GB1 external validation reproduced |
| **M5** | Does value transfer across **tasks**? | **Discovery** — transfer is weak (median ρ_rank 0.0599) *and* predictable from landscape similarity (ρ(f1, ρ_rank) = +0.5610; +0.7441 same-drug) |
| **M6** | Confirm M5 on independent data | **CONFIRMED** — ρ = **+0.7536**, CI [+0.2318, +0.9445]; but the first-choice dataset (AncSR1) **failed a phenotype-blind structural audit**, and two later candidates failed on pre-registered gates before Wu2020 was selected |
| **M7** | Can a few measurements replace the full landscape? | **PASS** — `m* = 16` gives ρ̂ = +0.6659; the practical minimum is set by the single-draw 5th percentile (0.079 → 0.401) |
| **M7-B** | Can task metadata replace measurement entirely? | **NO-GO** — ρ_zero = +0.3527, cluster CI [−0.1520, +0.6747], and the lowest-similarity tertile has *exactly* the overall median transfer |

## Why the negative results are kept

* **The AncSR1 audit.** The confirmation dataset originally planned was AncSR1.
  A phenotype-blind structural audit found it has only **2** definable tasks
  (one pair), against a pre-registered requirement of ≥3 tasks and ≥10 pairs.
  Replacing it was authorised **only** for structural ineligibility, and the
  replacement order was written down before the audit ran. Three correction
  findings came out of that audit and are recorded in
  `data_registry/M6_ELIGIBILITY_REPORT.md` — including that an earlier
  project note had mis-described the deposit (20 files vs the actual 184).
* **M7-B's NO-GO.** A metadata-only gate would have been the paper's most
  attractive claim. It failed on its own pre-registered conditions, and the
  failure is informative: it shows the M6/M7 predictor is *not* something one
  could have guessed from task labels — it genuinely requires measuring a little
  of the future.
* **Self-caught protocol flaws.** Three are recorded rather than quietly fixed:
  `AMENDMENT-019` (a degenerate cell rule frozen before any correlation was
  computed), `AMENDMENT-020` §3 (the pre-registered statistic turned out to be
  insensitive to the very variable of interest), and `AMENDMENT-021` §3 (the
  verdict logic originally under-implemented one of its own conditions).

## What the project is *not* claiming

The EOV quantity is **relational**, written `EOV_{B,π}(x | τ)`. The scalar
framing `EOV(x)` was abandoned, and `EOV = R_B − R_0` was abolished outright. The
paper's claim is about a **transferability boundary**, not about a universal
future-value score.

## Milestone documents

Design: `prereg/PHASE1_PROTOCOL.md`, `prereg/PHASE1_DECISION.md`, then
`prereg/amendments/AMENDMENT-001 … 022` in order.
Reports: `data_registry/M4_REPORT.md`, `M5_DISCOVERY_REPORT.md`,
`M6_ELIGIBILITY_REPORT.md`, `M6_CONFIRMATORY_REPORT.md`, `M6_CLOSEOUT.md`,
`M7_REPORT.md`, `M7B_REPORT.md`, `PHASE1_DECISION_REPORT.md`.
Chronology: `data_registry/FREEZE_LEDGER.md` (append-only, 48 batches).
