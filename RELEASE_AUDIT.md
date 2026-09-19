# RELEASE_AUDIT.md

Pre-push audit of the public EOV release.
Generated 2026-09-19.

```
remote      https://github.com/Neabigmo/EOV.git   (public, MIT)
commit      the commit that contains this file  (branch main)
            verify:  git log -1 --format=%H
tracked     184 files, 2,791,896 bytes
            (= 2.79 MB decimal / 2.66 MiB)
            verify:  git ls-files | wc -l
largest     654,300 bytes (639.0 KiB)
            results/tables/M4_LAYER_DECOMPOSITION.csv
history     fresh repository — no prior history anywhere
```

> **On hand-copied numbers.** Every figure in this header is measured with
> `git ls-files` against the working tree, and each of them moved while the
> release was being finalised (the file count went 182 → 183 → 184 as files were
> added, including this file itself). Rather than keep overwriting them, the
> commands that reproduce each figure are given above.
>
> The commit hash is deliberately **not** written down: a file cannot contain the
> hash of the commit that contains it, so any literal value here would be
> guaranteed stale. **All sizes are decimal (1 MB = 10⁶ bytes) unless a KiB/MiB
> label is shown.** Silent count drift across documents is a known failure mode
> in this project; §12.1 records what changed and why.

---

## 1. What was kept

| area | contents |
|---|---|
| **Core library** (`eov/`, 50 files) | `schema.py` (measurement schema v1.1–v1.4, roles, `graph_eligible()` guard), `landscape.py` (product space, graph, degree contracts), `search_sim.py` (the single search implementation), `tis.py` (leakage-proof Today Information Set), `audit_table.py`, `analysis_ready_manifest.py` |
| **Milestone analyses** (`eov/`) | all M3–M7B scripts, including every verifier (`m6_verify_result.py`, `m6_verify_report.py`, `m7_verify.py`, `m7b_verify.py`) and the TrpB/GB1 external-validation scripts |
| **Tests** (`tests/`, 6 files) | schema v1.2/v1.4 contracts, TEM-1 topology, search-simulator invariants, TIS bit-exact reproduction, plus `conftest.py` with the data-presence guards |
| **Preregistration** (`prereg/`, 26 files) | `PHASE1_PROTOCOL.md`, `PHASE1_DECISION.md`, `PHASE1_DATA_GATE.md`, `M1_SCHEMA_SPEC.md`, and **all 22 amendments in order** |
| **Provenance & audit chain** (`data_registry/`, 46 files) | `PROVENANCE_LEDGER.csv` (25 datasets), `FREEZE_LEDGER.md` (48 batches, append-only), `DATA_AUDIT.md`, `M4_LEAKAGE_AUDIT.md`, and every milestone report |
| **Result tables** (`results/tables/`, 11 files) | the paper's numeric outputs, each regenerable by the shipped code |
| **Configs** (`configs/`, 15 files) | `phase1_defaults.yaml` (every frozen parameter + the document that froze it), derived `dataset_manifest.csv`, M4 run configs and seeds |
| **Entry points** (`scripts/`, 4 files) | `fetch_public_data.py`, `make_dataset_manifest.py`, `reproduce_phase1.py`, `verify_release.py` |
| **Docs** (`docs/`, 4 files) + `figures/make_figures.py` | methods overview, data access, reproducibility, project history; figure builders |

**Deliberately kept although they are negative or self-critical:** the M6
eligibility failure, the M7-B NO-GO, and three self-caught protocol flaws
(`AMENDMENT-019`, `AMENDMENT-020` §3, `AMENDMENT-021` §3). These are part of the
method's credibility, not work-process noise.

## 2. What was deleted

| class | detail |
|---|---|
| **All third-party data** | `data/external/` — 311 files, **5.47 GB** (TEM-1, Phillips2023, Wu2020, AncSR1, TrpB4/GB1, GraphFLA corpus) |
| **Derived large tables** | `data/processed/*.parquet` — 101 MB (`M2_measurements`, `M3_taskpanel_measurements`) |
| **Search matrices / checkpoints** | all `*.npz` (`M4_EXP1_V`, `M4_EXP2_V`, `M4_EXP3_S1_R`, `M4_INV5_S1_R`, `M6_WU2020_R`, `M7_SPARSE`) |
| **Run logs** | 26 `*.log` / `*_err.log` files in `data_registry/` |
| **Scratch code** | `eov/_bench1.py` |
| **Third-party VCS metadata** | the GraphFLA partial clone under `data/external/` (with its own `.git`) |
| **Work-process artefacts** | the draft outbound email in `M0_license_and_novelty.md` (two third-party addresses); the LaTeX probe output; the Anubis challenge scratch files |
| **Caches** | `__pycache__/`, `.pytest_cache/`, `figures/out/`, `_build_log.json`, `RELEASE_CHECK.json` (all `.gitignore`d) |

**Also removed by consolidation:** 11 result tables initially appeared in **both**
`data_registry/` and `results/tables/`. Each table now has exactly one home, and
`scripts/build_release.py` carries an assertion that fails the build if the two
lists ever overlap again. Verified: **0 duplicate-content groups.**

