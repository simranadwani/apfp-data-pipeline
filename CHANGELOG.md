# Changelog

All notable changes to the APFP data pipeline. Newest first.
Each entry lists what changed, which files, and why.

## [0.1.12] — 2026-10-03

### Changed — one metric per meaning in Looker Studio; fct5 sort helpers
- **What:**
  - **Pipeline:** `fct5_maturity_rag` gets two helper columns at the end, `aspect_order` (Clarity 1, Capacity 2,
    Compliance 3) and `status_order` (Red 1, Amber 2, Green 3), so the 1.13 legend can sort Red, Amber, Green and
    the calculated field `ord_aspect` is not needed. 34 tests.
  - **Dashboard fields (docs):** the owner found too many metrics, a different one per table. The rule is now
    written down: one metric per meaning, context comes from a chart-level filter, plain sums use the built-in Sum.
    `distinct_grantees`, `distinct_grants` and `distinct_needs` replace about 20 single-purpose counts; the eight fct4
    `n_*` helpers are gone (the `inr_*` formulas hold `SUM(column)` inside); about 35 different calculated fields
    remain instead of about 54. `docs/LOOKER_FIELD_NAMING.md` has the full list, the deleted list and a chart-by-chart
    metric and filter map; `docs/looker_calculated_fields.txt` matches. `docs/COWORK_FIX_PROMPT_ROUND4.md` (new,
    supersedes round 3) re-points every chart first, then deletes the rest. Round 4 also asks for 4.03 as grouped
    Approved / Disbursed columns (no phantom point), 1.13 legend order and the 4.04 status colours.
- **Files:** `Final.js`, `tests/pipeline.test.js`, `tests/column_formats.js`, `docs/TABLE_FORMATS.md`,
  `PIPELINE_LOGIC.md`, `docs/LOOKER_FIELD_NAMING.md`, `docs/looker_calculated_fields.txt`,
  `docs/COWORK_FIX_PROMPT_ROUND4.md`, `docs/COWORK_FIX_PROMPT_ROUND3.md` (marked superseded).
- **Why:** Product owner feedback after the round 3 review. **After deploying:** run `runCompletePipeline` and
  drag the `fct5_maturity_rag` Table two columns wider.

## [0.1.11] — 2026-10-02

### Changed — one financial-year format, `FY 26-27`, in the pipeline and the dashboard (**values change**)
- **What:** Every `financial_year` (and `previous_financial_year`, `decision_for_fy`, `previous_grant_fy`) in every
  `stg_` and `fct_` tab is now written as `FY 26-27` instead of `2026-27`. Staging converts the source's
  `2026-27`, `2026-2027`, `FY 26-27` and the Dividends label `April 25-March 26` (to `FY 25-26`); the source
  tabs are untouched. `nextFinancialYear` / `previousFinancialYear` use the same format (century wrap
  `FY 99-00`). Grant and organisation IDs (they contain `202627`) are unchanged.
  - `fct6_grantee_annual_info`: the "Financial year" row now always names the previous year in
    `previous_value` (for example `FY 25-26`), even when the organisation had no grant that year; other
    rows still show `–`. Filtered by the Financial Year control the table shows exactly the selected
    year and the one before it.
  - 3 new tests, 33 in total (one-format check over every stg/fct tab, helper rules, fct6 by year).
- **Files:** `Staging.js`, `Utilities.js`, `Final.js`, `tests/pipeline.test.js`, `PIPELINE_LOGIC.md`.
- **Why:** Product owner wants `FY 26-27` everywhere (as in the mockup). **Looker Studio:** after the next
  `runCompletePipeline` the Financial Year control default and any filter or colour that names
  `2026-27` must be re-picked as `FY 26-27`; the calculated field `fy_label` is no longer needed.

### Changed — calculated fields named by type; unused fields removed (docs only)
- **What:** `docs/LOOKER_FIELD_NAMING.md` (new) gives the convention (`distinct_`, `sum_`, `max_`, `avg_`, `pct_`,
  `inr_`, `txt_`, `ord_`, `link_`) and the old-to-new map. `docs/looker_calculated_fields.txt` uses the new
  names and no longer lists ten unused fields (`m_committed`, `m_disbursed`, `m_apfp_share`, `m_team_size`,
  `m_attrition`, `m_foreign_share`, `core_policies_text`, `fy_label`, `recommendation_copy`,
  `m_support_grantees`). `docs/COWORK_FIX_PROMPT_ROUND3.md` (new, supersedes round 2) drives the Looker side:
  data refresh, FY switch-over, delete unused fields, rename, uniform controls (240 x 40, fixed slots),
  4.02 following the Financial Year control with five acceptance tests, and the leftovers.
  Column order and widths are left to the owner.
