ROUND 4 for the report "APFP Grant Portfolio Dashboard" (supersedes rounds 1 to 3)
https://datastudio.google.com/reporting/dba82e50-a6d6-4ef3-a273-ff3b0b827046

I reviewed the PDF the owner exported after round 3. Good work: FY reads "FY 26-27" everywhere, controls are one size and aligned, 4.02 follows the Financial Year control, 3.05 / 3.06 / 3.07, 4.05, the 2.0x colours and labels, the Guide links and the Click here links all look right. Do not redo them.

THE OWNER'S FEEDBACK THIS ROUND: "A lot of metrics have been created. A different metric was created for each table, while wherever possible the same metric should have been used." This round is mainly about fixing that.

RULES (unchanged)
- Do NOT edit the Data Pipeline sheet or the mockup sheet, do NOT run Apps Script, do NOT change sharing, do NOT commit to the repository. Font Raleway. Keep the built-in browser pane visible.
- OUT OF SCOPE (the owner does these by hand): column order and column widths of any table, the height of the 1.12 card and moving the sections below it, the height of the 4.01 / 4.08 label blocks, the "(1)" badge on single-select controls, bold table headers. Do not change them.
- Do NOT export a PDF; the owner does. Report by item number: DONE / PARTLY / NOT DONE and one line on what you saw.

=====================================================================
STEP 0. REFRESH DATA
=====================================================================
The pipeline was re-run: fct5_maturity_rag has two NEW last columns, aspect_order and status_order.
0.1 Resource > Manage added data sources > fct5_maturity_rag > Edit > Reconnect / refresh fields > apply. Confirm aspect_order and status_order (numbers) are in the field list. If they are missing, STOP and tell me: the pipeline run is not live yet.

=====================================================================
STEP 1. THE RULE: ONE METRIC PER MEANING
=====================================================================
1. The same thing is counted by the SAME field everywhere. Do not create a field per chart or per table.
2. The context ("active", "pending", "open", "Education") is a CHART-LEVEL FILTER on the chart or scorecard, not a new calculated field.
3. A plain sum or maximum of a column needs NO calculated field: use the column with the built-in Sum / Max aggregation and rename it in the chart.
4. A calculated field exists only for ratios, rupee text (Indian digit grouping), multi-term formulas and sort helpers.
The complete target list is below. The formulas are in docs/looker_calculated_fields.txt (the field name is the heading of each block).

TARGET FIELDS TO KEEP (calculated)
fct1_grant_portfolio: distinct_grantees; distinct_grants; pct_active_grants_on_track; pct_outcomes_achieved; avg_cost_per_beneficiary; sum_approved_lakh; sum_committed_lakh; sum_disbursed_lakh; inr_annual_budget; inr_approved; inr_cost_per_beneficiary; inr_proposed; txt_due_date; txt_grant_period; txt_grant_status_line; txt_sub_category_line; link_annual_report; link_grantee_360; ord_due_window; ord_funding_range.
fct1 "all years" copy: only distinct_grantees, sum_approved_lakh, sum_committed_lakh, sum_disbursed_lakh, avg_cost_per_beneficiary, inr_cost_per_beneficiary (whatever its charts 1.16, 2.08, 4.03, 4.05 use), nothing else.
fct2_outcome_progress: pct_outcomes_on_track; txt_status_q1, txt_status_q2, txt_status_q3, txt_status_q4.
fct3_support_activity: distinct_needs.
fct4_budget_year: inr_available, inr_dividends, inr_carry_forward, inr_committed_total, inr_committed_current, inr_next_q1, inr_disbursed, inr_unallocated (each with SUM(column) written inside the formula).
fct5_maturity_rag: distinct_grantees (same name and formula as in fct1).
fct6_grantee_annual_info: none.
Everything else is deleted (step 3).

=====================================================================
STEP 2. RE-POINT EVERY CHART AND TILE TO THE CORE METRICS (do this BEFORE deleting)
=====================================================================
For each row: set the chart's metric to the field shown, add the chart-level filters shown (flags are text TRUE / FALSE, use "equals TRUE"), keep the chart's own display name for the metric. After re-pointing, the value on screen must not change (check against the value in brackets for FY 26-27).
1.01 Grantees (9): distinct_grantees + is_active_grant = TRUE
1.02 On track (100%): pct_active_grants_on_track
1.03 Off-track active grants (0): distinct_grants + is_off_track_active_grant = TRUE
1.04 Open support needs (8): distinct_needs (fct3) + is_open_support_need = TRUE
1.05, 1.06: distinct_grants + is_active_grant = TRUE
1.07: distinct_grantees + is_active_grant = TRUE
1.08: distinct_grantees + thematic_area = Education
1.09: built-in Sum of primary_beneficiary_count
1.10: distinct_grantees
1.11: inr_annual_budget, inr_approved, built-in Sum of primary_beneficiary_count, inr_cost_per_beneficiary (do not touch column order)
1.12 scorecard: pct_outcomes_on_track
1.13: distinct_grantees (fct5) + status is one of Red, Amber, Green
1.14: distinct_needs
1.15: distinct_needs + response_category is not empty
1.16 (all years): distinct_grantees + is_active_grant = TRUE
2.05, 2.06, 2.08: sum_committed_lakh, sum_disbursed_lakh
2.07: distinct_grantees + is_funded_grantee = TRUE + funding_range is not empty
2.01 to 2.04, 2.09 to 2.12: the fct4 inr_* fields (unchanged)
3.01 (6): distinct_grants + is_pending_decision = TRUE
3.02 (0): distinct_grants + is_overdue_decision = TRUE
3.03 (0): distinct_grants + is_due_within_30_days = TRUE
3.04 (₹58,27,500): inr_proposed + is_pending_decision = TRUE + recommendation = Renew
3.05: distinct_grants + is_pending_decision = TRUE + recommendation in (Renew, Close) (existing filters stay)
3.06: distinct_grants + is_pending_decision = TRUE
3.07: pct_outcomes_achieved, inr_proposed
4.03: see step 4
4.05: built-in Sum of primary_beneficiary_count and inr_cost_per_beneficiary
4.06: Q1 to Q4 = txt_status_q1 to txt_status_q4; Annual = built-in Max of annual_achievement_pct formatted as percent, 0 decimals; Notes = the column latest_notes (delete your notes_last field)
4.07, 4.04, 4.02: no calculated metrics

