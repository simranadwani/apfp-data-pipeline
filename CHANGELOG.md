# Changelog

All notable changes to the APFP data pipeline. Newest first.
Each entry lists what changed, which files, and why.

## [0.1.0] — 2026-09-28

### Added — pipeline logic documentation
- **What:** Lineage, a logic table for every column of fct1–fct5, the staging rules, Looker
  Studio calculated-field formulas for the dashboard metrics, and the list of decisions,
  limitations and recommended source fixes. README now covers files and workflow.
- **Files:** `PIPELINE_LOGIC.md`, `README.md`.
- **Why:** SoP section 7 requires the documentation to be written during the build.

### Added — local test suite
- **What:** `npm test` runs the real Apps Script files in Node against in-memory spreadsheets
  seeded with the dummy source data. 10 tests cover row counts, idempotency, every derived
  field rule, the header-check gate and blank-key handling.
- **Files:** `tests/harness.js`, `tests/pipeline.test.js`, `tests/fixtures/source_dummy.json`,
  `tests/fixtures/export_source_fixture.py`, `package.json`.
- **Why:** Apps Script can't run in the cloud dev environment. The tests prove each change
  before `clasp push`. Excluded from Apps Script by `.claspignore`.

### Added — stg → fct pipeline (Goalkeep Data Pipeline SoP v1.0)
- **What:** Apps Script pipeline that reads the APFP Central Administration workbook and builds
  8 `stg_` tabs and 5 `fct_` tabs (T1–T5 from the dashboard mockup) in the Data Pipeline
  workbook. Includes an Index tab, a Pipeline Log, a Source Header Check gate that stops the run
  on missing/renamed columns (with an email alert), and cardinality tests. No triggers; run
  `runCompletePipeline` from the editor.
- **Files:** `Pipeline.js`, `Index.js`, `Utilities.js`, `Staging.js`, `Final.js`,
  `SourceHeaderCheck.js`, `Tests.js`, `.claspignore`. Removed the placeholder `Code.js`.
- **Why:** First version of the data layer that feeds the Looker Studio dashboard.
