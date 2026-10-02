ROUND 3 for the report "APFP Grant Portfolio Dashboard" (supersedes rounds 1 and 2)
https://datastudio.google.com/reporting/dba82e50-a6d6-4ef3-a273-ff3b0b827046

I reviewed the PDF the owner exported after your round 2 (the owner exports PDFs, you do not). Thank you: done and verified in that PDF: 3.05 (one "61+ days" Renew bar), 1.14 colours, 1.15 renders, 1.08 colours, 4.01 grant period and separators, 4.02 rebuilt (8 rows, headers Metric / Selected year / Previous year), 4.03 single axis, 4.07 table with Support provided, 4.08 Renew highlight, Guide text. Do not redo those. This round has four new things (FY format, unused fields, field names, control grid), the 4.02 filter behaviour, and the leftovers.

RULES (unchanged)
- Do NOT edit the Data Pipeline sheet or the mockup sheet, do NOT run Apps Script, do NOT change sharing, do NOT commit to the repository. Font Raleway. Keep the built-in browser pane visible.
- OUT OF SCOPE this round: table COLUMN ORDER and COLUMN WIDTHS (1.11, 3.07, 4.06, 4.07 and others). The owner will do those by hand. Do not change them.
- Work in the order below. After each item write DONE / PARTLY / NOT DONE and what you saw. "Check" means View mode.
- Palette: #0E4A5C deep teal, #167C88 teal, #245563 Guide bands, #F4F6F7 page, #FFFFFF cards, #F4F6F9 light header, #E2F2F4 light teal tile, #1E2838 text, #5F6C77 muted, RAG #C6695E Red / #D39F3A Amber (dark text) / #3A8969 Green, On Track #D4EEDD text #1D5F33, Off Track #F4CCCC text #991717, light series #B8D8DD.
- Deliberate deviations to LEAVE: title tags (1.11 T1, 1.13 T5, 2.02/2.03/2.11 T4), Guide text verbatim (including the "Grantee Comparison" wording), Amber with dark text, rupee text fields, 3.01 = 6 vs the 3.07 list of 3.

=====================================================================
STEP 0. REFRESH THE DATA (the pipeline was re-run: financial years now read "FY 26-27")
=====================================================================
The owner has deployed and re-run the pipeline. EVERY financial_year value is now "FY 26-27" / "FY 27-28" (it was "2026-27"). fct6 changed too.
0.1 Resource > Manage added data sources: for ALL data sources (fct1, fct1 all years, fct2, fct3, fct4, fct5, fct6) Edit > Reconnect / refresh fields > apply.
0.2 Check in a table or the control that financial_year now lists "FY 26-27" and "FY 27-28". If you still see "2026-27", STOP and tell me: the pipeline run is not live yet.

=====================================================================
STEP 1. FINANCIAL YEAR: ONE FORMAT "FY 26-27" EVERYWHERE
=====================================================================
1.1 Financial Year control (report level): set the default to "FY 26-27". It must be single-select. All pages show the same value.
1.2 Search every chart, control and conditional format for filters, colour maps or text that name "2026-27" or "2027-28" and re-pick them as "FY 26-27" / "FY 27-28". Nothing on screen may show the "2026-27" style any more (controls, axes, legends, table cells, titles, subtitles).
1.3 1.16, 2.08, 4.03, 4.05 (all-years data source): the year axis / legend / pivot column uses the field financial_year_all directly (it already reads "FY 26-27"); do NOT use fy_label (it is deleted in step 2). 1.16 colour per year: FY 26-27 #167C88 dark teal, FY 27-28 #68B0BA light (any consistent ramp, oldest lightest is fine).
1.4 Check the tiles for FY 26-27 (these values do not change): 1.01 = 9; 1.02 = 100%; 1.03 = 0; 1.04 = 8; 2.01 ₹52,50,000; 2.02 ₹1,49,25,000; 2.03 ₹96,00,000; 2.04 -₹96,75,000; 3.01 = 6; 3.04 ₹58,27,500.

