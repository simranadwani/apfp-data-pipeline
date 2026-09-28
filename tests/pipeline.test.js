// Local tests: run the real Apps Script files against the dummy source workbook.
// npm test   (no dependencies; uses node:test)
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadPipeline, isDate } = require('./harness');

function runFull(sourceTabs) {
  const h = loadPipeline(sourceTabs);
  h.ctx.runCompletePipeline();
  h.tab = (name) => h.pipeline.getSheetByName(name).toObjects();
  return h;
}

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

test('full pipeline builds every stg_ and fct_ tab with the expected row counts', () => {
  const h = runFull();
  const expected = {
    stg_grants: 18, stg_organisations: 18, stg_outcome_progress: 18, stg_support: 18,
    stg_decisions: 18, stg_dividends: 4, stg_disbursements: 18, stg_maturity: 18,
    fct1_grant_portfolio: 18, fct2_outcome_progress: 72, fct3_support_activity: 18,
    fct4_budget_year: 4, fct5_maturity_rag: 18,
  };
  Object.entries(expected).forEach(([tab, n]) => assert.equal(h.tab(tab).length, n, tab));
  const failed = h.tab('Cardinality Test Results').filter((r) => r.status !== 'PASS');
  assert.deepEqual(failed, []);
  assert.equal(h.mails.length, 0);
});

test('pipeline is idempotent: a second run produces identical stg_ and fct_ tabs', () => {
  const h = runFull();
  const snapshot = () => Object.fromEntries(h.pipeline.getSheets()
    .filter((s) => /^(stg|fct)/.test(s.getName()))
    .map((s) => [s.getName(), JSON.stringify(s.data)]));
  const first = snapshot();
  h.ctx.runCompletePipeline();
  assert.deepEqual(snapshot(), first);
});

test('fct1 derives decision, funding, maturity and outcome fields', () => {
  const h = runFull();
  const byId = Object.fromEntries(h.tab('fct1_grant_portfolio').map((r) => [r.grant_id, r]));

  const brigh = byId.BRIGH_01_202627_301;
  assert.equal(brigh.financial_year, '2026-27');
  assert.equal(brigh.funding_year, 'Year 1');
  assert.equal(brigh.duration_of_support_bucket, 'Year 1');
  assert.equal(brigh.decision_type, 'Renewal');
  assert.equal(brigh.decision_status, 'Pending');
  assert.equal(brigh.recommendation, 'Renew');
  assert.equal(brigh.committed_amount, 375000); // Committed tranche, not yet disbursed
  assert.equal(brigh.disbursed_amount, 0);
  assert.equal(brigh.funding_range, '');
  assert.equal(brigh.core_policies_met_count, 3); // Child Protection = No
  assert.equal(brigh.core_policies_total_count, 4);
  assert.equal(brigh.clarity_status, 'Green');
  assert.equal(brigh.cost_per_beneficiary, 1500); // 7,50,000 / 500
  assert.equal(brigh.grant_period, '2026-04-01 - 2027-03-31');
  assert.equal(brigh.grant_status_type_amount, 'Active - Restricted - 750000');
  assert.equal(brigh.is_active_grant, true);
  assert.ok(isDate(brigh.grant_start_date));

  const sakhi = byId.SAKHI_02_202627_302;
  assert.equal(sakhi.decision_status, 'Decided');
  assert.equal(sakhi.due_window, ''); // only pending decisions get a due window
  assert.equal(sakhi.funding_range, '₹1–10 lakh');
  assert.equal(sakhi.is_funded_grantee, true);

  const nayi = byId.NAYID_04_202627_304;
  assert.equal(nayi.grant_type, 'Discretionary'); // source value kept
  assert.equal(nayi.decision_type, 'Closure');
  assert.equal(nayi.proximity_to_children_beneficiary, 'Alternate School Support'); // source value kept

  const sehat = byId.SEHAT_05_202627_305;
  assert.equal(sehat.achieved_outcomes_count, 0); // Final Actual 80% < target 90%
  assert.equal(sehat.education_sub_category, 'NA');
});

test('fct2 unpivots quarters and marks the latest update', () => {
  const h = runFull();
  const rows = h.tab('fct2_outcome_progress').filter((r) => r.grant_id === 'BRIGH_01_202627_301');
  assert.deepEqual(rows.map((r) => r.quarter), ['Q1', 'Q2', 'Q3', 'Q4']);
  assert.equal(rows[0].target_value, 0.7);
  assert.equal(rows[0].achieved_value, 0.35);
  assert.equal(rows[0].outcome_achievement_pct, 0.5);
  assert.deepEqual(rows.map((r) => r.is_latest_update), [false, false, false, true]);
  assert.equal(rows[0].organization_id, 'BRIGH_202627_101');
});

test('fct3 generates support ids and treats In Progress as Open', () => {
  const h = runFull();
  const rows = h.tab('fct3_support_activity');
  const sakhi = rows.find((r) => r.grant_id === 'SAKHI_02_202627_302');
  assert.equal(sakhi.support_id, 'SUP-SAKHI_02_202627_302-Q2-1');
  assert.equal(sakhi.support_status, 'Open');
  assert.equal(sakhi.is_open_support_need, true);
  assert.equal(rows.filter((r) => r.support_status === 'In Progress').length, 0);
});

