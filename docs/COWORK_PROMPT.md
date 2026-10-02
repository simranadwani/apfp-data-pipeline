You are Claude Cowork. Build a Looker Studio dashboard exactly as specified in the attached document "APFP Looker Studio Dashboard - Build Specification" (APFP_Looker_Dashboard_Build_Spec.docx). That document is your single source of truth. Read all of it (especially Sections 2, 3, 6, 8 and 9) before you touch Looker Studio.

WHAT YOU ARE BUILDING
A five-page Looker Studio report named "APFP Grant Portfolio Dashboard" (pages: Dashboard Guide, 1. Portfolio Overview, 2. Funding Allocation, 3. Decision Queue, 4. Grantee 360). It reads from the Google Sheet "Data Pipeline":
https://docs.google.com/spreadsheets/d/1bjMmSxdN9RYJ6-Odgobqs4MedVy2QOMDYKLdKX08L00
Look-and-feel reference (read-only mockup workbook):
https://docs.google.com/spreadsheets/d/19kAsydK0TGmJtdJjlLn3Ldt_RWe_sdDPb4LIT1Snv_s
Paste-safe copies of every calculated-field formula are in the attached text file looker_calculated_fields.txt (use it instead of copying formulas out of the Word document).

HOW TO WORK
1. Use the browser session that is signed in to the Google account with access to the Data Pipeline sheet. If you are not signed in, or cannot open both sheets, stop and tell me.
2. Do the checks in Section 2 first. If any check fails, stop and report it.
3. Follow the build order in Section 9, one step at a time: theme -> data sources -> field IDs -> calculated fields -> shared Financial Year control -> pages 0, 1, 2, 3, 4 -> navigation and links -> final QA.
4. Type titles, captions, field names, formulas, display headers and hex colours exactly as the document gives them. Do not paraphrase, re-order or "improve" them.
5. After each page, run that page's checks in Section 9 and compare the numbers on screen with the expected values (Financial Year FY 26-27 selected unless a row says otherwise). Fix mismatches before moving on. If a number still differs after you have checked the filters and formulas, do not change any data: report the difference.
6. Keep a running log of what you built, what you skipped and why, and every place you had to deviate from the document.

RULES YOU MUST NOT BREAK
- The Data Pipeline sheet and the mockup are READ-ONLY. Never edit, rename, delete or add tabs, rows or cells. Never open Apps Script. Never run the pipeline.
- Create only Looker Studio items: one report and the data sources it needs. Do not modify any other Looker Studio report or data source.
- Do not share the report with anyone, and do not change link sharing or make anything public. It stays private to the signed-in account until I decide (Section 10).
- Do not invent data or hard-code numbers into charts. Every number must come from the data sources.
- If a step needs a login, permission, payment, or a decision the document does not cover, stop and ask me.
- Report anything unusual (missing columns, errors, unexpected values) instead of working around it.

WHEN TO STOP AND ASK ME
- Any prerequisite check in Section 2 fails.
- The filter test in Section 9 fails: one Financial Year control must change charts from every data source, and must NOT change the "all years" charts (1.16, 2.08, 4.02, 4.03, 4.05).
- A requirement cannot be done in Looker Studio and Section 8 does not give the alternative.
- You reach the sharing step (do not share; just tell me the report is ready).

FINAL REPORT (post this when you have finished)
1. The report's edit URL.
2. A checklist of every tile and chart in the document (IDs 1.01 to 4.08) marked Built / Partly built / Not built, with the reason for anything that is not "Built".
3. The QA results: expected versus actual for every number in Section 9.
4. A list of deviations from the document.
5. A screenshot of each of the five pages with the default filters, and one screenshot of Grantee 360 with an organisation selected.
6. Open questions for me.
