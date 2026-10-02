# APFP Pipeline — Data Model & Logic

How the APFP Looker Studio dashboard tables are built from the APFP Central Administration workbook.
Built to the Goalkeep *Data Pipeline Build Phase SoP v1.0*.

- **Source workbook:** APFP Central Administration (`18waNT2rH8HtErPqL3ERGNPNlSTXD-DfJc4quzzEhfkw`)
- **Pipeline workbook:** Data Pipeline (`1bjMmSxdN9RYJ6-Odgobqs4MedVy2QOMDYKLdKX08L00`)
- **Dashboard spec:** APFP Dashboard Mockup → *Fact Tables* tab (T1–T5)

---

## 1. Lineage

```
src (source workbook)             stg_ (pipeline workbook)      fct_ (pipeline workbook → Looker Studio)
─────────────────────             ────────────────────────      ────────────────────────────────────────
8. Grant Registry          ──►    stg_grants            ──┬──►  fct1_grant_portfolio   (T1)
9. Organisation Registry   ──►    stg_organisations     ──┤
4. Decision Tracker        ──►    stg_decisions         ──┤
6. Committed & Spent       ──►    stg_disbursements     ──┼──►  fct4_budget_year       (T4)
5. Dividends               ──►    stg_dividends         ──┘
2. Outcome Progress        ──►    stg_outcome_progress  ──────► fct2_outcome_progress  (T2)  (+ fct1)
3. Support                 ──►    stg_support           ──────► fct3_support_activity  (T3)
7. Organisation Maturity   ──►    stg_maturity          ──────► fct5_maturity_rag      (T5)  (+ fct1)
```

`stg_grants` is joined into every fct_ table to add `organization_id`, `organisation` and `thematic_area`.

**No int_ layer.** Each fct_ table is one join/aggregation away from staging. The shared logic
(quarter unpivot, disbursement sums) is a small helper function in `Final.js`, so an extra tab
would only add a write/read round trip. Add an int_ table if a future fct_ needs the same joined
dataset as another fct_.

`1. Workspace Creator` is not read: every field it holds is also in `8. Grant Registry`.
The `System - *` tabs are not read.

## 2. Pipeline workbook tabs

| Tab | Layer | Grain |
|---|---|---|
| `Index` | util | One row per tab. Scripts read every tab name from here (SoP 1.2) |
| `stg_*` (8 tabs) | stg | Same grain as the source tab |
| `fct1_grant_portfolio` | fct | One row per `grant_id` |
| `fct2_outcome_progress` | fct | One row per `grant_id` × `outcome_id` × reported `quarter` |
| `fct3_support_activity` | fct | One row per `support_id` |
| `fct4_budget_year` | fct | One row per `financial_year` |
| `fct5_maturity_rag` | fct | One row per `grant_id` × `aspect` × `indicator` |
| `fct6_grantee_annual_info` | fct | One row per `grant_id` × metric (8 metrics) |
| `ref_source_header_baseline` | ref | One row per source tab × column |
| `Source_Header_Audit` | util | Result of the latest header check |
| `Pipeline Log` | util | One row per build function per run |
| `Cardinality Test Results` | util | Result of the latest cardinality tests |

## 3. How to run

No triggers are installed. From the Apps Script editor, run **`runCompletePipeline`**:

0. **Time-zone alignment.** If the Data Pipeline workbook's time zone differs from the script's
   (`Asia/Kolkata` in `appsscript.json`), it is switched to the script's and a WARN is logged.
   Otherwise Apps Script shifts dates on every write/read. The source workbook is never changed;
   a different source zone is only logged, because staging reads source dates in the source's own zone.
1. **Source header check.** Compares the live source headers with `ref_source_header_baseline`
   (the first run creates the baseline). A missing or renamed column that the pipeline uses is
   CRITICAL: the pipeline stops before staging, logs an ERROR and emails you.
2. **Staging layer.** 8 × `buildStg*()`.
3. **Final layer.** 5 × `buildFct*()`.
4. **Cardinality tests.** Every table has rows, primary keys are unique and not null, and every
   `grant_id` / `organization_id` exists in the registries.

