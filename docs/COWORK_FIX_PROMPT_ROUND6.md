ROUND 6 for the report "APFP Grant Portfolio Dashboard" (supersedes round 5)
https://datastudio.google.com/reporting/dba82e50-a6d6-4ef3-a273-ff3b0b827046

The owner decided that values derived per row belong in the pipeline, not in Looker Studio. The pipeline now writes five columns in fct1_grant_portfolio, so five calculated fields can be deleted. Part A does that. Part B repeats the five small round 5 findings. Do not touch anything else (column order, column widths, the 1.12 height and the 4.01 / 4.08 label-block heights stay with the owner). Do not create other fields. Do not export a PDF; the owner does. Do not edit the Data Pipeline sheet, do not run Apps Script, do not change sharing, do not commit anything.

=====================================================================
PART A. USE THE NEW PIPELINE COLUMNS, THEN DELETE FIVE CALCULATED FIELDS
=====================================================================
A0. Resource > Manage added data sources > fct1_grant_portfolio (and "fct1 all years") > Edit > Reconnect / refresh fields > apply. Confirm these fields exist now: grant_period, grant_status_type_amount, sub_category_line, due_window_order, funding_range_order. If one is missing STOP and tell me: the pipeline run is not live yet.
A1. grant_period is text such as "01 Apr 2026 – 31 Mar 2027". If the data source still types it as Date, change its type to Text. grant_status_type_amount is text such as "Active · Restricted · ₹7,50,000". sub_category_line is text such as "Academics · Direct School Support". due_window_order and funding_range_order are numbers (Number, no aggregation shown as a metric: keep them as dimensions / sort fields).
A2. Re-point, then check the values on screen (BrightSteps Learning Trust, FY 26-27):
 - 4.01 GRANT PERIOD cell: field grant_period. It must read "01 Apr 2026 – 31 Mar 2027".
 - 4.01 CURRENT GRANT: ONE cell with field grant_status_type_amount, reading "Active · Restricted · ₹7,50,000" (the mockup shows the amount in the same line). Remove the separate right-aligned amount cell that was added for it, and make the one cell as wide as the other value cells.
 - 4.01 SUB-CATEGORY cell: field sub_category_line, reading "Academics · Direct School Support".
 - 3.05: sort the due window axis by due_window_order ascending (Overdue, 0–30 days, 31–60 days, 61+ days).
 - 2.07: sort the funding range axis by funding_range_order ascending.
A3. Delete the calculated fields txt_grant_period, txt_grant_status_line, txt_sub_category_line, ord_due_window, ord_funding_range (in fct1 and in the all-years copy if they exist there) ONLY after A2 is done and nothing uses them (no chart, sort, filter, control, conditional format, other field). Report the new totals per data source (about 30 different calculated fields remain).

=====================================================================
PART B. THE FIVE SMALL FINDINGS FROM ROUND 5
=====================================================================
B1. WHOLE-NUMBER AXES. 1.06, 1.07 and 3.06 show 0.5, 1.5, 2.5 on the count axis. Decimal places 0 on the axis and on the data labels, no fractional tick (axis minimum 0, maximum automatic; if fractions remain set the tick interval to 1). Then check 1.05, 1.08, 1.10, 1.13, 1.14, 1.16, 2.07 and 3.05: all whole numbers.
B2. 1.09 AXIS shows "1K, 1.5K, 2K". It must show full numbers (500, 1,000, 1,500 ... 3,500): axis number format Number (not Compact), 0 decimals.
B3. 4.04 FILL. The whole row is filled green. Only the Status cell must be filled. Apply the conditional-format rules to the Status column only (Green: fill #3A8969, text #FFFFFF; Amber: fill #D39F3A, text #1E2838; Red: fill #C6695E, text #FFFFFF); Aspect and Indicator have no fill.
B4. 1.13 DATA LABELS. They show counts (4). Show the share as a percentage, 0 decimals; if percent labels are not available on this chart type hide the labels.
B5. SCORECARD LABELS. Scorecards 1.01, 1.03 and 1.04 show raw field names as metric labels. Set "Grantees", "Off-track active grants", "Open support needs". Same for any other metric label that shows a field name.

CHECK (View mode, FY 26-27, defaults): 1.01 = 9; 1.02 = 100%; 1.03 = 0; 1.04 = 8; 3.01 = 6; 3.04 = Rs 58,27,500; 3.05 one bar "61+ days" = 3; 3.06 Defer 3 and Renew 3; 4.02 FY 26-27 | FY 25-26; 4.01 as in A2. Nothing else may change.
REPORT: each item DONE / PARTLY / NOT DONE with one line on what you saw; the field counts after A3. Update claude/looker_build_log.md.
