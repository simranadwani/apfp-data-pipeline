INVESTIGATION (no pipeline or source changes) for the report "APFP Grant Portfolio Dashboard"
https://datastudio.google.com/reporting/dba82e50-a6d6-4ef3-a273-ff3b0b827046

WHAT HAPPENED. The pipeline source was switched to the real "APFP Central Administration" workbook on 19 Oct. Several tabs there are still empty, so some pipeline tables have no rows and some columns are blank in every row. After that, some charts show "Data Set Configuration Error" instead of "No data" or a blank. The owner exported APFP_Grant_Portfolio_Dashboard_5.pdf. Your job is to find the EXACT cause of each error and to test the likely cause. Do not guess: quote what Looker Studio tells you.

RULES
- Do NOT edit the Data Pipeline workbook, the source workbook, the Apps Script, sharing, or any chart's configuration, and do not delete fields. Do not export a PDF. Keep the built-in browser pane visible.
- Part A is read-only. Part B (experiments) only changes data source FIELD TYPES and "Refresh fields", and only on the data sources named there; write down every before and after so the owner can undo it. Nothing else.
- Report in the format at the end.

THE CHARTS THAT SHOW THE ERROR (from the owner's PDF; the data source is in brackets)
1.04 tile (fct3), 1.12 chart and its scorecard (fct2), 1.13 (fct5), 1.14 (fct3), 1.15 (fct3), 2.07 (fct1), 3.04 tile (fct1), 3.05 (fct1), 3.07 (fct1), 4.06 (fct2), 4.07 (fct3), 4.08 "Proposed amount" row (fct1).
CHARTS ON THE SAME DATA THAT DO NOT ERROR (use as comparison): 1.01 to 1.03, 1.05 to 1.11, 1.16 (fct1); 2.01 to 2.06, 2.08 (fct4 / fct1 amounts, they show zero); 3.01 to 3.03 and 3.06 (fct1); 4.01 to 4.05 and the text rows of 4.08.

WHAT THE PIPELINE TABLES LOOK LIKE NOW (facts from the live workbook; check them yourself in view mode)
- fct2_outcome_progress and fct3_support_activity have NO data rows (header plus one blank row).
- fct1_grant_portfolio has 36 rows, but these columns are blank in every row: proposed_amount, decision_due_date, due_window, due_window_order, recommendation, decision_type, decision_status, reason_for_recommendation, funding_range, funding_range_order, foreign_contribution_rate, clarity_status, capacity_status, compliance_status, grant_performance_status, grantee_360_link.
- fct5_maturity_rag has 385 rows, but status and status_order are blank in every row.
- fct4_budget_year has 4 rows of zeros (numbers), so no error is expected there.

HYPOTHESES TO CONFIRM OR REJECT
H1. A data source whose tab has zero data rows cannot be read, so every chart on it errors (fct2, fct3).
H2. A column that is blank in every row is typed Text by Looker. A chart or calculated field that uses it as a number or date (SUM, ROUND, FORMAT_DATETIME, numeric sort, "Sort by") becomes invalid and errors, while charts that use only text fields show blank or null (fct1 and fct5).
H3. Something else (a missing or renamed field, a permission or connection problem, a blended data source). Say exactly what.

PART A: READ-ONLY DIAGNOSIS (do all of it before Part B)
A1. For EVERY chart in the error list: click "See details" and copy the full message word for word (it names the cause, for example "Invalid formula", "field not found", "cannot connect"). Also note the chart's data source, metric, dimension, sort field and any chart-level filter or calculated field (name and formula).
A2. For each data source fct1, fct2, fct3, fct5 (Resource > Manage added data sources > Edit): is there a banner or message on the data source itself? Is the connection (spreadsheet, tab, header row, range) still correct? List every field with its Type. Mark each field whose Type is not what it should be: numbers expected for proposed_amount, due_window_order, funding_range_order, foreign_contribution_rate, status_order, target_value, achieved_value, outcome_achievement_pct, final_actual_value, annual_achievement_pct; date expected for decision_due_date and response_date; everything else text.
A3. In the Data Pipeline workbook (view only) open fct2 and fct3: confirm they have only a header and a blank second row. Open fct1 and note the first 3 values of proposed_amount and decision_due_date (blank?).
A4. For each errored chart, say which hypothesis (H1, H2, H3) matches the message, in one line, with the quote.

PART B: EXPERIMENTS (only after A is written down)
B1 (tests H2 on fct1). In the data source fct1 set the Type of proposed_amount to Number, decision_due_date to Date (YYYYMMDD / Date), due_window_order and funding_range_order to Number. Then reload the report in View mode. Which of 3.04, 3.05, 3.07, 4.08 (proposed amount), 2.07 now show a value or "No data" instead of the error? Keep the change if it helps and write it down; revert it if it does not.
B2 (tests H2 on fct5). Same for fct5: status_order Number. Does 1.13 change?
B3 (tests H1 on fct2 and fct3). Add a scratch page named "ZZ scratch" with one Table chart on fct3 (dimension: any one text field) and one on fct2. Do they error? Then in the data source choose "Refresh fields" and look again. Delete the scratch page afterwards.
B4. If an error remains after B1 to B3, report the exact new message.

REPORT (by chart id): chart, exact error text from See details, data source, field or formula named, hypothesis, what B changed, result (fixed / still error / now blank). Then: (1) the list of fields whose Type you changed (before and after); (2) one sentence on whether the errors will disappear when the source tabs are filled and the data sources refreshed; (3) anything you could not check. Do not fix anything beyond Part B.