Other entry points:
- `runStagingLayerMenu`, `runFinalLayerMenu` and `runCardinalityTests` run one step on its own.
- `runSourceHeaderCheckMenu` runs only the header check.
- `setupSourceHeaderBaseline` re-snapshots headers after an agreed source change.
- `setupIndex` resets the Index tab.

Every run fully rebuilds each tab (`clearContents` then write), so running twice gives identical output.

## 4. Staging rules (all stg_ tabs)

| Rule | Detail |
|---|---|
| Header row | The first non-empty row of the tab. Registries start on row 1; tabs 2–7 on row 2. |
| Columns | Only the columns listed in `STAGING_SPECS` (`Staging.js`) are kept, renamed to snake_case. Bank details, narratives, links not used by the dashboard, and QA/system columns are dropped. |
| Category values | Kept **exactly as in the source**: `Discretionary`, `Complete`, `Discontinued`, `Alternate School Support`, `NA`, `Children`, `Application in Process`, and so on. Fix spellings in the source, not in the script (SoP 6.2). |
| Text | Trimmed. |
| Numbers | Stored as numbers. `₹`, commas and spaces are stripped. Unparseable values are blanked and logged as WARN. |
| Rates | `attrition_rate` and `foreign_contribution_rate` are kept as fractions (0.08). Text like `8%` becomes 0.08. |
| Dates | Stored as real dates at midnight. A date cell is read as the calendar day **shown in the source**, using the source workbook's time zone. Text `yyyy-mm-dd` and `dd/mm/yyyy` are parsed. The pipeline writes real dates only and **never sets a format**: date, number and percent display is owned by the sheet (the tabs are native Google Sheets Tables; see [docs/TABLE_FORMATS.md](docs/TABLE_FORMATS.md)). |
| Financial year | One format everywhere, in the pipeline and the dashboard: **`FY 26-27`**. Staging converts the source's `2026-27`, `2026-2027`, `FY 26-27` and the Dividends label `April 25-March 26` (→ `FY 25-26`). The source tabs are not changed. |
| Writing to Tables | Each tab is overwritten in place: header and rows go out in one `setValues`, so a Table keeps its columns and types. The header row is never cleared. Rows left over from a bigger previous run are deleted (or blanked if the sheet refuses); columns left over are blanked. A run with no data keeps the header and one blank row. Cosmetic steps and logging can never stop a run. |
| Blank keys | Rows whose key (`grant_id`, `organization_id`, `outcome_id`, `disbursement_id` or `financial_year`) is blank are skipped and logged as WARN. |

## 5. Fact table logic

Column names follow the mockup's *Fact Tables* tab. Where the mockup names a helper flag
(`active_grant_flag`, …), it is stored as an `is_*` boolean per SoP 1.5.

### fct1_grant_portfolio — one row per grant (T1)

Source for every row: `stg_grants`. Joins: `stg_organisations` on `organization_id`; `stg_decisions`, `stg_disbursements`, `stg_outcome_progress`, `stg_maturity` on `grant_id`.

