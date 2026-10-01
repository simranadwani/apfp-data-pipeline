Round 2 for the APFP Grant Portfolio Dashboard (same report, same rules as round 1: do not touch the Data Pipeline or mockup sheets, do not run Apps Script, do not change sharing, Raleway, palette #0E4A5C #167C88 #245563 #F4F6F7). I reviewed your PDF export (5 pages). Thank you: fixes 1, 2, 6 (3.06/3.07), 7 and the 4.01/4.08 label blocks look right. Please work through the list below in order, and tell me when each item is done. Keep the built-in browser pane visible while you work.

A. THE PIPELINE IS DEPLOYED. You are blocked only by stale field lists in Looker Studio.
   Verified in the live sheet today: tab fct6_grantee_annual_info exists (144 rows); fct5_maturity_rag has the new last column aspect_display; fct3_support_activity and stg_support have the new last column (fct3: response_category). Last pipeline run 1 Oct 11:41, all SUCCESS.
   1. Resource → Manage added data sources. For fct3_support_activity, fct5_maturity_rag: Edit → "Reconnect" (or Refresh fields) → apply. Confirm response_category (fct3) and aspect_display (fct5) now appear.
   2. Add a NEW data source: Add data → Google Sheets → Data Pipeline → fct6_grantee_annual_info (use first row as headers). Field types: all text except metric_order (number). Name it fct6_grantee_annual_info.
   3. This fixes the "Data Set Configuration Error" on 1.15 and 4.07 (they reference response_category). Check both render. If 1.15 still errors, open See details and tell me the field named.

B. GRANTEE 360 (page 5)
   4. 4.02: delete the current table and rebuild it on fct6_grantee_annual_info: dimensions metric, current_value, previous_value (in that order), no metrics, sort metric_order ascending, 8 rows, no pagination. Column headers: "Metric", "Selected year", "Previous year". Bold the first row ("Financial year") with a #F4F6F9 background using a conditional format on metric = Financial year. Controls Financial Year (field financial_year), Organisation (organisation) and Grant Status (grant_status) must filter it: after building, change the Organisation control and confirm the table changes. "–" is correct when the previous year has no data (all organisations show it for now: the sample data has one year only).
   5. 4.04: use aspect_display (not aspect) as the first dimension, then indicator, then status. Sort by aspect ascending then indicator ascending. Colour Status with the same RAG rules as 1.11 (Green #3A8969 / Amber #D39F3A / Red #C6695E fills; Amber text dark #1E2838, others white). Currently it shows plain text "Green". (The sample data has one maturity indicator per grant, so one row is expected.)
   6. 4.03: still two axes (right axis -1 to 1). Use ONE value axis. The "Disbursed (where different)" series must not draw a point at 0 when it is blank: keep it as a line with markers on the same axis, or if it cannot be blank-safe, show it in the tooltip only.
   7. 4.05: the pivot shows raw field names ("fy_label / Reach / Cost per Beneficiary", "primary_bene…"). Rename the row dimension header to "Primary beneficiary group", and make the column header just the year (FY 26-27) with sub-columns Reach and Cost per Beneficiary. No raw field IDs anywhere.
   8. 4.06: column order must be Outcome / indicator, Target, Q1, Q2, Q3, Q4, Annual, Notes (now Notes sits before Q1). Notes gets the widest column.
   9. 4.07: after step A.1, confirm columns Quarter, Support category, Request, Status, APFP response, and add Support provided (response_category). No Record Count.
   10. 4.08: the RECOMMENDATION row currently shows the rationale text. Point it to the field recommendation (highlight Renew), keep RATIONALE on reason_for_recommendation. Make the label column the same height as its rows (the dark block runs past the last row; same on 4.01).
   11. Controls on this page: Financial Year, Organisation, Grant Status are spread across the bar unevenly. Put them in one tidy row like the other pages (same widths and gaps).

C. DECISION QUEUE (page 4)
   12. 3.05 is EMPTY (axis 0–1, no bars). Diagnose it: check the chart filter (recommendation IN Renew, Close), the dimension (due_window) and the metric; pending Renew rows exist (3), so bars must show. Note: Close decisions are all "Decided", so with the Decision Status control on Pending only Renew can show; that is expected, do not change the control. Tell me what was wrong.
   13. 3.07: the "Reason for recommendation" column is squeezed (header wraps, text cut "Dummy rat…"). Give it the widest column and shorten others; keep column order as is.
   14. Do not change anything else on 3.06 (single colour #0E4A5C is right; it shows only the recommendations that exist in the filtered data).

D. PORTFOLIO OVERVIEW (page 2) and FUNDING (page 3)
   15. Whole-number axes: 1.08 and 3.05 axes still show 0.2, 0.4 …; 1.09/1.10/1.14 ok. Set decimal places 0 on every count axis (and use tick count so no fractions appear).
   16. Truncated category labels remain on 1.05, 1.06, 1.07, 1.09, 1.10, 1.13, 1.14, 2.05 (e.g. "Transa…", "Educat…", "Compl…", "Public Leader…"). Fix by widening the label area (Style → Axis → label width) or making the chart taller/horizontal so full labels show.
   17. 2.05 has small whiskers/error bars on the bars. Remove them (Style → turn off any trend/error/reference lines).
   18. 1.08: the colours (pink/purple/orange/dark) are outside the palette. Use the teal ramp #68B0BA #3F97A3 #167C88 #0E4A5C. Same axis fix as 15.
   19. 1.12: the table card has a large empty area under the 9 rows. Reduce the card height or table height so no empty block remains, and move the sections below up.
   20. 2.09–2.12 captions are clipped (they wrap to a second line and the table tag "T4" is cut). Widen the caption boxes or shorten the text size to fit on one line, exactly "2.09 | Dividends | T4" etc.

E. GUIDE (page 1)
   21. The "How to use" line 2 says "use Grantee Comparison for subcategory analysis": that page does not exist. Replace it with: "2 Apply the Financial Year filter and the page filters at the top of each view." Also add a blank line between items 1, 2 and 3.
   22. The Financial Year control shows "Financial Year: 20… (1)" truncated. Widen it to 220 px on every page.

F. LINK_360 (done, please verify more)
   23. Your link formula differs from the one I gave (it uses lookerstudio.google.com and single encoding). If it works, keep it, but test Paws & Care Trust (contains &), Jan Neta Fellowship Trust and Sakhi Youth Collective, each from "Click here" on 3.07 in View mode, and confirm Grantee 360 opens with that organisation. Report the three results. If any fails, switch to the formula in docs/looker_calculated_fields.txt (double-encoded) and retest.

G. FINAL CHECK
   24. In View mode, step through all 5 pages with default filters, then with Financial Year 2027-28. Send a new PDF export and a short report: item number, done / partly / not done.
   25. Update claude/looker_build_log.md with the results (do not commit anything to the repository).