=====================================================================
STEP 2. DELETE UNUSED CALCULATED FIELDS (delete first, rename second)
=====================================================================
2.1 Delete these without further checking, in every data source where they exist (fct1, fct1 all years, blend): fy_label, recommendation_copy, m_support_grantees, m_committed, m_disbursed, m_apfp_share, m_team_size, m_attrition, m_foreign_share, core_policies_text. If one is still used by a chart, filter, sort, conditional format or other formula, first re-point that use: recommendation_copy -> recommendation; fy_label -> financial_year (or financial_year_all in the all-years source); the others have no remaining use.
2.2 AUDIT: for every OTHER calculated field in every data source (including the ones you created yourself: row-level Indian-format fields, notes_last, grant_period_text, status/type/amount line, blend fields), find whether it is used by any chart (metric, dimension, breakdown, sort, filter, scorecard), control, conditional-format rule, or another calculated field. DELETE every field with no use and every field that duplicates another field with the same formula (keep one). Candidates to check first: grant_status_line (4.01 now uses a status / type / amount field), inr_proposed, inr_approved, inr_proposed_renewal where a row-level field replaced them, max_annual_budget / inr_annual_budget in the all-years copy (they were added for the old 4.02), and every field in the all-years source that no chart there uses.
2.3 The formulas of every field are kept in docs/looker_calculated_fields.txt, so nothing is lost. Do not delete pipeline columns (the Google Sheet headers); only calculated fields.
2.4 Write down: fields deleted, fields kept with the charts that use them.

=====================================================================
STEP 3. NAME THE REMAINING CALCULATED FIELDS BY TYPE
=====================================================================
Convention: distinct_ = COUNT_DISTINCT; sum_ = SUM; max_ = MAX; avg_ = average or per-unit ratio; pct_ = percentage; inr_ = rupee text (already, keep); txt_ = other text; ord_ = sort helper; link_ = hyperlink. Pipeline columns are never renamed.
Rename both the field name and, where the editor lets you, the Field ID. Chart column headers you already renamed stay as they are. Do ONE data source at a time, base fields before the fields that use them, then check that no formula shows an error, no chart shows "Configuration error", and no conditional format or filter lost its field. If an ID cannot be changed, rename the display name and say so.
fct1_grant_portfolio (and the same fields in the all-years copy):
 m_active_orgs -> distinct_active_orgs; m_active_grants -> distinct_active_grants; m_on_track_grants -> distinct_on_track_grants; m_off_track_grants -> distinct_off_track_grants; m_pct_on_track -> pct_active_grants_on_track; m_grantees -> distinct_grantees; m_beneficiaries -> sum_beneficiaries; m_funded_grantees -> distinct_funded_grantees; m_approved -> sum_approved; m_proposed -> sum_proposed; m_annual_budget -> max_annual_budget; m_cost_per_beneficiary -> avg_cost_per_beneficiary; m_pending -> distinct_pending_grants; m_overdue -> distinct_overdue_grants; m_due30 -> distinct_due_30_days_grants; m_proposed_renewal -> sum_proposed_renewal; m_pct_achieved -> pct_outcomes_achieved; m_disbursed_if_different -> sum_disbursed_lakh_if_different; m_approved_lakh -> sum_approved_lakh; m_disbursed_lakh -> sum_disbursed_lakh; m_committed_lakh -> sum_committed_lakh; due_date_text -> txt_due_date; annual_report_link_text -> link_annual_report; link_360 -> link_grantee_360; grant_period_text -> txt_grant_period; grant_status_line -> txt_grant_status_line; sub_category_line -> txt_sub_category_line; funding_range_order -> ord_funding_range; due_window_order -> ord_due_window.
fct2_outcome_progress: m_outcomes_latest -> distinct_latest_outcomes; m_outcomes_latest_on_track -> distinct_latest_outcomes_on_track; m_pct_outcomes_on_track -> pct_outcomes_on_track; status_q1..status_q4 -> txt_status_q1..txt_status_q4; m_annual_pct -> pct_annual_achievement; notes_last -> txt_notes_last.
fct3_support_activity: m_open_needs -> distinct_open_needs; m_needs -> distinct_needs; m_responses -> distinct_responses.
fct4_budget_year: n_available -> sum_available_budget; n_dividends -> sum_dividends; n_carry_forward -> sum_carry_forward; n_committed_current -> sum_committed_current_fy; n_next_q1 -> sum_committed_next_fy_q1; n_committed_total -> sum_committed_total; n_disbursed -> sum_disbursed_funding; n_unallocated -> sum_unallocated_balance. (inr_* stay.)
fct5_maturity_rag: m_assessed -> distinct_assessed_grantees; aspect_order -> ord_aspect.
Any field you created that is not in this list and survived step 2: apply the same convention (prefix from the formula) and list old -> new in your report. Blend: re-open the 4.02 blend and the 1.x blends if any, and confirm they still resolve.
After renaming, re-check the headline values in 1.4 and that these still work: 3.05 bar, 4.04 colours, 4.08 Renew highlight, the Click here links.