| Column | Type | Source | Logic |
|---|---|---|---|
| financial_year | text | Grant Registry › Financial Year | Normalised to `FY 26-27` |
| grant_id | text | Grant Registry › Grant ID | Primary key |
| organization_id | text | Grant Registry › Organisation ID | — |
| organisation | text | Grant Registry › Organisation Name | — |
| mission | text | Org Registry › Mission Statement | Joined on `organization_id` |
| thematic_area | text | Grant Registry › Thematic Area | As source |
| education_sub_category | text | Grant Registry › Thematic Sub-area | As source (`NA` for non-education) |
| proximity_to_children_beneficiary | text | Grant Registry › Proximity to Children / Beneficiary | As source |
| grant_status | text | Grant Registry › Grant Status | As source: `Active` / `Complete` / `Discontinued` |
| grant_type | text | Grant Registry › Grant Type | As source. `Discretionary` = the mockup's *Activity-based* |
| grant_performance_status | text | Outcome Progress › Q1–Q4 Status | Take the **latest quarter that has any status** for the grant. `Off Track` if any outcome is Off Track in that quarter, else `On Track`. Blank if nothing is reported |
| grant_start_date / grant_end_date | date | Grant Registry | As source |
| funding_year | text | Grant Registry | `Year N`, where N = number of distinct financial years this `organization_id` has a grant in, up to and including this grant's FY |
| duration_of_support_bucket | text | derived | From N: 1 → `Year 1`; 2–5 → `Years 2–5`; 6–10 → `Years 6–10`; >10 → `Years 11+` |
| primary_beneficiary_group | text | Grant Registry › Primary Beneficiary Group | As source |
| primary_beneficiary_count | number | Grant Registry › Primary Beneficiary Count | As source |
| clarity_status / capacity_status / compliance_status | text | Organisation Maturity › Status | **Worst** RAG (Red > Amber > Green) across the grant's indicators for that aspect. Blank if no indicator is rated |
| fcra_registration | text | Org Registry › FCRA Registration Status | As source |
| has_completed_program_lifecycle | boolean | Grant Registry › Grant Status | TRUE when `Complete` |
| annual_budget | number | Grant Registry › Annual Budget — Current FY | As source |
| team_size | number | Grant Registry › Team Size — Current FY | As source |
| attrition_rate | number | Grant Registry › Employee Attrition — Current Snapshot | Fraction |
| foreign_contribution_rate | number | Grant Registry › Foreign Funding — Percentage of Total Annual Funding | Fraction |
| core_policies_met_count | number | Org Registry › Code of Conduct, POSH, Child Protection, Data Protection Policy? | Number of those 4 answered `Yes` |
| core_policies_total_count | number | constant | 4 |
| approved_amount | number | Grant Registry › Amount Approved | As source |
| committed_amount | number | Committed & Spent › Planned Amount | Sum for the grant where Status is `Committed` or `Disbursed` (a disbursed tranche was committed first) |
| disbursed_amount | number | Committed & Spent › Actual Amount | Sum for the grant where Status = `Disbursed` |
| funding_range | text | derived | Band on **total disbursed per organisation × financial year**: `<₹1 lakh`, `₹1–10 lakh` (≤10 L), `₹11–20 lakh` (≤20 L), `₹21–50 lakh` (≤50 L), `>₹50 lakh`. Blank when nothing is disbursed |
| decision_type | text | Decision Tracker › Decision Type | `Closure` when `Close`, otherwise `Renewal`. Blank if the grant has no decision row |
| decision_status | text | Decision Tracker › Decision Status | `Anagha's Recommendation` → `Pending`; `Decision Locked` → `Decided`; other values as source |
| due_window | text | Decision Due Date vs run date | Pending decisions only: days = due date − run date. <0 `Overdue`; 0–30 `0–30 days`; 31–60 `31–60 days`; >60 `61+ days` |
| recommendation | text | Decision Tracker › Decision Type | As source: `Renew` / `Modify` / `Defer` / `Close` |
| decision_due_date | date | Decision Tracker › Decision Due Date | As source |
| reason_for_recommendation | text | Decision Tracker › Decision Rationale | As source |
| grantee_360_link | text | — | Blank until the Looker report exists (needs its URL) |
| proposed_amount | number | Decision Tracker › Proposed Amount | As source |
| total_outcomes_count | number | Outcome Progress › Outcome ID | Distinct outcomes for the grant |
| achieved_outcomes_count | number | Outcome Progress › Final Actual vs End-of-Program Cycle Target | Outcomes where the number in Final Actual ≥ the number in the target (`80% achieved` vs `70% of annual target` → achieved) |
| annual_report_link | text | Decision Tracker › Annual Report Link | Falls back to Org Registry › Latest Annual Report Link |
| grant_period | text | derived | `yyyy-MM-dd - yyyy-MM-dd` from start/end dates |
| grant_status_type_amount | text | derived | `grant_status - grant_type - approved_amount` |
| cost_per_beneficiary | number | derived | `approved_amount ÷ primary_beneficiary_count`, rounded to 2 decimals. Blank if count is 0 |
| is_active_grant | boolean | Grant Status | TRUE when `Active` |
| is_funded_grantee | boolean | derived | TRUE when `disbursed_amount > 0` |
| is_pending_decision | boolean | derived | TRUE when `decision_status = Pending` |
| is_overdue_decision | boolean | derived | Pending and due date before the run date |
| is_due_within_30_days | boolean | derived | Pending and due in 0–30 days |
| is_on_track_active_grant | boolean | derived | `is_active_grant` and `grant_performance_status = On Track` |
| is_off_track_active_grant | boolean | derived | `is_active_grant` and `grant_performance_status = Off Track` |
| as_of_date | date | run date | Date the pipeline ran. `due_window` and the due flags are relative to it |

