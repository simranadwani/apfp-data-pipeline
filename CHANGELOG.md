# Changelog

All notable changes to the APFP data pipeline. Newest first.
Each entry lists what changed, which files, and why.

## [0.1.7] — 2026-10-01

### Added — `fct6_grantee_annual_info` (chart 4.02) and `fct5.aspect_display` (chart 4.04)
- **What:**
  - New table `fct6_grantee_annual_info`: one row per grant × metric (annual budget, % funded by
    APFP, team size, attrition, core policies, FCRA registration, foreign contribution share, plus
    a `Financial year` label row). Each row holds the value for the grant's year and for the
    **same organisation's previous year** side by side, as display text (rupees in Indian
    grouping). This is the mockup's 4.02 layout, which Looker Studio cannot build from `fct1`.
  - `fct5_maturity_rag.aspect_display` (new last column): the aspect on the first row of each
    block and blank after it, for the merged-Aspect look of 4.04. `fct5` rows are now ordered
    grant › aspect › indicator.
  - `getSheetIndex` appends rows for new tabs to an older Index tab (existing rows and renamed
    tabs are kept), so the new table needs no manual Index edit.
  - New helpers `previousFinancialYear` and `formatInr`; `buildFct6GranteeAnnualInfo` runs
    after `buildFct5MaturityRag` in `runFinalLayer`, with cardinality tests (31 tests in total).
- **Files:** `Final.js`, `Utilities.js`, `Index.js`, `Pipeline.js`, `Tests.js`,
  `tests/pipeline.test.js`, `tests/column_formats.js`, `tests/generate_table_formats.js`,
  `docs/TABLE_FORMATS.md`, `PIPELINE_LOGIC.md`, `docs/COWORK_FIX_PROMPT.md`, review document.
- **Why:** Product owner approved both after the dashboard review. **After deploying:** run
  `runCompletePipeline`; the new tab `fct6_grantee_annual_info` appears (convert it to a Table
  if you want, like the others) and `fct5` gets its extra column (drag its Table one column wider).

## [0.1.6] — 2026-10-01

### Added — dashboard review and Cowork fix prompt (docs only)
- **What:** Page-by-page comparison of the built Looker Studio dashboard (PDF export) against the
  mockup, with severity and the exact Looker fix per finding, the charts that cannot be copied
  exactly (with workarounds), and a ready-to-paste fix prompt for Cowork. Pipeline validated
  against the live sheets: the 30 Sep run succeeded (Table-safe code) and a local run on the
  1 Oct source gives the same rows and columns, plus the new Support Provided column.
- **Files:** `docs/APFP_Dashboard_Review_and_Cowork_Fixes.docx`, `docs/COWORK_FIX_PROMPT.md`.
- **Why:** Product owner asked for the comparison and feedback for Cowork. No script changes.

## [0.1.5] — 2026-10-01

### Added — "Support Provided" from the source Support tab
- **What:** The source `3. Support` tab has a new column M, **Support Provided** (a dropdown). It
  is now staged (`stg_support.support_provided`) and becomes `fct3_support_activity.response_category`,
  with the value kept exactly as entered. This fills the gap that left dashboard chart 1.15
  (Support Provided to Grantees) empty and gives 4.07 its "APFP response". `response_date`
  stays blank (the source has no date). The new column is the **last column** in `stg_support` and
  `fct3_support_activity`; existing columns keep their positions. The column is required, so a rename is caught by the
  source header check.
  - 4 new tests (26 in total); the test fixture was refreshed from the current source (only the
    Support tab changed).
- **Files:** `Staging.js`, `Final.js`, `tests/pipeline.test.js`,
  `tests/fixtures/source_dummy.json`, `PIPELINE_LOGIC.md`.
- **Why:** Product owner added the column to close the known data gap. **After deploying, run
  `setupSourceHeaderBaseline` once** (otherwise the header audit shows a harmless "New Header
  Added" warning), then `runCompletePipeline`. The dropdown currently holds placeholders
  (`Support 1`, `Support 2`); change them in the source when the real list is final.

## [0.1.4] — 2026-09-30

### Fixed — pipeline failed once the output tabs were converted to Google Sheets Tables
- **What:** The 30 Sep run stopped at `buildStgGrants` with "You can't set the number format of
  cells in a typed column". Every output tab is now a native Table, whose column types own the
  number and date formats, and the writer tried to set one.
  - `writeSheet` no longer sets any number format and no longer clears the whole tab. It writes
    header and rows in one `setValues` (so a Table keeps its columns and types), then removes
    only what a bigger previous run left behind: surplus rows are deleted (blanked if refused),
    surplus columns blanked; a run with no data keeps the header and one blank row.
  - `log` can no longer throw: `appendRow`, else `setValues` on the next free row, else the Apps
    Script log only. A step that succeeded is no longer recorded as an ERROR because logging hiccuped.
  - New `bestEffort` helper for purely cosmetic steps (freeze header, tidy-up).
  - The `yyyy-mm-dd` date formatting added in 0.1.1 is removed; the sheet's Table column types
    (or your own formats) show dates and numbers. New guide `docs/TABLE_FORMATS.md` lists every
    column to format, with the Indian-rupee custom number formats.
  - Harness models Tables (typed columns reject formats, failing `appendRow`); 7 new tests, all
    of which fail on the previous code (22 tests in total). A test keeps the format list in step
    with the real output columns.
- **Files:** `Utilities.js`, `tests/harness.js`, `tests/pipeline.test.js`,
  `tests/column_formats.js`, `tests/generate_table_formats.js`, `docs/TABLE_FORMATS.md`,
  `PIPELINE_LOGIC.md`, `package.json` (`npm run formats`), dashboard spec (prerequisite 4).
- **Why:** The product owner keeps the native Table look for all output tabs; the pipeline must
  work with it. Output values are unchanged.

## [0.1.3] — 2026-09-30

### Added — Looker Studio dashboard build specification and Cowork prompt
- **What:** A self-contained Word specification for building the five-page APFP dashboard in
  Looker Studio (data sources and field IDs, every calculated field, filters, pixel layouts for
  all pages, 39 charts and 12 tiles with exact titles, metrics and display headers, colours and
  fonts from the mockup, Indian-rupee formula, build order and a QA checklist with expected
  values from the current data), the prompt to give Claude Cowork, and a paste-safe text file of
  all formulas.
- **Files:** `docs/APFP_Looker_Dashboard_Build_Spec.docx`, `docs/COWORK_PROMPT.md`,
  `docs/looker_calculated_fields.txt`, `README.md`. No script changes; `.claspignore` already
  keeps `docs/` out of Apps Script.
- **Why:** The dashboard is to be built by Cowork in a browser, which needs the design, filter
  and metric decisions written down in one place. Filters follow the product owner's spec (FY
  shared, other filters per page); the doc records the deviations from the mockup.

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