=====================================================================
STEP 4. FILTER CONTROLS: ONE SIZE, ONE SPACING, EVERYWHERE
=====================================================================
4.1 Every control on every page: width 240 px, height 40 px, y = 92, same style: white fill, 1 px #167C88 border, radius 4, value text 13 px bold #0E4A5C, label text 13 px, font Raleway. No dark-teal filled controls (the Financial Year control currently looks different from the others).
4.2 Slots (x position): slot 1 = 24, slot 2 = 280, slot 3 = 536, slot 4 = 792 (16 px gap). Financial Year is ALWAYS slot 1 on every page, in the same place. Others fill slots 2, 3 in this order:
  Guide: Financial Year.
  Portfolio Overview: Financial Year, Grant Status, Thematic Area.
  Funding Allocation: Financial Year, Thematic Area.
  Decision Queue: Financial Year, Decision Status, Thematic Area.
  Grantee 360: Financial Year, Organisation, Grant Status.
4.3 Nothing overlaps (currently Financial Year overlaps Thematic Area on Funding Allocation and Decision Status on Decision Queue; Grantee 360 is unevenly spread). Use Arrange > Align and Distribute; verify the numbers in the Position / size panel, do not judge by eye.
4.4 Labels clean: "Financial Year", "Grant Status", "Thematic Area", "Decision Status", "Organisation". Financial Year and Organisation single-select. The "(1)" badge cannot be removed in Looker Studio: leave it. Make the Financial Year control wide enough to show "FY 26-27" untruncated (240 px is enough once the "20..." truncation is gone).
4.5 Defaults: Financial Year FY 26-27; Decision Status Pending; Organisation BrightSteps Learning Trust; Grant Status and Thematic Area blank (all).
4.6 Do NOT delete or recreate the Organisation control on Grantee 360 (its filter ID df232 is used by the Click here link). If you must replace it, tell me first.

=====================================================================
STEP 5. 4.02 MUST FOLLOW THE FINANCIAL YEAR CONTROL
=====================================================================
Required behaviour: the table shows the SELECTED financial year in "Selected year" and the year BEFORE it in "Previous year", nothing more and nothing less. FY 26-27 selected -> previous FY 25-26. FY 25-26 selected -> previous FY 24-25. The first row ("Financial year") carries the labels, so the column header always names the right years even when that organisation had no data in the previous year (then the other rows show "–").
The pipeline already does this: fct6_grantee_annual_info has one row per grant per metric with financial_year = the selected year and previous_value = the previous year. So the table only needs the Financial Year control to filter fct6 by financial_year, and the Organisation control to filter by organisation (or organization_id).
5.1 First try WITHOUT a blend: Resource > Manage field names and IDs: make fct6's financial_year, organisation and grant_status field IDs identical to the IDs of the controls (compare them). Build the table on fct6 only (dimensions metric, current_value, previous_value; sort metric_order ascending). Test with the Organisation and Financial Year controls. If both now filter it, delete the blend and keep this simpler version.
5.2 If the Organisation control still does not reach it, keep your blend, but: the blend's controlling side must be the CURRENT-YEAR fct1 source (financial_year), NOT the all-years copy; join keys financial_year AND organization_id; show only fct6's metric, current_value, previous_value. Table subtitle: "Selected financial year and the year before it".
5.3 Acceptance tests (View mode, Grantee 360), write the result of each:
  T1 BrightSteps Learning Trust + FY 26-27: first row Financial year | FY 26-27 | FY 25-26; Annual budget ₹50,00,000; % funded by APFP 15%; Team size 12; Attrition 8%; Core policies 3 / 4; FCRA registration Registered; Foreign contribution share 0%; every Previous-year value except the first row is "–". Exactly 8 rows, no row numbers, no pagination footer.
  T2 BrightSteps + FY 27-28: "No data" (BrightSteps has no grant in FY 27-28: correct).
  T3 ImpactSpring Foundation + FY 27-28: first row FY 27-28 | FY 26-27; Annual budget ₹98,00,000; previous values "–".
  T4 Change ONLY the Financial Year control (organisation unchanged) and confirm the table changes or goes to "No data" accordingly: this proves the FY control reaches 4.02.
  T5 The table never shows a third year and never shows an extra row or column.
The sample data has one year per organisation, so a populated previous column cannot be seen yet; do not try to fake it.

