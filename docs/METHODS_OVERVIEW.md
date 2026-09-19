# Methods overview

A short, non-normative map of what this repository computes. The **authoritative**
definitions are `prereg/PHASE1_PROTOCOL.md`, `prereg/PHASE1_DECISION.md` and the
amendments; where this file and those disagree, those win.

## 1. The object of study

A **landscape** is a genotype space `X` with a task `τ` mapping `X → ℝ`. A
**parent** `x ∈ X` is a starting point for a budgeted search.

* Search: `R` rounds, budget `B` genotypes total, policy `π ∈ {random, greedy_ssm,
  mlde_ridge}`. `R_{B,π}(x,τ)` is the best value reached. The start is not counted
  against `B` (OP-1).
* Utility: `V_{B,π}(x,τ) = u_τ(R_{B,π}(x,τ))` with

  ```
  u_τ(z) = (z − q05_τ) / (q95_τ − q05_τ)
  ```

  quantiles taken over that task's own informative distribution (OP-12). **No
  clip** — the clip was added by mistake once and removed (`AMENDMENT-013` §1,
  `AMENDMENT-014` §3).
* Because `u_τ` is affine, `scale2max` and OP-12 give **identical Spearman** and
  identical normalised regret; only the empirical-quantile form is nonlinear.

`AdaptationPremium` is reported but is **never** an optimisation target, and the
quantity `EOV = R_B − R_0` is **abolished**.

## 2. Starting-point value is budget-stable

M4 varies `B` with the task fixed. Cross-budget Spearman of the parent ranking is
`0.833 / 0.929 / 0.994` (min / median / max) after the invariant-5 noise
correction. A four-layer decomposition `R_0 / R_k^oracle / R_k^adaptive / R_{B,π}`
separates what the landscape offers from what the policy can reach.

## 3. Starting-point value is task-conditional

The **transfer operator** is

```
T(τ_s → τ_t) = Corr_x[ V(x,τ_s), V(x,τ_t) ]
```

estimated by the pair-level `ρ_rank`: for each `(policy, budget)` cell compute
Spearman between the two tasks' parent-level `V`, then average over admissible
cells. Cross-task transfer is **usually weak** (median `0.0599` in discovery,
`0.0021` in confirmation).

## 4. The boundary is predictable

The task-pair descriptor `f1_landscape_rho` is the Spearman correlation between
the two tasks' values over shared informative genotypes. It predicts `T`:

| milestone | statistic | value |
|---|---|---|
| M5 discovery (TEM-1 + Phillips, 21 pairs) | Spearman(f1, ρ_rank) | +0.5610 |
| M5 discovery, same-drug subgroup (16) | Spearman(f1, ρ_rank) | +0.7441 |
| **M6 confirmation (Wu2020, 15 pairs)** | Spearman(f1, ρ_rank) | **+0.7536**, CI [+0.2318, +0.9445] |

`f1` needs **both** tasks' landscapes, so M6 is explanatory, not prospective.

## 5. From explanatory to prospective similarity

* **M7** — estimate `f1` from only `m` shared genotypes (`m ∈ {4,8,16,32,64,128}`,
  200 random draws each). At the pre-registered `m* = 16`, `ρ̂ = +0.6659`
  (CI [+0.3406, +0.8734]) → **PASS**. The decision-relevant quantity is the
  **single-draw** 5th percentile, which rises from `0.079` at `m=4` to `0.401` at
  `m=16`; hence "≈16 shared measurements".
* **M7-B** — replace the measurement entirely with **task metadata** (drug ECFP4
  fingerprint × dose; strain isolation year). `ρ_zero = +0.3527`, but the
  task-cluster bootstrap CI `[−0.1520, +0.6747]` spans zero and — decisively — the
  lowest-similarity tertile has median `ρ_rank = +0.0407`, identical to the whole
  sample. **NO-GO**: metadata cannot substitute for measuring landscape similarity.

## 6. What is deliberately *not* claimed

* Not "we can predict transferability before observing the future task" — that
  would need M7-B, which failed.
* Not "there is a task-general EOV scalar" — EOV is written
  `EOV_{B,π}(x | τ)`; it is **relational**.
* Not "the ~16-measurement rule is universal" — it rests on 2 systems.

## 7. Statistical hygiene

* Thresholds, `m` grids, descriptors and seeds were frozen **before** the
  corresponding analysis ran (`prereg/amendments/`).
* Uncertainty for pair-level quantities uses **bootstrap over pairs**; for the
  metadata gate it uses **task-cluster bootstrap** plus a **within-system
  permutation** test, because task pairs sharing a task are not independent.
* Every headline number has an automated verifier (`eov/*_verify*.py`).
* Negative results and self-caught protocol flaws are kept, not deleted
  (`AMENDMENT-019`, `AMENDMENT-020` §3, `AMENDMENT-021` §3).
