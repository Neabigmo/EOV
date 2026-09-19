# AMENDMENT-022 — release redaction and the two document classes

| field | value |
|---|---|
| version | **22** |
| date | 2026-09-19 |
| status | **effective for the public release only** |
| scope | packaging, not science |

---

## 1｜What this amendment does

It records the **redaction pass applied when packaging this repository for public
release**. No threshold, formula, dataset, result or verdict is changed. The
scientific content is byte-identical except for the replacements listed below.

## 2｜Two document classes (the reason there is a split at all)

| class | treatment | why |
|---|---|---|
| **Code** (`eov/*.py`, `scripts/*.py`) | hard-coded machine paths replaced by portable expressions | a hard-coded absolute project path is a functional bug, not just a privacy leak |
| **Documents** (`prereg/**`, `data_registry/**`) | machine-specific path strings replaced; new hashes recorded below | the freeze ledger is **append-only**, so a documented revision extends the chain rather than breaking it |
| **`prereg/M1_SCHEMA_SPEC.md`** | **verbatim, unchanged** | its SHA-256 is asserted by `tests/test_schema_v1_2.py` |
| **`tests/**`** (all test files) | **verbatim, unchanged** | `test_tem1_topology.py` is hash-locked by a tripwire inside `test_schema_v1_2.py`, which is itself hash-locked by `test_schema_v1_4.py`. Rewriting them would require rewriting the very constants that make the tripwires meaningful — a self-referential weakening. |

### 2.1 The consequence, stated plainly

Two historical machine paths therefore survive inside `tests/`, and one survives
in `data_registry/` prose. They are **interpreter/installation paths only**
(conda and a bare Python directory). The release scan confirms **no username, no
credential, no token, no cookie and no personal email** anywhere in the tracked
tree; see `RELEASE_AUDIT.md`.

A conscious trade-off was made in favour of audit integrity. The alternative —
rewriting three chained hash constants — would have silently converted "the
frozen v1.1 asset is byte-identical" into "the frozen asset matches whatever the
release copy says", which is exactly the guarantee the tests exist to provide.

## 3｜Exact replacement rules applied to documents

The literal strings being replaced are deliberately **not reproduced here** —
that would re-introduce the very leak this amendment removes. What follows is an
exact description of each rule; the pre-redaction originals remain available to
the authors in the working copy, and every affected file's pre-redaction SHA-256
is recorded in `data_registry/FREEZE_LEDGER.md`.

| class of literal string replaced | placeholder substituted |
|---|---|
| the project's own absolute path (a drive letter followed by four path segments, in both backslash and forward-slash form) | `<PROJECT_ROOT>` |
| the conda interpreter path used for development (interpreter binary and its environment directory) | `<PYTHON>` / `<PYTHON_ENV>` |
| a local Python 3.14 installation path that is known-broken in this environment | `<PYTHON_BROKEN>` |
| the local Git executable path | `git` (resolved from `PATH`) |

Plus one content removal: the **draft outbound email** in
`data_registry/M0_license_and_novelty.md`, which contained two third-party
correspondence addresses and was a work-process artefact. It is replaced by a
one-line note stating the action that was contemplated. The *scientific* content
of that section — that the AncSR1 blocker was technical rather than legal, and
how the license was verified — is retained in full.

## 4｜Code-level replacements

The project-root constant (previously an absolute literal) is now derived from
`__file__`, in both the `os.path` and `pathlib` idioms. Result tables were
redirected from `data_registry/` to `results/tables/` so that each table has
exactly **one** home in the release, in keeping with the project's rule against
duplicating the same fact in two files.

## 5｜Invariance

| item | changed? |
|---|---|
| every frozen threshold (0.45 / E1=3 / E2=10 / GO 0.45 / COND 0.25) | **no** |
| `V`, `u_τ` (OP-12, no clip), `R_{B,π}`, `R=3`, `search_sim.py` | **no** |
| every result table and every reported number | **no** |
| M4–M7B verdicts | **no** |
| dataset licenses / `redistribution_allowed` | **no** |

## 6｜Verification performed

1. `tests/` shipped byte-identical (sha256 of `test_tem1_topology.py` =
   `537afe9b…`, matching the tripwire constant).
2. `pytest tests` in the packaged tree: **66 passed, 20 skipped**, exit 0.
   In the full-data working tree: **86 passed**.
3. M7-B re-run inside the packaged tree reproduced
   `ρ_zero = +0.3527`, CI `[−0.1520, +0.6747]`, `p = 0.01600`, `NO-GO`.
4. `scripts/verify_release.py`: see `RELEASE_AUDIT.md`.
