TEST (own scratch files only): how does Looker Studio behave when a Google Sheet table is empty, partly blank, or has a placeholder row?

WHY. In the real dashboard, charts on pipeline tables that have no data rows, or columns that are blank in every row, show "Data Set Configuration Error" ("The underlying data has changed. Please notify the data source owner to refresh." or "There was a problem fetching data from the underlying Google Sheet.") instead of "No data" or zero. We need to know which sheet shapes give an error and which give a normal "No data" / blank / zero, so the pipeline can be fixed. You will test this on a NEW scratch spreadsheet and a NEW scratch report. Nothing real is touched.

RULES
- Do NOT open for editing, change, copy or delete: the real report "APFP Grant Portfolio Dashboard", the "Data Pipeline" workbook, the "APFP Central Administration" workbook, the Apps Script, any sharing setting. Use only the two NEW files below.
- Create exactly two new files in the owner's Drive: the spreadsheet "ZZ Looker empty-state test" and the Looker Studio report "ZZ Looker empty-state test report". Keep both private (do not change sharing). Do not delete them at the end; report their links.
- Do NOT press "Apply" in any "Refresh fields" dialog. You may press "Refresh fields" only to read the preview and then Cancel. (In the real report Apply would delete fields.) Never press "Reconnect" unless a step says so.
- Do not export a PDF. Report by scenario using the table at the end. Quote error messages word for word.
- To bypass Looker's cache after every change in the sheet, open the report in View mode and use the three-dot menu > "Refresh data" (or reload the page twice). Wait about a minute after editing the sheet; if the result looks unchanged, refresh once more and say so.

STEP 0. BUILD THE SCRATCH SHEET
Spreadsheet "ZZ Looker empty-state test", one tab named "t" (first row = headers, exactly these 7 columns):
financial_year | grant_id | organisation | amount | due_date | sort_order | is_active
Baseline data (rows 2 to 5), every cell filled:
FY 26-27 | G1 | Alpha | 1000 | 2026-12-31 | 1 | TRUE
FY 26-27 | G2 | Beta | 2500 | 2027-01-31 | 2 | FALSE
FY 26-27 | G3 | Gamma | 400 | 2027-02-28 | 3 | TRUE
FY 25-26 | G4 | Delta | 900 | 2026-03-31 | 4 | TRUE
Column types in the sheet: amount and sort_order numbers, due_date a real date (format yyyy-mm-dd), is_active text TRUE/FALSE (plain text, not a checkbox), the others text.
Keep a copy of this baseline in a second tab "baseline" so you can restore it quickly (copy and paste values).

STEP 1. BUILD THE SCRATCH REPORT ON THE BASELINE
New report, add data source: Google Sheets > "ZZ Looker empty-state test" > tab "t", "Use first row as headers" ON, default options. In the data source editor check that the types are: amount Number, sort_order Number, due_date Date (YYYY-MM-DD), the rest Text. Fix a type only if Looker got it wrong, and note it. Add a financial_year dropdown control with default value FY 26-27 (single select).
Page 1 charts (all on this one data source):
C1 Scorecard: Sum of amount.
C2 Scorecard: Record Count with a chart-level filter is_active equals TRUE.
C3 Table: dimensions grant_id, due_date; metric Sum of amount; sort by sort_order ascending.
C4 Bar chart: dimension financial_year, metric Sum of amount. Add a chart-level filter ignoring the control (use the chart setting "Apply filter: off" / "Ignore controls") so it shows all years.
C5 Scorecard with a calculated field named inr_amount = ROUND(SUM(amount), 0).
C6 Table: dimension organisation, metric COUNT_DISTINCT(grant_id), sort by organisation.
Check everything renders with the baseline (C4 shows FY 25-26 and FY 26-27). If not, fix your chart before continuing.

STEP 2. THE SCENARIOS (change ONLY the data in tab "t"; never touch headers; never refresh fields). After each scenario: View mode, refresh data, then record for C1 to C6 exactly what is shown (a number, "No data", blank, or an error with the exact "See details" text). Also open the data source editor (Resource > Manage added data sources > Edit), note any banner on it, press "Refresh fields", write down the Missing / Invalid / Changed fields lists, and press CANCEL.
S0 baseline (control FY 26-27).
S1 EMPTY LIKE THE PIPELINE: delete rows 2 to 5 so only the header row and one blank second row remain.
S2 BLANK COLUMNS: restore the baseline, then clear every cell of the columns amount, due_date and sort_order (rows 2 to 5), keep the text columns filled.
S3 ZERO INSTEAD OF BLANK: from S2, type 0 in every cell of amount and sort_order (rows 2 to 5); leave due_date blank.
S4 ANCHOR ROW ONLY: header plus ONE data row: FY 00-00 | SCHEMA | schema row | 0 | 1900-01-01 | 0 | FALSE. Control stays FY 26-27.
S5 ANCHOR ROW + BLANK COLUMNS: restore the baseline, clear amount, due_date, sort_order in rows 2 to 5, and insert the anchor row from S4 as row 2 (so those three columns have a value only in the anchor row).
S6 ANCHOR VISIBLE ON ALL-YEARS CHART: from S4, look at C4 (all years). Does a bar "FY 00-00" appear? Then add a chart-level filter on C4: financial_year "Not equal to" FY 00-00. Does the bar disappear and does C4 then show "No data" (not an error)?
S7 OPTIONAL, only if you have time: restore the baseline, convert the data range of tab "t" into a Google Sheets Table (Insert > Table, header row 1), then repeat S1 and S2. Same result as without a Table?

STEP 3. REPORT
Fill this table (one row per scenario and chart; you may group charts that behave the same):
scenario | C1 | C2 | C3 | C4 | C5 | C6 | data source banner | Refresh-fields preview (Missing / Invalid / Changed) | notes
Then answer in plain sentences:
1. Which sheet shapes give "Data Set Configuration Error" and which give a normal "No data" / blank / zero? (S1, S2, S3, S4, S5.)
2. In S2, which chart types fail and which survive (scorecard, table, bar, calculated field, sort on a blank numeric column)?
3. Does writing 0 instead of blank in numeric columns (S3) keep the fields alive? Does a blank date column still break?
4. Does one placeholder ("anchor") row (S4, S5) keep the schema intact so that charts show "No data" when the year control excludes it? Does it show a stray bar on an all-years chart, and does the chart-level filter (S6) remove it?
5. Anything you could not test, and anything surprising.
Do not change anything outside the two scratch files.