## 3. Data the user must fetch

`data_registry/PROVENANCE_LEDGER.csv` holds **25 datasets**: **9** with
`redistribution_allowed = TRUE`, **16** with `FALSE`. **This release ships none
of them** — size and the regenerate-from-source principle apply uniformly.

```bash
python scripts/fetch_public_data.py --list
python scripts/reproduce_phase1.py --check
```

| needed for | dataset | official source | auto? |
|---|---|---|---|
| M7-B | — | *(none)* | **runs with zero downloads** |
| M6 | `Wu2020_H3N2_siteB` | Springer Source Data, CC-BY-4.0, 174 KB | ✅ `--dataset wu2020` |
| M4/M5/M7 | `TEM-1CML` | GitHub `Gaszek_Yildiz_Meng_2025`, GPL-3.0 | semi-auto (clone) |
| M4/M5/M7 | `Phillips2023_HA_CH65` | eLife 83628 Source Data, CC-BY-4.0 | manual link |
| audit only | `AncSR1_Starr2017` | Dryad `10.5061/dryad.jsxksn0hk`, CC0-1.0, 184 files / 6.3 GB | semi-auto (PoW client shipped) |
| external validation | `TrpB4_Johnston2024`, `Bank2016_Hsp90_Dryad` | CaltechDATA / Dryad, CC0-1.0 | manual |

Full instructions: `docs/DATA_ACCESS.md`.

## 4. Privacy scan results

`python scripts/verify_release.py` — **VERDICT: PASS** (also re-run inside a clean
clone).

| pattern | hits |
|---|---|
| Windows absolute paths | **0** |
| POSIX home paths (`/Users/…`, `/home/…`) | **0** |
| conda / miniconda paths | **0** |
| email addresses | **0** |
| IPv4 addresses | **0** |
| token-like strings (GitHub / OpenAI / Slack / AWS access-key prefixes) | **0** |
| private-key blocks | **0** |

### 4.1 The one documented exception — and why

**8 occurrences across 2 files** retain historical machine paths:
`tests/test_tem1_topology.py` and `tests/test_schema_v1_2.py` (4 each).

These two files are **shipped byte-identical on purpose.** `test_schema_v1_2.py`
contains a tripwire asserting the SHA-256 of `test_tem1_topology.py`, and
`test_schema_v1_4.py` asserts the SHA-256 of `test_schema_v1_2.py`. Rewriting the
paths would have required rewriting those constants — converting *"the frozen v1.1
asset is byte-identical"* into *"the frozen asset matches whatever the release
copy says"*, i.e. destroying the guarantee the tripwires exist to provide.

The trade-off was made in favour of audit integrity. What is retained is
**interpreter/installation paths only — no username, no credential, no email, no
hostname.** The strings are enumerated in
`prereg/amendments/AMENDMENT-022_release_redaction.md` §3.

**An earlier redaction attempt was caught by exactly this tripwire** (expected
`537afe9b…`, got `495344c9…`), which is why `tests/` is excluded from path
rewriting. `prereg/M1_SCHEMA_SPEC.md` is likewise shipped verbatim.

## 5. Large-file audit (whole history, not just `HEAD`)

```
objects scanned (git rev-list --objects --all)   204
largest single object                            654,300 bytes (639.0 KiB)
objects > 10 MB                                    0
objects > 25 MB                                    0
objects > 50 MB                                    0
working tree, tracked, total                     2.74 MB
```

Because the repository is **newly initialised** (the working analysis tree was
never a git repository), there is no prior history to rewrite and no risk of a
purged-but-still-reachable blob. No `git filter-repo` is required.

## 6. License audit

* **0 tracked files** match `data/external/`, `*.parquet`, `*.npz`, `*.rda`,
  `*.xlsx`, `*.zip`, `*.tar*` or `*.log`. No third-party artifact is redistributed.
* Every tracked file is either first-party source/documentation or a **derived
  numeric output** of first-party code (`results/tables/`, `data/manifests/`).
* `LICENSE` is MIT and explicitly scopes itself to first-party material, naming
  `docs/DATA_ACCESS.md` for third-party terms.
* `configs/dataset_manifest.csv` is generated from the provenance ledger by
  `scripts/make_dataset_manifest.py`, so per-dataset licensing cannot drift.
* Governing rule retained from `AMENDMENT-008`: the license that counts is that
  of the **artifact actually ingested** — not the paper's, not a mirror's.

## 7. Test results

| environment | command | result |
|---|---|---|
| **clean clone, no data** | `pytest tests` | **66 passed, 20 skipped**, exit 0 |
| **full-data working tree** | `pytest tests` | **86 passed**, exit 0 |

The 20 skips are declared in `tests/conftest.py` and are *conditional on data
absence*, so the identical command runs the whole suite once data is present — no
test was deleted or weakened. `conftest.py` also propagates into the subprocess
suites, which is why the frozen-suite regression tests stay green.

