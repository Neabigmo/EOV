# `analyses/` — where the milestone scripts actually live

The M3–M7B analysis scripts are **not** duplicated here. They live in `eov/`
alongside the library, because the whole set shares one flat module namespace
(`from search_sim import …`, `from landscape import …`, `from tis import …`,
40+ import sites in total). Splitting them into a separate directory would mean
rewriting every one of those sites across 30 files whose end-to-end
re-verification requires third-party data that is not shipped — a large amount
of risk for a purely cosmetic gain.

Use this file as the index instead.

## Core library (`eov/`)

| module | what it is |
|---|---|
| `schema.py` | measurement schema v1.1–v1.4: states, censoring evidence, dataset roles, `graph_eligible()` hard guard, validators |
| `landscape.py` | `MixedAlphabetSpace` (product genotype space), `GenotypeGraph`, `MeasurementIndex`, adjacency/degree contracts |
| `search_sim.py` | the **single** implementation of all search policies; `budget_schedule` (OP-1); `utility_from_values` (OP-12) |
| `tis.py` | Today Information Set — structurally incapable of reading future-task keys (L39) |
| `audit_table.py`, `analysis_ready_manifest.py` | QC tables and the analysis-ready manifest |

## Milestone scripts

| milestone | scripts |
|---|---|
| **M3** | `m3_taskpanel_closeout.py` |
| **M4** | `m4_gates.py`, `m4_emit_manifests.py`, `exp1_stability.py`, `exp2_baselines.py`, `exp3_tomorrow_test.py`, `exp4_readiness_vs_eov.py`, `m4_h1_auxiliary.py`, `m4_layer_decomposition.py`, `m4_int1_int3_diagnostic.py`, `m4_exp3_topk_sensitivity.py`, `m4_openparam_sensitivity.py`, `m4_op4_rep_sensitivity.py`, `m4_invariant5_fix.py`, `m4_anchor_audit.py`, `m4_anchor_saturation.py`, `m4_dataset_execution_audit.py`, `m4_dataset_gap_sweep.py`, `m4_verify_report.py` |
| **M5** | `m5_transfer_map.py`, `m5_explain.py` |
| **M6** | `m6_dryad_client.py`, `m6_ancsr1_{fetch,listing,access_probe,structure,eligibility,identity_and_recon}.py`, `m6_{replacement_screen,replacement_detail,moulana_structure,exhaustive_screen}.py`, `m6_wu2020_run.py`, `m6_verify_result.py`, `m6_verify_report.py` |
| **M7** | `m7_sparse_probing.py`, `m7_verify.py` |
| **M7-B** | `m7b_zero_measurement_gate.py`, `m7b_verify.py` |
| **external validation** | `trpb_baseline.py`, `trpb_external_check.py`, `trpb_local_optimum_check.py`, `gb1_external_check.py` |

## Running them

Use the supported entry point rather than calling scripts directly:

```bash
python scripts/reproduce_phase1.py --check
python scripts/reproduce_phase1.py --stage m7b
python scripts/reproduce_phase1.py --stage all
```

It reports which inputs are missing and which `fetch_public_data.py` command
obtains them.
