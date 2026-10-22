TEST on a COPY of the real dashboard: how does Looker Studio behave when a pipeline table is empty, partly blank, or has a placeholder row?

WHY. In the real dashboard, charts on pipeline tables that have no data rows, or columns that are blank in every row, show "Data Set Configuration Error" ("The underlying data has changed. Please notify the data source owner to refresh." or "There was a problem fetching data from the underlying Google Sheet.") instead of "No data" or zero. We need to know which sheet shapes give an error and which give a normal "No data" / blank / zero, so the pipeline can be fixed. You will test this on a COPY of the dashboard that points at a COPY of a sample sheet. The original dashboard and sheets are never touched.

INPUTS
- ORIGINAL REPORT (copy it, never edit it): https://datastudio.google.com/reporting/dba82e50-a6d6-4ef3-a273-ff3b0b827046
- SAMPLE SHEET (the owner gives you the link in the message with this prompt): a Google Sheet that holds the fact tables with sample data in every column. Its tabs are named like the pipeline tabs: fct1_grant_portfolio, fct2_outcome_progress, fct3_support_activity, fct4_budget_year, fct5_maturity_rag, fct6_grantee_annual_info. If one of these tabs is missing or its headers differ from the original data source's fields, STOP and tell the owner which one.

RULES
- Do NOT edit, copy over, move or delete: the original report, the sample sheet itself, the "Data Pipeline" workbook, the "APFP Central Administration" workbook, the Apps Script, any sharing setting. Do not export a PDF. Keep the built-in browser pane visible.
- You may create exactly two new files, both private to the owner (do not change sharing), and you must NOT delete them at the end (report their links):
  (1) a copy of the sample sheet, named "ZZ sample copy (empty-state test)";
  (2) a copy of the report, named "ZZ APFP copy (empty-state test)".
  All edits happen only in these two copies. Also keep a third copy of the sample sheet named "ZZ sample backup (do not edit)" to restore from.
- In the REPORT COPY (and only there) you may use "Edit connection" and "Reconnect" to switch the data sources to the sheet copy. You may press "Refresh fields" to read the preview of Missing / Invalid / Changed fields, but press CANCEL, not Apply, unless a step says otherwise.
- After EVERY change in the sheet copy: open the report copy in View mode, use the three-dot menu > "Refresh data" (or reload twice), and wait about a minute. If a result looks unchanged, refresh once more and say that you did.
- Quote error messages word for word ("See details").

STEP 0. MAKE THE COPIES AND SWITCH THE SOURCES
0.1 Make two copies of the sample sheet (File > Make a copy): "ZZ sample copy (empty-state test)" (work file) and "ZZ sample backup (do not edit)".
0.2 Open the ORIGINAL report, File > Make a copy, name it "ZZ APFP copy (empty-state test)". When asked, choose "Create new data source" for every data source so the copy has its own data sources (the original must stay linked to its own).
0.3 In the report copy: Resource > Manage added data sources. For each of the data sources fct1 (current year), fct1 (all years), fct2, fct3, fct4, fct5, fct6: Edit > change the spreadsheet to "ZZ sample copy (empty-state test)" and the worksheet to the tab of the same name (both fct1 sources use fct1_grant_portfolio), keep "Use first row as headers" ON, and Reconnect. If a dialog lists Missing / Changed fields, write them down and cancel instead of applying, then tell the owner. Also check the blended data source behind 4.02 (fct6 + fct1): after repointing, does it still show both sources?
0.4 List the final mapping you set (data source name, spreadsheet, tab).

STEP 1. BASELINE (full sample data)
Open every page in View mode with the default controls (Financial year FY 26-27, Decision status Pending where present). For each chart id from 1.01 to 4.08 write: shows data / shows 0 or blank / error (with message). Any error with FULL data is itself a finding: report it and do not continue to Step 2 before telling the owner which charts fail.