=====================================================================
STEP 6. LEFTOVERS FROM ROUND 2 (not column order, not widths)
=====================================================================
Page 1 (Guide)
6.1 Make each of the four card headings clickable. Select the heading text box, select the text, use the link icon, and paste the URL of that page (open the page in View mode, copy the address bar; page URLs look like https://datastudio.google.com/reporting/<report id>/page/<page id>). Test all four in View mode. If the editor truly has no link option, say so and I will give the owner another way.
Page 2 (Portfolio Overview)
6.2 1.08: count axis whole numbers only (it shows 0.2, 0.4 ...). Same for 1.05, 1.06, 1.07, 1.09, 1.10, 1.14, 1.16: decimal places 0 on axis and data labels.
6.3 Truncated category labels ("Transa...", "Educat...", "Compl...", "Review goals & long-te...", "Inclusi..."): widen the category axis area or make the chart taller so the full label shows. Do not shorten the values.
6.4 1.13: legend order Red, Amber, Green (now Amber, Red, Green); data labels as percent.
6.5 1.12: the card is far taller than its rows; reduce card height so there is no empty block, and move the sections below it up.
Page 3 (Funding Allocation)
6.6 2.05, 2.06, 2.08: Committed #167C88, Disbursed #B8D8DD (light). Data labels on the bars: dark #1E2838 on light bars, white on dark bars; 2.05 has none now, add them (1 decimal). Remove the small whiskers / error bars on 2.05 (Style: turn off error bars, trend and reference lines).
6.7 2.09-2.12 captions are clipped ("T4" cut off). Make the caption boxes wide enough for one line: "2.09 | Dividends | T4", "2.10 | Carry Forward | T4", "2.11 | Current FY | T4", "2.12 | Next FY Q1 | T4".
Page 4 (Decision Queue)
6.8 3.07 header row: fill #167C88, white text (it is still light grey). Click here: after the renames in step 3 the field is link_grantee_360; test the link formula in 6.15.
Page 5 (Grantee 360)
6.9 4.03: the line "Disbursed (where different)" still draws a dot at 0 where the value is blank. Make the blank value not plot (the field must return NULL, not 0; use the chart's missing-data option if there is one) or hide that series if it cannot be done. Shorten the left axis title to "₹ lakh". Add data labels to the columns.
6.10 4.04: the Status cells show plain text with no colour (the rules broke after the field swap). Re-point the conditional-format rules to the Status field: Green #3A8969 white text, Amber #D39F3A text #1E2838, Red #C6695E white text. Check.
6.11 4.05: the header still reads "Financial year / Reach / Cost per Beneficiary". Row dimension header "Primary beneficiary group"; column group header = the financial year only ("FY 26-27") over two sub-columns "Reach" and "Cost per Beneficiary". If the pivot cannot hide the auto-generated corner label, replace the pivot with a plain table: dimensions Primary beneficiary group, Reach (sum_beneficiaries), Cost per Beneficiary (inr_cost_per_beneficiary), filtered by the Financial Year control (current-year source).
6.12 4.08 and 4.01: the dark label column runs below the last row. Make the label blocks exactly as tall as the rows, with the thin separators between rows.
6.13 4.07 and 4.06: leave as they are (column order and widths are the owner's).
6.14 Table header style: 3.07, 4.05 and any other table with a light header that the mockup shows teal: fill #167C88 white text (4.02, 4.04, 4.07 are done).
6.15 CLICK HERE (link_grantee_360, formerly link_360): the formula must be exactly the one in docs/looker_calculated_fields.txt under link_grantee_360 (host datastudio.google.com, page p_0lm6sfxw7d, parameter df232, double-encoded name). Test in View mode from 3.07 for Nyaya Setu Foundation, Sehat Saathi Foundation, BrightSteps Learning Trust, and, by temporarily choosing the right Decision Status or using the Grantee 360 control directly, a name containing "&": Paws & Care Trust. Each must open Grantee 360 with that organisation selected. Report the four results.

=====================================================================
STEP 7. FINISH
=====================================================================
7.1 Walk all 5 pages in View mode with defaults (Financial Year FY 26-27): no "Data Set Configuration Error", no empty chart, no raw field name anywhere, no "2026-27" style label, no overlapping controls, every count axis whole numbers. Then set Financial Year to FY 27-28: no page errors (values differ).
7.2 Do NOT export a PDF: the owner will export it. Tell the owner when the report is ready.
7.3 Send a short report: for every numbered item DONE / PARTLY / NOT DONE and one line on what you saw; the list of calculated fields DELETED; the list of fields KEPT with the charts that use them; the old -> new field names; the 4.02 test results T1-T5; the Click here results.
7.4 Update claude/looker_build_log.md with the same (do not commit anything to the repository).