## 8. Clean-environment reproduction audit

Cloned to a fresh directory (`git clone` from the local repository, commit
`d66bf7b`) and run with **no third-party data present**:

| check | result |
|---|---|
| `scripts/verify_release.py` | **PASS** |
| `pytest tests` | **66 passed, 20 skipped** |
| `eov/m7b_zero_measurement_gate.py` | **reproduced exactly**: `ρ_zero = +0.3527`, cluster CI `[−0.1520, +0.6747]`, `p_perm = 0.01600`, verdict **NO-GO** |
| `figures/make_figures.py` | built Fig. 3 and Fig. 4 from the shipped tables |
| developer-path grep over the clone | 3 files, all accounted for: the scanner's own patterns + the 2 verbatim test files |

M7-B reproducing **bit-for-bit with zero downloads** is the strongest available
evidence that the packaging did not alter the science: it exercises the library,
the frozen descriptors (`ECFP4 Tanimoto = 0.109756`, year scale 10), the frozen
thresholds, the task-cluster bootstrap and the within-system permutation.

## 9. Known deviations from the suggested layout

1. **`analyses/` holds only an index**, not moved scripts. All 30+ analysis
   scripts stay in `eov/` because the whole set shares one flat module namespace
   (40+ import sites such as `from search_sim import …`). Moving them would mean
   editing every site in files whose full re-verification needs data that is not
   shipped — high risk for a cosmetic gain. `analyses/README.md` is the index.
2. **`figures/` contains a builder, not final artwork.** Fig. 1 is conceptual and
   has no data; Figs. 2–4 are generated from `results/tables/`. Publication
   styling is not applied.
3. **`CITATION.cff` and `LICENSE` contain placeholders** (author, ORCID,
   repository URL, copyright holder). They were deliberately left un-guessed.

## 10. Pre-push checklist — status

- [x] **Placeholders filled.** `LICENSE` copyright holder and `CITATION.cff`
      author / repository URL are set from the target GitHub account
      (`Neabigmo` / 杨一横). And the `main` branch of
      <https://github.com/Neabigmo/EOV> was confirmed **empty** (`git ls-remote`
      exit 0, no refs), so this is a first push with no history to reconcile.
      → Read the two files and change them if the intended copyright holder or
      author list differs.
- [ ] **Decide the `tests/` verbatim exception** from §4.1: keep it, or accept
      rewriting three chained hash constants instead.
- [ ] Optional: on a second machine, run
      `python scripts/fetch_public_data.py --dataset wu2020` and then
      `python scripts/reproduce_phase1.py --stage m6` to confirm the download
      path end-to-end outside the author's environment.
- [ ] Optional: add an ORCID to `CITATION.cff` once available.

## 11. Publication

| item | value |
|---|---|
| remote | `https://github.com/Neabigmo/EOV.git` |
| remote state before push | exists, public, default branch `main`, **no refs** (`git ls-remote` exit 0, empty output) |
| local branch pushed | `main` |
| history | 3 commits, freshly initialised — the working analysis tree was never under version control, so no `git filter-repo` was needed and no purged-but-reachable blob can exist |

## 12. Post-push verification (run against the remote, not the local copy)

A fresh `git clone https://github.com/Neabigmo/EOV.git` into an empty directory:

| check | result |
|---|---|
| local `HEAD` == `origin/main` | **`7d2d6b6` both** |
| tracked files in the clone | **183** |
| `scripts/verify_release.py` | **PASS** |
| `pytest tests` (no third-party data) | **66 passed, 20 skipped**, exit 0 |
| `eov/m7b_zero_measurement_gate.py` | **`ρ_zero = +0.3527`**, CI `[−0.1520, +0.6747]`, `p = 0.01600`, `NO-GO` — identical to the pre-package result |
| `LICENSE` / `CITATION.cff` on GitHub | copyright holder and repository URL present, no placeholders in active fields |

### 12.1 Audit numbers that were wrong on first write, and are now fixed

Four self-inflicted defects, all caught before or shortly after the first push:

1. **File count** — written three times, each correct only for the instant it was
   measured (182 → 183 → 184) because files were still being added, including
   this one. Now paired with the command that reproduces it.
2. **Largest object** — first reported as "639 KB"; the same file is 654.3 KB
   decimal. The two differ only by the divisor (1024 vs 1000) and are now stated
   as **654,300 bytes (639.0 KiB)**.
3. **GitHub license detection** — the first `LICENSE` had a "scope" appendix
   appended to the MIT text, which made GitHub report `NOASSERTION`. The appendix
   moved to `LICENSE-SCOPE.md`; GitHub now reports **MIT**.
4. **Self-referential commit hash** — the header originally named the commit that
   produced the file, which can never be correct for the file's own commit. The
   field now names the *role* of the commit and gives `git log -1 --format=%H`
   instead of a literal.

Items 1–4 are the same failure mode in different clothing: **a value written into
a document that is derived from a moving target.** The fix in each case is to
publish the derivation command alongside the value, or to drop the value.




