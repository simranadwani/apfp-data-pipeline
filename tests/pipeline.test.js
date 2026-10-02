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
    fct4_budget_year: 4, fct5_maturity_rag: 18, fct6_grantee_annual_info: 144,
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
  assert.equal(brigh.financial_year, 'FY 26-27');
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

test('fct2 carries target text, annual achievement and the latest notes on every quarter row', () => {
  const h = runFull();
  const rows = h.tab('fct2_outcome_progress').filter((r) => r.grant_id === 'BRIGH_01_202627_301');
  assert.equal(rows.length, 4);
  rows.forEach((r) => {
    assert.equal(r.target_text, '70% of annual target');
    assert.equal(r.final_actual_value, 0.8); // "80% achieved"
    assert.ok(Math.abs(r.annual_achievement_pct - 0.8 / 0.7) < 1e-9);
    assert.equal(r.latest_notes, 'Dummy Q4 review note 1'); // notes of the latest reported quarter (Q4)
  });
  // Distinct outcome rows never mix: each outcome keeps its own annual figures.
  const all = h.tab('fct2_outcome_progress');
  const byOutcome = {};
  all.forEach((r) => { (byOutcome[r.outcome_id] = byOutcome[r.outcome_id] || new Set()).add(r.annual_achievement_pct); });
  Object.values(byOutcome).forEach((set) => assert.equal(set.size, 1));
});

