# License scope

`LICENSE` (MIT) covers **the source code and the documents authored in this
repository only**.

## What that means in practice

| material | covered by MIT? |
|---|---|
| source code (`eov/`, `scripts/`, `tests/`, `figures/`) | yes |
| this project's own documents (`prereg/`, `docs/`, `data_registry/*.md`) | yes |
| derived numeric outputs produced by this project's code (`results/tables/`, `data/manifests/`) | yes |
| **any third-party dataset** | **no** |

## Third-party data

**No third-party dataset is redistributed in this repository.** `data/external/`
is deliberately absent and `.gitignore`d.

Every dataset used by the project keeps its own license, is listed with its
provenance, license and redistribution basis in
`data_registry/PROVENANCE_LEDGER.csv`, and must be obtained from its official
source — see [`../docs/DATA_ACCESS.md`](../docs/DATA_ACCESS.md).

The governing rule (retained from `prereg/amendments/AMENDMENT-008`) is that the
license which counts is that of the **artifact actually ingested**, not the
paper's license and not a mirror's.