- **Files:** `docs/LOOKER_FIELD_NAMING.md`, `docs/looker_calculated_fields.txt`,
  `docs/COWORK_FIX_PROMPT_ROUND3.md`, `docs/COWORK_FIX_PROMPT_ROUND2.md` (marked superseded),
  `docs/COWORK_PROMPT.md`. The older build spec `.docx` still uses the old names and `2026-27`; the text
  files are the source of truth.
- **Why:** Product owner asked for self-explanatory field names, removal of unused fields and consistency.

## [0.1.10] — 2026-10-02

### Changed — Cowork round 2 prompt rewritten after auditing it against the mockup (docs only)
- **What:** The "final" dashboard export was byte-identical to the previous one, so it showed none of
  round 2's edits; the prompt itself was re-audited against the mockup (re-rendered) and the live data.
  - **Corrected my errors:** the instruction to reword the Guide "Grantee Comparison" line is removed
    (text stays verbatim); series colours now follow the mockup (Disbursed and Close light `#B8D8DD`;
    1.14 Closed `#167C88`, Open `#D6E8EF`; 1.08 `#167C88 / #E16E3F / #67A6AB / #D9E8ED`) instead of my
    earlier values.
  - **Added:** 4.01 grant period (typed as Date by Looker; new field `grant_period_text`), 1.11 column
    order, 1.13 legend order, 3.05 diagnosis checklist and expected result (one "61+ days" bar = 3),
    row numbers and pagination off, table header styles, single-select Financial Year and Organisation,
    4.08 recommendation highlight, 2.05 labels and error bars, 4.03 blank point, field-refresh
    fallback, expected values for FY 2026-27, a hard-refresh/new-filename export instruction and
    the deliberate deviations Cowork must not undo. 42 numbered items.
- **Files:** `docs/COWORK_FIX_PROMPT_ROUND2.md`, `docs/looker_calculated_fields.txt`.
- **Why:** Close every remaining gap in one pass. No pipeline changes.

## [0.1.9] — 2026-10-01

### Added — Cowork round 2 fix prompt (docs only)
- **What:** Review of Cowork's progress export (fixes 1–7 and part of 8 done) and a second
  prompt for the remaining and new findings. Confirms against the live sheet that the pipeline
  update is deployed (`fct6_grantee_annual_info` 144 rows, `fct5.aspect_display`, fct3/stg_support
  last column, last run SUCCESS), so Cowork's "blocked" items only need the Looker Studio data
  source fields refreshed and `fct6` added as a data source.
- **Files:** `docs/COWORK_FIX_PROMPT_ROUND2.md`.
- **Why:** Cowork reported the pipeline "does not look deployed"; 1.15 and 4.07 show a Data Set
  Configuration Error until the fct3 field list is refreshed.

## [0.1.8] — 2026-10-01

### Added — exact `link_360` formula so "Click here" opens a pre-filtered Grantee 360 (docs only)
- **What:** `link_360` now targets the Grantee 360 page and sets the Organisation control through
  its filter parameter (`df232`), with the organisation name encoded as Looker Studio expects
  (double-encoded: space `%2520`, `&` `%2526`). Checked against the URL copied from the live
  report (byte-for-byte for Civic Leadership Forum) and against an independent encoder for all
  18 organisation names plus names with `, / + # ' %`. The Cowork fix prompt (item 7) and the
  review document carry the formula.
- **Files:** `docs/looker_calculated_fields.txt`, `docs/COWORK_FIX_PROMPT.md`,
  `docs/APFP_Dashboard_Review_and_Cowork_Fixes.docx`. No script changes. The older build spec
  `.docx` still shows the placeholder formula; the text file is the source of truth.
- **Why:** Product owner enabled "Enable viewer filters in report link" and supplied the page URL.
  The link breaks if the Organisation control is deleted and recreated (new `df` ID).

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