test('fct4 rolls the carry-forward and reserves next year Q1 commitments', () => {
  const h = runFull();
  const rows = h.tab('fct4_budget_year');
  assert.deepEqual(rows.map((r) => r.financial_year), ['2025-26', '2026-27', '2027-28', '2028-29']);
  const [y1, y2] = rows;
  assert.equal(y1.dividend_income, 2500000);
  assert.equal(y1.prior_year_carry_forward, 0);
  assert.equal(y1.available_budget, 2500000);
  assert.equal(y1.unallocated_balance, y1.available_budget - y1.annual_committed_funding - y1.next_year_q1_committed_funding);
  // Carry-forward excludes the Q1 reserve, which next year counts as its own commitment.
  assert.equal(y2.prior_year_carry_forward, y1.available_budget - y1.annual_committed_funding);
  assert.equal(y2.available_budget, y2.dividend_income + y2.prior_year_carry_forward);
});

test('a renamed required source header stops the pipeline before staging and emails the owner', () => {
  const h = loadPipeline();
  h.ctx.runCompletePipeline(); // first run records the header baseline

  const fixture = h.source.getSheetByName('8. Grant Registry').data;
  fixture[0][fixture[0].indexOf('Amount Approved')] = 'Approved Amount';
  h.pipeline.getSheetByName('stg_grants').clearContents();

  assert.throws(() => h.ctx.runCompletePipeline(), /critical source header issue/);
  const audit = h.pipeline.getSheetByName('Source_Header_Audit').toObjects();
  const renamed = audit.find((r) => r.issue_type === 'Renamed Header');
  assert.equal(renamed.header, 'Amount Approved');
  assert.equal(renamed.severity, 'CRITICAL');
  assert.equal(h.pipeline.getSheetByName('stg_grants').data.length, 0); // staging never ran
  assert.equal(h.mails.length, 1);
  const lastLog = h.pipeline.getSheetByName('Pipeline Log').toObjects().pop();
  assert.equal(lastLog.status, 'ERROR');
});

test('a new, unused source column is a warning and does not stop the pipeline', () => {
  const h = loadPipeline();
  h.ctx.runCompletePipeline();
  h.source.getSheetByName('5. Dividends').data[1].push('Remarks');
  h.ctx.runCompletePipeline();
  const audit = h.pipeline.getSheetByName('Source_Header_Audit').toObjects();
  assert.equal(audit[0].issue_type, 'New Header Added');
  assert.equal(audit[0].severity, 'WARN');
});

test('staging skips rows with a blank key and logs a warning', () => {
  const src = clone(require('./fixtures/source_dummy.json'));
  src['3. Support'][2][3] = ''; // blank Grant ID on the first data row
  const h = runFull(src);
  assert.equal(h.tab('stg_support').length, 17);
  const warn = h.tab('Pipeline Log').find((r) => r.level === 'WARN' && /stg_support|STG_SUPPORT/.test(r.function));
  assert.match(warn.message, /skipped/);
});

test('helper rules', () => {
  const { ctx } = loadPipeline();
  assert.equal(ctx.normaliseFinancialYear('April 25-March 26'), '2025-26');
  assert.equal(ctx.normaliseFinancialYear('2026-27'), '2026-27');
  assert.equal(ctx.normaliseFinancialYear('FY 26-27'), '2026-27');
  assert.equal(ctx.normaliseFinancialYear('2026-2027'), '2026-27');
  assert.equal(ctx.normaliseFinancialYear('next year'), '');
  assert.equal(ctx.nextFinancialYear('2026-27'), '2027-28');
  assert.equal(ctx.nextFinancialYear('2099-00'), '2100-01');

  assert.equal(ctx.parseMeasure('70% of annual target'), 0.7);
  assert.equal(ctx.parseMeasure('732 learners'), 732);
  assert.equal(ctx.parseMeasure('pending'), null);

  assert.equal(ctx.dueWindow(-1), 'Overdue');
  assert.equal(ctx.dueWindow(0), '0–30 days');
  assert.equal(ctx.dueWindow(30), '0–30 days');
  assert.equal(ctx.dueWindow(31), '31–60 days');
  assert.equal(ctx.dueWindow(61), '61+ days');

  assert.equal(ctx.fundingRange(0), '');
  assert.equal(ctx.fundingRange(50000), '<₹1 lakh');
  assert.equal(ctx.fundingRange(1000000), '₹1–10 lakh');
  assert.equal(ctx.fundingRange(1000001), '₹11–20 lakh');
  assert.equal(ctx.fundingRange(5000000), '₹21–50 lakh');
  assert.equal(ctx.fundingRange(5000001), '>₹50 lakh');

  assert.equal(ctx.durationBucket(1), 'Year 1');
  assert.equal(ctx.durationBucket(5), 'Years 2–5');
  assert.equal(ctx.durationBucket(6), 'Years 6–10');
  assert.equal(ctx.durationBucket(11), 'Years 11+');

  const m = [{ aspect: 'Capacity', status: 'Green' }, { aspect: 'Capacity', status: 'Red' }, { aspect: 'Clarity', status: 'Amber' }];
  assert.equal(ctx.worstRag(m, 'Capacity'), 'Red');
  assert.equal(ctx.worstRag(m, 'Compliance'), '');

  const outcomes = [
    { q1_status: 'On Track', q2_status: 'On Track', q3_status: '' },
    { q1_status: 'On Track', q2_status: 'Off Track', q3_status: '' },
  ];
  assert.equal(ctx.grantPerformanceStatus(outcomes), 'Off Track'); // latest reported quarter is Q2
  assert.equal(ctx.grantPerformanceStatus([{}]), '');

  assert.equal(ctx.mapDecisionStatus("Anagha's Recommendation"), 'Pending');
  assert.equal(ctx.mapDecisionStatus('Decision Locked'), 'Decided');
});
