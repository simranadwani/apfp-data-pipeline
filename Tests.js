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
  { key: 'FCT2_OUTCOME_PROGRESS', pk: ['grant_id', 'outcome_id', 'quarter'], grantFk: true },
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
    const rows = readSheetSafe(ss, table);
    function record(test, ok, detail) { results.push([now, table, test, ok ? 'PASS' : 'FAIL', detail || '']); }

    record('has_rows', rows.length > 0, rows.length + ' row(s)');
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

  writeSheet(ss, idx.UTIL_CARDINALITY_TESTS, CARDINALITY_TEST_HEADERS, results);
  const failed = results.filter(function (r) { return r[3] === 'FAIL'; });
  log(ss, idx, failed.length ? 'WARN' : 'INFO', 'runCardinalityTests', results.length,
    failed.length ? failed.length + ' test(s) failed: ' + failed.map(function (r) { return r[1] + ' ' + r[2]; }).slice(0, 5).join('; ')
      : 'All ' + results.length + ' tests passed',
    Date.now() - start, 'SUCCESS');
  return failed.length;
}
