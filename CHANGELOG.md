# Changelog

All notable changes to the APFP data pipeline. Newest first.
Each entry lists what changed, which files, and why.

## [0.1.0] — 2026-09-28

### Added — stg → fct pipeline (Goalkeep Data Pipeline SoP v1.0)
- **What:** Apps Script pipeline that reads the APFP Central Administration workbook and builds
  8 `stg_` tabs and 5 `fct_` tabs (T1–T5 from the dashboard mockup) in the Data Pipeline
  workbook. Includes an Index tab, a Pipeline Log, a Source Header Check gate that stops the run
  on missing/renamed columns (with an email alert), and cardinality tests. No triggers; run
  `runCompletePipeline` from the editor.
- **Files:** `Pipeline.js`, `Index.js`, `Utilities.js`, `Staging.js`, `Final.js`,
  `SourceHeaderCheck.js`, `Tests.js`, `.claspignore`. Removed the placeholder `Code.js`.
- **Why:** First version of the data layer that feeds the Looker Studio dashboard.