=====================================================================
STEP 3. DELETE EVERY OTHER CALCULATED FIELD
=====================================================================
In every data source (fct1, fct1 all years, fct2, fct3, fct4, fct5, any blend) delete each calculated field that is not in the keep list of step 1. Known ones: distinct_active_orgs, distinct_active_grants, distinct_on_track_grants, distinct_off_track_grants, distinct_funded_grantees, distinct_pending_grants, distinct_overdue_grants, distinct_due_30_days_grants, sum_beneficiaries, sum_approved, sum_proposed, max_annual_budget, sum_proposed_renewal, sum_disbursed_lakh_if_different, distinct_latest_outcomes, distinct_latest_outcomes_on_track, pct_annual_achievement, notes_last / txt_notes_last, distinct_open_needs, distinct_responses, distinct_assessed_grantees, inr_proposed_renewal, ord_aspect, the eight fct4 sum_* (or n_*) helper fields, and any field with the old m_ / n_ names, plus every row-level or duplicate field you created yourself (for example a second rupee-text field with the same formula as an inr_ field, a status / type / amount helper that duplicates txt_grant_status_line, grant_period_text now named txt_grant_period).
Delete in this order so nothing breaks: charts first (step 2 is done), then fields that other fields use last. Delete a field only when no chart, filter, sort, conditional format, control or other field still uses it; if one does, re-point that use first.
The fct4 inr_* formulas and the three ratio formulas must be the versions in docs/looker_calculated_fields.txt (they write SUM(column) inside, so they do not need the helper fields). Update each from that file, then delete the helpers.
If a kept field is missing a rename: use the convention distinct_ / sum_ / avg_ / pct_ / inr_ / txt_ / ord_ / link_.
After this step the report should have about 35 different calculated fields (about 12 of them text, link or sort helpers), plus the few copies in the all-years source. Count them and report the number per data source.

=====================================================================
STEP 4. 4.03 AND THE OTHER LEFTOVERS
=====================================================================
4.1 4.03 Funding history: replace "Approved columns + Disbursed line" by two grouped columns on one axis: Approved (sum_approved_lakh) #167C88 and Disbursed (sum_disbursed_lakh) #B8D8DD, data labels on, legend on, axis title "₹ lakh" if the auto title is too long (otherwise leave it). No line series, so the phantom point at 0 disappears.
4.2 1.13 legend order: Red, Amber, Green. Sort the breakdown dimension (status) by status_order ascending (the new fct5 column; use it as the sort field of the breakdown) and the bars (aspect) by aspect_order ascending (Clarity, Capacity, Compliance). Delete the old ord_aspect. Data labels as percent. A single colour per bar is correct for the sample data (each aspect has one rating).
4.3 4.04 Status cells show plain text ("Red", "Green") with no fill in the exported PDF although the rules exist. In View mode (not Edit preview) check; if there is no fill, rebuild the rule: Style > Conditional formatting on the Status column itself, rules: Status equals Green: fill #3A8969 text #FFFFFF; equals Amber: fill #D39F3A text #1E2838; equals Red: fill #C6695E text #FFFFFF; compare with the working RAG rules on 1.11 and copy their settings. The table must use dimension aspect_display (not aspect), indicator, status.
4.4 Everything in rounds 1 to 3 that is not listed in this prompt: leave as it is.

=====================================================================
STEP 5. CHECK AND REPORT
=====================================================================
5.1 View mode, FY 26-27, default filters: these must be exactly the same as before: 1.01 = 9; 1.02 = 100%; 1.03 = 0; 1.04 = 8; 2.01 ₹52,50,000; 2.02 ₹1,49,25,000; 2.03 ₹96,00,000; 2.04 -₹96,75,000; 2.09 ₹27,50,000; 2.10 ₹25,00,000; 2.11 ₹1,28,25,000; 2.12 ₹21,00,000; 3.01 = 6; 3.02 = 0; 3.03 = 0; 3.04 ₹58,27,500; 3.05 one bar "61+ days" = 3 Renew; 3.06 Defer 3 + Renew 3; 1.05 Year 1 = 9; 1.16 bars unchanged; 1.14 and 1.15 unchanged; 4.02 eight rows with FY 26-27 | FY 25-26 first row. No "Configuration error", no empty chart.
5.2 If any value changed, find which filter is missing on that chart and fix it; do not create a new field.
5.3 Report: per data source the list of calculated fields KEPT (with the charts that use each), the list DELETED, the total count, and the item results.
5.4 Update claude/looker_build_log.md with the same (do not commit anything to the repository).