test('grant_status is present on fct2, fct3 and fct5 so the Grant Status filter reaches every table', () => {
  const h = runFull();
  const grantStatus = Object.fromEntries(h.tab('fct1_grant_portfolio').map((r) => [r.grant_id, r.grant_status]));
  ['fct2_outcome_progress', 'fct3_support_activity', 'fct5_maturity_rag'].forEach((tab) => {
    const rows = h.tab(tab);
    assert.ok(rows.length > 0, tab);
    rows.forEach((r) => {
      assert.ok(r.grant_status !== '', tab + ' has a blank grant_status for ' + r.grant_id);
      assert.equal(r.grant_status, grantStatus[r.grant_id], tab + ' ' + r.grant_id);
    });
  });
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

test('fct3 response_category comes from the source "Support Provided" column, values untouched', () => {
  const h = runFull();
  const src = require('./fixtures/source_dummy.json')['3. Support'];
  const hdr = src[1];
  const gi = hdr.indexOf('Grant ID'), pi = hdr.indexOf('Support Provided');
  const expected = src.slice(2).filter((r) => r[gi] !== '').map((r) => r[pi]);
  assert.equal(expected.length, 18);
  assert.deepEqual(h.tab('stg_support').map((r) => r.support_provided), expected);
  assert.deepEqual(h.tab('fct3_support_activity').map((r) => r.response_category), expected);
  assert.ok(expected.every((v) => v !== ''), 'the fixture should have a value on every request');
  assert.ok(h.tab('fct3_support_activity').every((r) => r.response_date === '')); // the source still has no response date
});

test('Support Provided is the last column of stg_support and fct3 (existing columns keep their positions)', () => {
  const h = runFull();
  const last = (name) => { const hd = h.pipeline.getSheetByName(name).data[0]; return hd[hd.length - 1]; };
  assert.equal(last('stg_support'), 'support_provided');
  assert.equal(last('fct3_support_activity'), 'response_category');
});

test('a request with no "Support Provided" yet has a blank response_category (not counted as a response)', () => {
  const src = clone(require('./fixtures/source_dummy.json'));
  const hdr = src['3. Support'][1];
  src['3. Support'][2][hdr.indexOf('Support Provided')] = ''; // first request: nothing provided yet
  const h = runFull(src);
  const rows = h.tab('fct3_support_activity');
  assert.equal(rows[0].response_category, '');
  assert.equal(rows.filter((r) => r.response_category !== '').length, 17);
});

test('the staging header requirement catches a renamed "Support Provided" column', () => {
  const h = loadPipeline();
  h.ctx.runCompletePipeline(); // records the header baseline
  const hdr = h.source.getSheetByName('3. Support').data[1];
  hdr[hdr.indexOf('Support Provided')] = 'Support Given';
  assert.throws(() => h.ctx.runCompletePipeline(), /critical source header issue/);
  const issue = h.pipeline.getSheetByName('Source_Header_Audit').toObjects().find((r) => r.severity === 'CRITICAL');
  assert.equal(issue.header, 'Support Provided');
});

test('fct4 rolls the carry-forward and reserves next year Q1 commitments', () => {
  const h = runFull();
  const rows = h.tab('fct4_budget_year');
  assert.deepEqual(rows.map((r) => r.financial_year), ['FY 25-26', 'FY 26-27', 'FY 27-28', 'FY 28-29']);
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

test('pipeline workbook in another time zone is aligned to the script time zone before any write', () => {
  const h = loadPipeline(null, { pipelineTimeZone: 'America/Los_Angeles' });
  h.ctx.runCompletePipeline();
  assert.equal(h.pipeline.getSpreadsheetTimeZone(), 'Asia/Kolkata');
  const warn = h.pipeline.getSheetByName('Pipeline Log').toObjects().find((r) => r.function === 'alignTimeZones');
  assert.match(warn.message, /America\/Los_Angeles to Asia\/Kolkata/);
  // Second run: nothing to align, no new warning.
  h.ctx.runCompletePipeline();
  const warns = h.pipeline.getSheetByName('Pipeline Log').toObjects().filter((r) => r.function === 'alignTimeZones');
  assert.equal(warns.length, 1);
});

test('source workbook in another time zone is reported, not changed, and dates keep the source day', () => {
  // Midnight 1 Apr 2026 in Auckland is still 31 Mar in India: reading the day in the
  // script zone would give 31 Mar.
  const src = clone(require('./fixtures/source_dummy.json'));
  const reg = src['8. Grant Registry'];
  const col = reg[0].indexOf('Grant Start Date');
  reg[1][col] = { __date__: '2026-03-31T11:00:00.000Z' }; // = 2026-04-01 00:00 Pacific/Auckland
  const h = loadPipeline(src, { sourceTimeZone: 'Pacific/Auckland' });
  h.ctx.runCompletePipeline();
  assert.equal(h.source.getSpreadsheetTimeZone(), 'Pacific/Auckland');
  const brigh = h.pipeline.getSheetByName('fct1_grant_portfolio').toObjects().find((r) => r.grant_id === 'BRIGH_01_202627_301');
  assert.match(brigh.grant_period, /^2026-04-01 - /);
  assert.ok(h.pipeline.getSheetByName('Pipeline Log').toObjects().some((r) => /Source workbook time zone is Pacific\/Auckland/.test(r.message)));
});

test('the pipeline never sets a number format: dates and numbers are formatted by the sheet', () => {
  const h = runFull();
  Object.values(h.pipeline.sheets).forEach((sh) => {
    assert.equal(sh.formatCalls, 0, sh.name + ' had a number format set');
    assert.deepEqual(sh.numberFormats, {}, sh.name);
  });
});

// ---- Google Sheets Tables (typed columns) ----
const SNAPSHOT_TABS = /^(stg_|fct)/;
function snapshot(h) {
  return Object.fromEntries(Object.values(h.pipeline.sheets)
    .filter((sh) => SNAPSHOT_TABS.test(sh.name))
    .map((sh) => [sh.name, JSON.stringify(sh.data.slice(0, sh.getLastRow()))]));
}

test('after every tab is converted to a Table, the pipeline runs cleanly and output is identical', () => {
  const h = runFull();
  const before = snapshot(h);
  h.convertToTables();
  assert.doesNotThrow(() => h.ctx.runCompletePipeline());
  assert.deepEqual(snapshot(h), before);
  const log = h.tab('Pipeline Log');
  assert.equal(log.filter((r) => r.status === 'ERROR').length, 0);
  assert.equal(log.filter((r) => r.function === 'runCompletePipeline').pop().status, 'SUCCESS');
  Object.values(h.pipeline.sheets).forEach((sh) => {
    assert.equal(sh.formatCalls, 0, sh.name + ' had a number format set');
    if (/^(stg_|fct|ref_|Index|Source_Header_Audit|Cardinality)/.test(sh.name)) assert.equal(sh.headerClears, 0, sh.name + ' header row was cleared');
  });
});

test('a failing appendRow on the Pipeline Log never stops a run; entries go through the fallback', () => {
  const h = runFull();
  h.convertToTables();
  h.pipeline.getSheetByName('Pipeline Log').appendFails = true;
  const rowsBefore = h.tab('Pipeline Log').length;
  assert.doesNotThrow(() => h.ctx.runCompletePipeline());
  const log = h.tab('Pipeline Log');
  assert.equal(log.length - rowsBefore, 16); // 8 staging + 6 fact + cardinality tests + run summary
  assert.equal(log.filter((r) => r.status === 'ERROR').length, 0);
  assert.equal(log.pop().function, 'runCompletePipeline');
});

test('even if the Pipeline Log cannot be written at all, the run still completes and logs to Apps Script', () => {
  const h = runFull();
  h.pipeline.getSheetByName('Pipeline Log').failAllWrites = true;
  h.logs.length = 0;
  assert.doesNotThrow(() => h.ctx.runCompletePipeline());
  assert.ok(h.logs.some((l) => /runCompletePipeline/.test(l) && /SUCCESS/.test(l)));
  assert.ok(h.logs.some((l) => /buildFct1GrantPortfolio/.test(l)));
});

test('a run with fewer rows than before leaves no stale rows and keeps the header', () => {
  const h = runFull();
  h.source.getSheetByName('3. Support').data.splice(3, 5); // 5 support requests removed
  h.convertToTables();
  h.ctx.runCompletePipeline();
  ['stg_support', 'fct3_support_activity'].forEach((tab) => {
    const sh = h.pipeline.getSheetByName(tab);
    assert.equal(sh.getLastRow(), 14, tab + ' should have header + 13 rows');
    assert.equal(sh.data.length, 14, tab + ' still has stale rows');
    assert.equal(sh.headerClears, 0);
  });
  assert.equal(h.tab('fct3_support_activity').length, 13);
});

test('schema growth (v0.1.2 added columns) and shrinkage both write cleanly on a Table', () => {
  const h = runFull();
  const fct2 = h.pipeline.getSheetByName('fct2_outcome_progress');
  const fullWidth = fct2.getLastColumn();
  fct2.data = fct2.data.map((r) => r.slice(0, 15));             // pretend the Table is the old 15-column version
  const stg = h.pipeline.getSheetByName('stg_support');
  const extraCol = stg.getLastColumn();
  stg.data.forEach((r, i) => { r[extraCol] = i === 0 ? 'old_extra_column' : 'stale'; }); // a column the new schema no longer has
  h.convertToTables();
  assert.doesNotThrow(() => h.ctx.runCompletePipeline());
  assert.equal(fct2.getLastColumn(), fullWidth);
  assert.ok(Object.keys(h.tab('fct2_outcome_progress')[0]).includes('annual_achievement_pct'));
  assert.ok(!Object.keys(h.tab('stg_support')[0]).includes('old_extra_column'));
  assert.equal(stg.headerClears, 0);
});

test('a run with no data rows keeps a header and one blank row (a Table needs a body)', () => {
  const src = clone(require('./fixtures/source_dummy.json'));
  const h = loadPipeline(src);
  h.tab = (name) => h.pipeline.getSheetByName(name).toObjects();
  h.ctx.runCompletePipeline();
  h.convertToTables();
  h.source.getSheetByName('3. Support').data.splice(2);         // header only
  assert.doesNotThrow(() => h.ctx.runCompletePipeline());
  assert.equal(h.tab('stg_support').length, 0);
  assert.equal(h.pipeline.getSheetByName('stg_support').getLastRow(), 1);
});

test('every numeric and date output column has a format in tests/column_formats.js', () => {
  const { FORMATS } = require('./column_formats');
  const h = runFull();
  Object.entries(FORMATS).forEach(([tab, groups]) => {
    const listed = Object.values(groups).flat();
    assert.equal(new Set(listed).size, listed.length, tab + ' lists a column twice');
    const rows = h.tab(tab);
    const cols = Object.keys(rows[0]);
    listed.forEach((c) => assert.ok(cols.includes(c), tab + ' lists unknown column ' + c));
    cols.forEach((c) => {
      const numeric = rows.some((r) => typeof r[c] === 'number' || isDate(r[c]));
      if (numeric) assert.ok(listed.includes(c), tab + '.' + c + ' is numeric/date but has no format');
      else assert.ok(!listed.includes(c), tab + '.' + c + ' is listed but holds no numbers or dates');
    });
  });
  ['stg_', 'fct'].forEach((prefix) => Object.keys(h.pipeline.sheets).filter((n) => n.startsWith(prefix)).forEach((n) => assert.ok(FORMATS[n], n + ' missing from column_formats.js')));
});

test('helper rules', () => {
  const { ctx } = loadPipeline();
  // every accepted input gives the one format, "FY 26-27"
  ['April 25-March 26', '2025-26', 'FY 25-26', 'FY25-26', '2025-2026'].forEach((v) => assert.equal(ctx.normaliseFinancialYear(v), 'FY 25-26', v));
  assert.equal(ctx.normaliseFinancialYear('next year'), '');
  assert.equal(ctx.nextFinancialYear('FY 26-27'), 'FY 27-28');
  assert.equal(ctx.nextFinancialYear('FY 99-00'), 'FY 00-01');
  assert.equal(ctx.previousFinancialYear('FY 26-27'), 'FY 25-26');
  assert.equal(ctx.previousFinancialYear('FY 00-01'), 'FY 99-00');
  assert.equal(ctx.previousFinancialYear('2026-27'), ''); // only the one format is accepted here
  assert.equal(ctx.nextFinancialYear(''), '');

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

test('fct6 puts each metric on its own row with the selected and previous year side by side', () => {
  const h = runFull();
  const rows = h.tab('fct6_grantee_annual_info');
  const mine = rows.filter((r) => r.grant_id === 'SAKHI_02_202627_302');
  assert.deepEqual(mine.map((r) => r.metric), ['Financial year', 'Annual budget', '% Annual Budget funded by APFP', 'Team size', 'Attrition', 'Core policies', 'FCRA registration', 'Foreign contribution share']);
  const v = Object.fromEntries(mine.map((r) => [r.metric, r.current_value]));
  assert.equal(v['Financial year'], 'FY 26-27');
  assert.equal(v['Annual budget'], '\u20B954,00,000');
  assert.equal(v['% Annual Budget funded by APFP'], '24%'); // 1275000 / 5400000
  assert.equal(v['Team size'], '13');
  assert.equal(v['Attrition'], '11%');
  assert.equal(v['Core policies'], '4 / 4');
  assert.equal(v['FCRA registration'], 'Application in Process');
  assert.equal(v['Foreign contribution share'], '5%');
  assert.ok(mine.every((r) => r.previous_financial_year === 'FY 25-26'));
  // no FY 25-26 grant in the sample data: the label row still names the previous year, the rest are dashes
  const prev = Object.fromEntries(mine.map((r) => [r.metric, r.previous_value]));
  assert.equal(prev['Financial year'], 'FY 25-26');
  assert.ok(mine.filter((r) => r.metric !== 'Financial year').every((r) => r.previous_value === '\u2013'));
});

test('fct6 previous_value comes from the same organisation in the year before', () => {
  const h = runFull();
  const fct1 = h.pipeline.getSheetByName('fct1_grant_portfolio');
  const hdr = fct1.data[0];
  const col = (n) => hdr.indexOf(n);
  const row = fct1.data[1].slice();
  row[col('grant_id')] = 'TEST_PREV'; row[col('financial_year')] = 'FY 25-26'; row[col('annual_budget')] = 3600000; row[col('team_size')] = 67;
  fct1.data.push(row); // an earlier-year grant of the same organisation as data row 1
  h.ctx.buildFct6GranteeAnnualInfo(h.pipeline, h.ctx.getSheetIndex(h.pipeline));
  const rows = h.tab('fct6_grantee_annual_info').filter((r) => r.grant_id === fct1.data[1][col('grant_id')]);
  const v = Object.fromEntries(rows.map((r) => [r.metric, r]));
  assert.equal(v['Annual budget'].previous_value, '\u20B936,00,000');
  assert.equal(v['Team size'].previous_value, '67');
  assert.equal(v['Financial year'].previous_value, 'FY 25-26');
});

test('fct5 aspect_display shows the aspect once per block and keeps blanks after it', () => {
  const h = runFull();
  const rows = h.tab('fct5_maturity_rag');
  rows.forEach((r, i) => {
    const sameBlock = i > 0 && rows[i - 1].grant_id === r.grant_id && rows[i - 1].aspect === r.aspect;
    assert.equal(r.aspect_display, sameBlock ? '' : r.aspect);
  });
  assert.equal(rows.filter((r) => r.aspect_display !== '').length > 0, true);
});

test('formatInr groups digits the Indian way', () => {
  const h = loadPipeline();
  const f = h.ctx.formatInr;
  assert.equal(f(960), '\u20B9960');
  assert.equal(f(96000), '\u20B996,000');
  assert.equal(f(750000), '\u20B97,50,000');
  assert.equal(f(86000000), '\u20B98,60,00,000');
  assert.equal(f(-9675000), '-\u20B996,75,000');
  assert.equal(f('x'), '');
});

test('an Index tab from an older release gets the new rows appended and keeps renamed tabs', () => {
  const h = runFull();
  const index = h.pipeline.getSheetByName('Index');
  const hdr = index.data[0];
  const keyCol = hdr.indexOf('key'), nameCol = hdr.indexOf('sheet_name');
  index.data = index.data.filter((r) => r[keyCol] !== 'FCT6_GRANTEE_ANNUAL_INFO'); // as it was before this release
  index.data.find((r) => r[keyCol] === 'FCT1_GRANT_PORTFOLIO')[nameCol] = 'my_fct1';
  const idx = h.ctx.getSheetIndex(h.pipeline);
  assert.equal(idx.FCT6_GRANTEE_ANNUAL_INFO, 'fct6_grantee_annual_info');
  assert.equal(idx.FCT1_GRANT_PORTFOLIO, 'my_fct1');
  const keys = h.tab('Index').map((r) => r.key);
  assert.equal(keys.filter((k) => k === 'FCT6_GRANTEE_ANNUAL_INFO').length, 1);
});

test('every financial_year value in every stg_ and fct_ tab uses the one format "FY yy-yy"', () => {
  const h = runFull();
  let checked = 0;
  Object.keys(h.pipeline.sheets).filter((n) => /^(stg|fct)/.test(n)).forEach((n) => {
    h.tab(n).forEach((r) => ['financial_year', 'previous_financial_year', 'decision_for_fy', 'previous_grant_fy'].forEach((c) => {
      if (c in r && r[c] !== '') { assert.match(r[c], /^FY \d{2}-\d{2}$/, n + '.' + c + ' = ' + r[c]); checked++; }
    }));
  });
  assert.ok(checked > 100);
});

test('fct6 filtered to one financial year shows exactly that year and the year before it', () => {
  const h = runFull();
  const rows = h.tab('fct6_grantee_annual_info').filter((r) => r.financial_year === 'FY 27-28');
  assert.ok(rows.length > 0);
  assert.ok(rows.every((r) => r.previous_financial_year === 'FY 26-27'));
  const labels = rows.filter((r) => r.metric === 'Financial year');
  assert.ok(labels.every((r) => r.current_value === 'FY 27-28' && r.previous_value === 'FY 26-27'));
});
