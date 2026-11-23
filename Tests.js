/**
 * Tests.gs — cardinality tests run after every full pipeline run (SoP 6.3).
 * Checks every table has rows, primary keys are unique and not null, and that
 * grant_id / organization_id values resolve to the registries.
 */

const CARDINALITY_TEST_HEADERS = ['checked_at', 'table', 'test', 'status', 'detail'];

const CARDINALITY_SPECS = [
  { key: 'STG_GRANTS', pk: ['grant_id'] },
  { key: 'STG_ORGANISATIONS', pk: ['organization_id'] },
  { key: 'STG_OUTCOME_PROGRESS', pk: ['grant_id', 'outcome_id'], grantFk: true },
  { key: 'STG_SUPPORT', pk: [], grantFk: true },
  { key: 'STG_DECISIONS', pk: ['grant_id'], grantFk: true },
  { key: 'STG_DIVIDENDS', pk: ['financial_year'] },
  { key: 'STG_DISBURSEMENTS', pk: ['disbursement_id'], grantFk: true },
  { key: 'STG_MATURITY', pk: ['grant_id', 'aspect', 'indicator'], grantFk: true },
  { key: 'FCT1_GRANT_PORTFOLIO', pk: ['grant_id'], orgFk: true },
  { key: 'FCT2_OUTCOME_PROGRESS', pk: ['grant_id', 'outcome_id'], label: 'placeholder rows', where: function (r) { return r.has_update === false; } },
  { key: 'FCT2_OUTCOME_PROGRESS', pk: ['grant_id', 'outcome_id', 'quarter'], grantFk: true, label: 'reported rows', where: function (r) { return r.has_update === true; } },
  { key: 'FCT3_SUPPORT_ACTIVITY', pk: ['support_id'], grantFk: true },
  { key: 'FCT4_BUDGET_YEAR', pk: ['financial_year'] },
  { key: 'FCT5_MATURITY_RAG', pk: ['grant_id', 'aspect', 'indicator'], grantFk: true },
  { key: 'FCT6_GRANTEE_ANNUAL_INFO', pk: ['grant_id', 'metric'], grantFk: true },
];

/** Menu / editor entry point. Returns the number of failed tests. */
function runCardinalityTests(ss, idx) {
  ss = ss || getPipelineSpreadsheet();
  idx = idx || getSheetIndex(ss);
  const start = Date.now();
  const now = formatTimestamp(new Date());
  const results = [];
  const grantIds = indexBy(readSheetSafe(ss, idx.STG_GRANTS), 'grant_id');
  const orgIds = indexBy(readSheetSafe(ss, idx.STG_ORGANISATIONS), 'organization_id');

  CARDINALITY_SPECS.forEach(function (spec) {
    const table = idx[spec.key];
    const allRows = readSheetSafe(ss, table);
    const rows = spec.where ? allRows.filter(spec.where) : allRows;
    const suffix = spec.label ? ' [' + spec.label + ']' : '';
    function record(test, ok, detail) { results.push([now, table, test + suffix, ok ? 'PASS' : 'FAIL', detail || '']); }

    if (!spec.label) record('has_rows', rows.length > 0, rows.length + ' row(s)');
    if (spec.pk.length) {
      const nulls = rows.filter(function (r) { return spec.pk.some(function (c) { return isBlank(r[c]); }); }).length;
      record('not_null(' + spec.pk.join(', ') + ')', nulls === 0, nulls ? nulls + ' row(s) with a blank key' : '');
      const seen = {};
      const dups = [];
      rows.forEach(function (r) {
        const k = key.apply(null, spec.pk.map(function (c) { return r[c]; }));
        if (seen[k]) dups.push(k);
        seen[k] = true;
      });
      record('unique(' + spec.pk.join(', ') + ')', dups.length === 0, dups.length ? dups.slice(0, 5).join('; ') : '');
    }
    if (spec.grantFk) {
      const bad = rows.filter(function (r) { return !grantIds[r.grant_id]; }).map(function (r) { return r.grant_id; });
      record('relationship(grant_id → stg_grants)', bad.length === 0, bad.length ? bad.slice(0, 5).join(', ') : '');
    }
    if (spec.orgFk) {
      const bad = rows.filter(function (r) { return !orgIds[r.organization_id]; }).map(function (r) { return r.organization_id; });
      record('relationship(organization_id → stg_organisations)', bad.length === 0, bad.length ? bad.slice(0, 5).join(', ') : '');
    }
  });

  // Every outcome defined in stg_outcome_progress must appear in fct2, reported or not.
  const fct2Outcomes = {};
  readSheetSafe(ss, idx.FCT2_OUTCOME_PROGRESS).forEach(function (r) { fct2Outcomes[key(r.grant_id, r.outcome_id)] = true; });
  const missing = readSheetSafe(ss, idx.STG_OUTCOME_PROGRESS).filter(function (r) { return !fct2Outcomes[key(r.grant_id, r.outcome_id)]; });
  results.push([now, idx.FCT2_OUTCOME_PROGRESS, 'covers_every_outcome(stg_outcome_progress)', missing.length ? 'FAIL' : 'PASS',
    missing.length ? missing.length + ' outcome(s) missing, e.g. ' + missing.slice(0, 3).map(function (r) { return r.grant_id + '/' + r.outcome_id; }).join(', ') : '']);

  writeSheet(ss, idx.UTIL_CARDINALITY_TESTS, CARDINALITY_TEST_HEADERS, results);
  const failed = results.filter(function (r) { return r[3] === 'FAIL'; });
  log(ss, idx, failed.length ? 'WARN' : 'INFO', 'runCardinalityTests', results.length,
    failed.length ? failed.length + ' test(s) failed: ' + failed.map(function (r) { return r[1] + ' ' + r[2]; }).slice(0, 5).join('; ')
      : 'All ' + results.length + ' tests passed',
    Date.now() - start, 'SUCCESS');
  return failed.length;
}

/**
 * Read-only audit (run from the Apps Script editor, read the Execution log): lists every fct column whose cells carry a
 * date format although the column is not a date column. The pipeline itself never sets formats; the sheet's Table owns them.
 */
function auditOutputFormats() {
  const ss = getPipelineSpreadsheet();
  const idx = getSheetIndex(ss);
  const bad = [];
  ['FCT1_GRANT_PORTFOLIO', 'FCT2_OUTCOME_PROGRESS', 'FCT3_SUPPORT_ACTIVITY', 'FCT4_BUDGET_YEAR', 'FCT5_MATURITY_RAG', 'FCT6_GRANTEE_ANNUAL_INFO'].forEach(function (k) {
    const sheet = ss.getSheetByName(idx[k]);
    if (!sheet || sheet.getLastRow() < 2) return;
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    const formats = sheet.getRange(2, 1, 1, headers.length).getNumberFormats()[0];
    headers.forEach(function (h, i) {
      const unquoted = String(formats[i]).replace(/"[^"]*"/g, '').replace(/\\./g, '');
      const dateLike = /y|d{1,2}|m{2,}/i.test(unquoted) && !/^(0|#|\[)/.test(unquoted);
      const isDateColumn = /_date$/.test(h) || h === 'as_of_date';
      if (dateLike && !isDateColumn) bad.push(idx[k] + '.' + h + '  ' + formats[i]);
    });
  });
  Logger.log(bad.length ? 'Date-formatted columns that are not dates:\n' + bad.join('\n') : 'No non-date column has a date format.');
  return bad;
}