### fct2_outcome_progress — one row per grant × outcome × reported quarter (T2)

Built by unpivoting Q1–Q4 in `stg_outcome_progress`. A quarter gets a row only when it has a status, progress or notes, so unreported future quarters don't count.

| Column | Type | Source | Logic |
|---|---|---|---|
| financial_year | text | Outcome Progress › Financial Year | As source |
| grant_id | text | Outcome Progress › Grant ID | — |
| organization_id, organisation, thematic_area, grant_status | text | stg_grants | Joined on `grant_id`. `grant_status` lets the dashboard's Grant Status filter reach this table |
| outcome_id | text | Outcome Progress › Outcome ID | — |
| outcome_indicator | text | Outcome Progress › Outcome / Indicator | As source |
| quarter | text | column position | `Q1`–`Q4` |
| status | text | Qn Status | As source (`On Track` / `Off Track`) |
| target_text | text | End-of-Program Cycle Target | As source (e.g. `70% of annual target`), for display |
| target_value | number | End-of-Program Cycle Target | First number in the text. `%` becomes a fraction (`70% of annual target` → 0.7); plain numbers are kept (`732 learners` → 732) |
| achieved_value | number | Qn Progress | Same parsing (`35% achieved` → 0.35) |
| outcome_achievement_pct | number | derived | `achieved_value ÷ target_value` |
| final_actual_value | number | Final Actual | Same parsing as `target_value` (`80% achieved` → 0.8). Repeated on every quarter row of the outcome |
| annual_achievement_pct | number | derived | `final_actual_value ÷ target_value` (`80%` ÷ `70%` = 1.143). Repeated on every quarter row of the outcome; the dashboard's "Annual" column |
| outcome_notes | text | Qn Anagha Notes | As source |
| latest_notes | text | Qn Anagha Notes | Notes of the outcome's latest reported quarter. Repeated on every quarter row so a table can show one note per outcome |
| evidence_link | text | Qn Evidence Link | As source |
| is_latest_update | boolean | derived | TRUE on the outcome's latest quarter that has a status (for "latest update" scorecards) |

### fct3_support_activity — one row per support request (T3)

| Column | Type | Source | Logic |
|---|---|---|---|
| financial_year | text | Support › Financial Year | As source |
| grant_id | text | Support › Grant ID | — |
| organization_id, organisation, thematic_area, grant_status | text | stg_grants | Joined on `grant_id`. `grant_status` lets the dashboard's Grant Status filter reach this table |
| support_id | text | derived | `SUP-<grant_id>-<quarter>-<n>`, where n = order of the request within that grant and quarter. The source has no Support ID, so this changes if rows are reordered (see §7) |
| quarter | text | Support › Quarter | As source |
| support_category | text | Support › Support Type | As source |
| request_description | text | Support › Support Required | As source |
| support_status | text | Support › Status | `In Progress` → `Open`; `Open` / `Closed` as source |
| is_open_support_need | boolean | derived | TRUE when `support_status = Open` |
| response_notes | text | Support › Anagha Notes | As source |
| response_date | date | — | Blank: the source has no response date yet |
| evidence_link | text | Support › Evidence Link | As source |
| response_category | text | Support › Support Provided | The dropdown value as entered (currently the placeholders `Support 1` / `Support 2`). Blank until APFP fills it in. Last column of the table (added in 0.1.5, appended so the existing columns keep their positions) |

### fct4_budget_year — one row per financial year (T4)

Years = every FY in Dividends or the Committed & Spent tracker, in order.