STEP 2. SCENARIOS (edit tabs only in "ZZ sample copy (empty-state test)"; never touch headers; after each scenario record the affected charts, then RESTORE the tab(s) from "ZZ sample backup (do not edit)" by copying the cell values back, and check that the baseline is back before the next scenario).
Chart to tab map: fct1 -> 1.01 to 1.03, 1.05 to 1.11, 2.05 to 2.07, 3.01 to 3.07, 4.01, 4.08; fct1 all years -> 1.16, 2.08, 4.03, 4.05; fct2 -> 1.12, 4.06; fct3 -> 1.04, 1.14, 1.15, 4.07; fct4 -> 2.01 to 2.04, 2.09 to 2.12; fct5 -> 1.13, 4.04; fct6 -> 4.02.
S1 EMPTY LIKE THE PIPELINE. In fct3_support_activity and fct2_outcome_progress delete every data row so only the header row and one blank second row remain. Charts to read: 1.04, 1.14, 1.15, 4.07 and 1.12, 4.06.
S2 BLANK COLUMNS. In fct1_grant_portfolio clear (all rows, keep the header) proposed_amount, decision_due_date, due_window, due_window_order, funding_range, funding_range_order, recommendation, decision_status. In fct5_maturity_rag clear status and status_order. Charts to read: 3.04, 3.05, 3.06, 3.07, 2.07, 4.08, 1.13, 4.04.
S3 ZERO INSTEAD OF BLANK. From the S2 state, type 0 into every row of the numeric columns only (fct1: proposed_amount, due_window_order, funding_range_order; fct5: status_order). Leave the date and text columns blank. Same charts as S2. Does writing 0 keep the fields alive and remove the error?
S4 PLACEHOLDER ("ANCHOR") ROW ON EMPTY TABLES. Starting again from the baseline: in fct3_support_activity and fct2_outcome_progress delete all data rows and put exactly ONE row in row 2 with these values: financial_year FY 00-00 and previous_financial_year FY 00-00 where such a column exists; every id column (grant_id, organization_id, outcome_id, support_id) the text SCHEMA; every other text column the text n/a; every numeric column 0; every date column 1900-01-01; every true/false column FALSE. Charts to read: the same as S1. With the Financial year control on FY 26-27, do the charts show "No data" or zero instead of the error?
S5 ANCHOR ROW + BLANK COLUMNS. From the baseline: in fct1_grant_portfolio and fct5_maturity_rag clear the same columns as S2, then insert ONE anchor row as row 2 (same rule as S4) so that those columns hold a value only in the anchor row. Charts to read: the same as S2. Do they now work, and do the real rows still show correctly?
S6 STRAY ANCHOR ON ALL-YEARS CHARTS. In fct1_grant_portfolio (all rows kept) add the anchor row. The all-years charts (1.16, 2.08, 4.03, 4.05) ignore the Financial year control: does a "FY 00-00" bar or row appear? Then, in the REPORT COPY only, add a chart-level filter "financial_year Not equal to FY 00-00" to ONE of them (1.16) and say whether the stray bar disappears. Remove that filter again afterwards.
S7 OPTIONAL (only if time allows): convert fct3_support_activity in the sheet copy to a Google Sheets Table (Insert > Table, header row 1) and repeat S1 and S4. Same result?

STEP 3. REPORT
Table: scenario | chart ids affected | for each chart: value shown / "No data" / blank / error with exact text | data source banner (yes/no, text) | Refresh-fields preview (Missing / Invalid / Changed fields, then Cancel) | notes.
Then answer in plain sentences:
1. Which sheet shapes give "Data Set Configuration Error" (S1, S2, S3, S4, S5)? Which give "No data", zero or blank?
2. Does writing 0 instead of blank in numeric columns (S3) fix the charts? Does a blank date or text column still break any chart?
3. Does one anchor row (S4, S5) make the charts show "No data" / zero instead of an error while real rows still show correctly? Which charts, if any, still fail?
4. S6: does the anchor row show as a stray bar or row on the all-years charts, and does a chart filter remove it?
5. Anything that failed even with full data (Step 1), anything you could not test, anything surprising.
Finish by listing the two files you created with their links, and confirm that the original report, the sample sheet, the Data Pipeline workbook and the source workbook were not changed.
