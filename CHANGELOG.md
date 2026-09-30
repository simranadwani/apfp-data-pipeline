# Changelog

All notable changes to the APFP data pipeline. Newest first.
Each entry lists what changed, which files, and why.

## [0.1.2] — 2026-09-30

### Added — columns the Looker Studio dashboard needs for its page filters and Grantee 360
- **What:**
  - `grant_status` on `fct2_outcome_progress`, `fct3_support_activity` and `fct5_maturity_rag`
    (joined from `stg_grants`), so the Grant Status filter on Portfolio Overview and
    Grantee 360 reaches every chart, not only the `fct1` ones.
  - `fct2`: `target_text`, `final_actual_value`, `annual_achievement_pct` (final actual ÷
    target) and `latest_notes`, for the Grantee 360 outcome table (target, Q1–Q4, annual, notes).
  - Two new tests (15 in total).
- **Files:** `Final.js`, `tests/pipeline.test.js`, `PIPELINE_LOGIC.md`.
- **Why:** Checking the dashboard filter spec (FY, Thematic Area, Grant Status, Decision
  Status, Organisation) against the pipeline showed these columns were missing. Existing
  columns and row counts are unchanged.

## [0.1.1] — 2026-09-29

### Fixed — dates shifted back by up to a day in stg_/fct_ tabs
- **What:** The first live run wrote `2026-04-01` as `2026-03-31 11:30` in stg_ and
  `2026-03-31 04:30` in fct_. As a result `grant_period` and `as_of_date` were a day early, and
  due windows could be off by a day. `runCompletePipeline` now first aligns the Data Pipeline
  workbook's time zone to the script's (Asia/Kolkata) and logs a WARN when it changes it.
  - Staging reads source dates in the source workbook's own time zone.
  - Every date column is formatted `yyyy-mm-dd` (it was US `mm-dd-yy`).
  - Added 3 tests; one of them fails on the old code.
- **Files:** `Pipeline.js` (`alignTimeZones`), `Staging.js` (`castValue`, `parseDateValue`,
  `stageTable`), `Utilities.js` (`writeSheet`), `tests/harness.js`, `tests/pipeline.test.js`,
  `PIPELINE_LOGIC.md` (§3, §4, §7 notes 10–12).
- **Why:** The Data Pipeline sheet was in a US time zone (UTC−7) while the script runs in
  Asia/Kolkata; Apps Script shifts dates on each write/read when these differ. All non-date
  values in the first run were verified correct against an independent recomputation from the
  live source.

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
