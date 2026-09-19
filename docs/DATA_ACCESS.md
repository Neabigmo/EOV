# Data access

> **No dataset is redistributed with this repository.**
> `data/external/` and `data/processed/` are absent and `.gitignore`d.

The project's own rule (C8, `prereg/amendments/AMENDMENT-008`) is that the
governing license is the license of the **artifact actually ingested** — not the
paper's license, and not a mirror's. Redistribution permission is therefore
decided per dataset, and this release takes the conservative branch everywhere:
nothing is shipped.

`data_registry/PROVENANCE_LEDGER.csv` is the single source of truth: 25 datasets,
each with its official source, license, `analysis_allowed`,
`redistribution_allowed` and the basis for that decision.
`configs/dataset_manifest.csv` is derived from it by
`scripts/make_dataset_manifest.py`.

Of the 25 registered datasets, 9 have `redistribution_allowed = TRUE` and 16 have
`FALSE`. **This release ships none of them**, for two reasons that apply
uniformly: size (gigabytes of raw archives), and the reproducibility principle
that derived data should be regenerated from the official source rather than
trusted from a copy.

## Quick start

```bash
python scripts/fetch_public_data.py --list          # what is available
python scripts/reproduce_phase1.py --check          # what is missing right now
```

Only one stage runs with **zero downloads**: `--stage m7b`, because its two
inputs (`results/tables/M5_TRANSFER_MAP.csv` and
`data/manifests/M6_WU2020_RESULT.json`) are small derived files that *are*
tracked.

## Datasets, in the order the pipeline needs them

| dataset | role | license (ingested artifact) | how to obtain |
|---|---|---|---|
| `Wu2020_H3N2_siteB` | **M6 confirmation** (6 tasks × 576) | **CC-BY-4.0** | auto: `fetch_public_data.py --dataset wu2020` — Springer Source Data, sheet *"Fitness and preference"* |
| `TEM-1CML` | M4/M5 discovery (8 tasks × 55,296) | GPL-3.0 (repo LICENSE) | semi-auto: clone [Gaszek_Yildiz_Meng_2025](https://github.com/msadikyildiz/Gaszek_Yildiz_Meng_2025); needs `data/processed/TEM1-combinatorial-mutagenesis-intended.csv` |
| `Phillips2023_HA_CH65` | M4/M5 discovery (3 tasks × 2¹⁶) | CC-BY-4.0 | manual: eLife [83628](https://doi.org/10.7554/eLife.83628) Source Data |
| `AncSR1_Starr2017` | **failed** structural eligibility | CC0-1.0 | semi-auto: Dryad [10.5061/dryad.jsxksn0hk](https://doi.org/10.5061/dryad.jsxksn0hk) — 184 files / 6.3 GB. The API download route needs a token and the public route is Anubis-PoW protected; a working client ships as `eov/m6_dryad_client.py` |
| `TrpB4_Johnston2024`, `Bank2016_Hsp90_Dryad` | external validation only | CC0-1.0 | manual, see `--list` |

## Expected layout

Fetch scripts place files where the code expects them:

```
data/
├── external/
│   ├── Wu2020_RBS_epistasis/raw/41467_2020_15102_MOESM6_ESM.xlsx
│   ├── TEM1_Gaszek2025/data/processed/TEM1-combinatorial-mutagenesis-intended.csv
│   ├── Phillips2023_HA_CH65/raw/...
│   └── AncSR1_Starr2017/raw/...
├── processed/            # built by the pipeline, not shipped
│   └── M2_measurements.parquet
└── manifests/            # small checksum/provenance files (tracked)
```

`data/processed/M2_measurements.parquet` is the unified measurement table
(schema v1.4, see `prereg/M1_SCHEMA_SPEC.md`). Its sha256 is recorded in
`data/manifests/M2_measurements.parquet.sha256`.

## Licensing notes that matter

* **Never treat a mirror as the source.** `GraphFLA` is a third-party repack;
  `BANK2016_Hsp90_GraphFLA` is registered with `redistribution_allowed = FALSE`
  and must not be re-packaged.
* **Paper license ≠ data license.** `TrpB4_Johnston2024` is a worked example:
  the PNAS article is CC-BY-NC-ND, but the ingested CaltechDATA deposit is CC0-1.0.
* **Two similarly named datasets are genuinely different.** `CTXM14_woson2020`
  and `CTXM14_Palzkill2024` must not be conflated; likewise `Bank2016` appears
  both as an original Dryad deposit and as a GraphFLA repack.
