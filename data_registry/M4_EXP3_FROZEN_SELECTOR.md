# Exp 3 — S1 模型选择冻结记录

> S1 只用 AMP 族的 leave-one-concentration-out；**AZT 的任何测量在此时不可见**。
> 判据：平均 NR 最小者被选为 Phase-I selector。

| 选择器 | 5 个伪未来任务上的平均 NR |
|---|---|
| current_fitness | 0.7510 |
| neighbor_informative_frac | 0.7580 |
| known_family_worst | 0.7586 |
| proxy_eov_today | 0.7645 |
| local_robustness | 0.7687 |
| known_family_mean | 0.7748 |
| n_better_neighbors | 0.7788 |
| local_ruggedness | 0.7788 |
| dist_to_best | 0.7803 |

**冻结的 Phase-I selector = `current_fitness`**

**冻结的最强 heuristic（S1 口径）= `neighbor_informative_frac`**

S1 的 5 个 holdout：AMP@0.0, AMP@12.2, AMP@195.0, AMP@3.1, AMP@48.8。它们与 `AMP@781.0` 的 CL-5 rho 跨度为 0.0996（AMP@0.0）～0.7585（AMP@48.8），故 S1 不是同任务自比。
