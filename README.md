# apfp-data-pipeline

Google Apps Script pipeline that turns the **APFP Central Administration** workbook into clean
fact tables in the **Data Pipeline** workbook, for the APFP Looker Studio dashboard.
Built to the Goalkeep *Data Pipeline Build Phase SoP v1.0*.

- **Logic for every table and column:** [PIPELINE_LOGIC.md](PIPELINE_LOGIC.md)
- **History of changes:** [CHANGELOG.md](CHANGELOG.md)
- **Dashboard build spec (Looker Studio):** [docs/APFP_Looker_Dashboard_Build_Spec.docx](docs/APFP_Looker_Dashboard_Build_Spec.docx), with the Cowork prompt in [docs/COWORK_PROMPT.md](docs/COWORK_PROMPT.md) and paste-safe formulas in [docs/looker_calculated_fields.txt](docs/looker_calculated_fields.txt)

## Files

| File | Contains |
|---|---|
| `Pipeline.js` | Spreadsheet IDs, `runCompletePipeline()`, layer runners |
| `Index.js` | `setupIndex()`, `getSheetIndex()`: tab names come from the Index tab |
| `Utilities.js` | `readSheet()`, `writeSheet()`, `key()`, `log()` and other shared helpers |
| `Staging.js` | `buildStg*()`: one per source tab |
| `Final.js` | `buildFct*()`: one per dashboard fact table |
| `SourceHeaderCheck.js` | Source header gate that runs before staging |
| `Tests.js` | `runCardinalityTests()` |
| `tests/` | Local Node tests (not pushed to Apps Script) |

## Workflow

1. Edit code locally.
2. Run the local tests: `npm test` (Node 18+, no dependencies). They run the real pipeline
   against the dummy source data in `tests/fixtures/source_dummy.json`.
3. `clasp push`. `.claspignore` pushes only `*.js` in the root and `appsscript.json`.
4. In the Apps Script editor, run `runCompletePipeline`.
5. Commit, push, and add a CHANGELOG entry.

To refresh the test fixture after the source workbook changes, download it as .xlsx and run
`python3 tests/fixtures/export_source_fixture.py <file.xlsx> tests/fixtures/source_dummy.json`
(needs `openpyxl`).