| Column | Type | Source | Logic |
|---|---|---|---|
| financial_year | text | Dividends › FY, Committed & Spent › Financial Year | Normalised to `FY 26-27` |
| dividend_income | number | Dividends › Dividends | Sum for the FY |
| prior_year_carry_forward | number | derived | Previous FY's `available_budget − annual_committed_funding`. 0 for the first FY. **Can be negative** when a year was over-committed |
| available_budget | number | derived | `dividend_income + prior_year_carry_forward` |
| annual_committed_funding | number | Committed & Spent › Planned Amount | Sum where FY = this FY and Status is `Committed` or `Disbursed` |
| next_year_q1_committed_funding | number | Committed & Spent › Planned Amount | Same sum for the **next** FY's `Q1` tranches |
| annual_disbursed_funding | number | Committed & Spent › Actual Amount | Sum where FY = this FY and Status = `Disbursed` |
| unallocated_balance | number | derived | `available_budget − annual_committed_funding − next_year_q1_committed_funding` (mockup formula) |

The next-year Q1 amount is only a reserve: it is subtracted from this year's unallocated balance but **not** from the carry-forward, because next year counts it again in its own `annual_committed_funding`. Subtracting it twice would double count.

### fct5_maturity_rag — one row per grant × aspect × indicator (T5)

| Column | Type | Source | Logic |
|---|---|---|---|
| financial_year | text | Organisation Maturity › Financial Year | As source |
| grant_id | text | Organisation Maturity › Grant ID | — |
| organization_id, organisation, thematic_area, grant_status | text | stg_grants | Joined on `grant_id`. `grant_status` lets the dashboard's Grant Status filter reach this table |
| aspect | text | Organisation Maturity › Aspect | As source (`Clarity` / `Capacity` / `Compliance`) |
| indicator | text | Organisation Maturity › Indicator | As source (the 11 source indicators, not the mockup's 6) |
| status | text | Organisation Maturity › Status | As source (`Red` / `Amber` / `Green`) |
| aspect_display | text | derived | The aspect on the first row of each aspect block per grant, blank on the other rows (rows are ordered grant › aspect › indicator). A Looker table cannot merge cells, so this column gives the mockup's merged-Aspect look (chart 4.04). Last column |

### fct6_grantee_annual_info — one row per grant × metric (chart 4.02)

Looker Studio cannot transpose a table. The mockup shows metrics down the side with the selected year and the previous year beside it, so this table is stored that way. Source: `fct1_grant_portfolio` only. All values are display text.

| Column | Type | Logic |
|---|---|---|
| financial_year | text | The grant's financial year (the page's Financial Year control filters on this) |
| previous_financial_year | text | One year earlier (`FY 26-27` → `FY 25-26`) |
| grant_id, organization_id, organisation, grant_status | text | From the fct1 row |
| metric_order | number | 1–8; sort by it |
| metric | text | `Financial year`, `Annual budget`, `% Annual Budget funded by APFP`, `Team size`, `Attrition`, `Core policies`, `FCRA registration`, `Foreign contribution share` |
| current_value | text | The metric for this grant's year: rupees with Indian grouping (`₹54,00,000`), percentages rounded to whole % (`approved_amount ÷ annual_budget` for the funded share), `n / 4` for core policies, `FY 2026-27` for the Financial year row. `–` when blank |
| previous_value | text | Same, taken from the **same `organization_id`'s fct1 row in the previous financial year**. `–` when that organisation has no grant in the previous year |

The `Financial year` row (metric_order 1) carries the two column labels (`FY 26-27`, `FY 25-26`), because a table header cannot show a value. `previous_value` of this row is **always** the previous year's label, even when the organisation had no grant that year (the other rows show `–` then). Dashboard: table on `fct6`, dimensions `metric`, `current_value`, `previous_value`, sorted by `metric_order`; Financial Year, Organisation and Grant Status controls apply. If the same organisation has a different `organization_id` in different years, the previous year shows `–` (the ID must be stable across years).

## 6. Looker Studio calculated fields

The mockup's *Dashboard Metric* columns are aggregates. They are **not stored** in the tables, because a per-row copy would double count once Looker sums it. Create them as calculated fields on the data source:

| Metric (mockup) | Data source | Looker Studio formula |
|---|---|---|
| distinct_active_organisations | fct1 | `COUNT_DISTINCT(CASE WHEN is_active_grant THEN organization_id END)` |
| distinct_active_grants | fct1 | `COUNT_DISTINCT(CASE WHEN is_active_grant THEN grant_id END)` |
| distinct_grantees | fct1 | `COUNT_DISTINCT(organization_id)` |
| primary_beneficiaries_reached | fct1 | `SUM(primary_beneficiary_count)` |
| distinct_funded_grantees | fct1 | `COUNT_DISTINCT(CASE WHEN is_funded_grantee THEN organization_id END)` |
| apfp_funding_share | fct1 | `SUM(approved_amount) / MAX(annual_budget)` (one organisation and FY selected) |
| total_committed_funding | fct1 | `SUM(committed_amount)` |
| total_disbursed_funding | fct1 | `SUM(disbursed_amount)` |
| pending_decisions_count | fct1 | `COUNT_DISTINCT(CASE WHEN is_pending_decision THEN grant_id END)` |
| overdue_pending_decisions_count | fct1 | `COUNT_DISTINCT(CASE WHEN is_overdue_decision THEN grant_id END)` |
| due_within_30_days_count | fct1 | `COUNT_DISTINCT(CASE WHEN is_due_within_30_days THEN grant_id END)` |
| proposed_renewal_amount | fct1 | `SUM(CASE WHEN is_pending_decision AND recommendation = "Renew" THEN proposed_amount ELSE 0 END)` |
| on_track_active_grants_count | fct1 | `COUNT_DISTINCT(CASE WHEN is_on_track_active_grant THEN grant_id END)` |
| off_track_active_grants_count | fct1 | `COUNT_DISTINCT(CASE WHEN is_off_track_active_grant THEN grant_id END)` |
| pct_outcomes_achieved | fct1 | `SUM(achieved_outcomes_count) / SUM(total_outcomes_count)` (the mockup has this inverted) |
| open_support_needs_count | fct3 | `COUNT_DISTINCT(CASE WHEN is_open_support_need THEN support_id END)` |
| support_needs_count | fct3 | `COUNT_DISTINCT(support_id)` |

`outcome_achievement_pct` (fct2) and `available_budget` / `unallocated_balance` (fct4) are row-level values, so they are stored.

## 7. Decisions taken and known limitations

| # | Topic | Decision / limitation | Recommended fix |
|---|---|---|---|
| 1 | Category values | Kept exactly as in the source (agreed). Looker labels will show source spellings, e.g. `Alternate School Support`, `NA`. | Standardise dropdowns in the source if labels need to change |
| 2 | Returning organisations | In the dummy data every "Returning Organisation" has a **new** Organisation ID, so `funding_year` is `Year 1` for everyone. | Make sure a returning organisation keeps its original Organisation ID |
| 3 | Support ID | Generated (`SUP-<grant>-<quarter>-<n>`), so it changes if support rows are reordered. | Add a Support ID column to `3. Support` |
| 4 | Support response | `response_category` now comes from the source column **Support Provided**; `response_date` is still blank (no date in the source). The dropdown currently holds placeholders (`Support 1`, `Support 2`), not the four approved categories (Connected to other partners · Additional funding raised · Provided expert advice · Other). | Replace the dropdown values in the source when final (no pipeline change); add a Response Date column if the date is needed |
| 5 | Outcome values | Targets and progress are free text; only the first number is read. | Keep entries in the `NN% …` pattern, or split value and unit into two columns |
| 6 | Due window | Computed against the run date. Without a trigger it is only as fresh as the last manual run (`as_of_date`). | Add the daily trigger when ready (SoP 4.2) |
| 7 | Budget sample data | Dummy dividends (₹25–34 L/yr) are far below dummy commitments (₹1.3 Cr in FY 26-27), so `fct4` shows negative balances. The logic is correct; the numbers are dummy. | — |
| 8 | Grantee 360 link | Blank until the Looker report URL is known. | Share the report URL and filter parameter |
| 9 | Record Status | Rows are not filtered on Record Status (all dummy rows are `Active`). | Say if archived records should be excluded |
| 10 | Dummy outcome data | The dummy data fills Q1–Q4 of FY 26-27, including quarters still in the future, and every Q4 is On Track. So all 18 grants are `On Track` and the off-track charts are empty. Real data only has reported quarters. | — |
| 11 | Dummy decision dates | Every pending decision is due 31 Mar 2027/28, so all are `61+ days`; Overdue and 0–30 are empty. | — |
| 12 | `Sheet1` | An empty default tab remains in Data Pipeline. The pipeline never uses it. | Delete it by hand |
