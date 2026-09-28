/**
 * SourceHeaderCheck.gs — gate that runs before staging (SoP 6.4).
 * Compares live source headers with ref_source_header_baseline and writes the
 * result to Source_Header_Audit. A missing column that staging needs is CRITICAL
 * and stops the pipeline. Other differences are WARN / INFO for review.
 */

const BASELINE_HEADERS = ['source_key', 'sheet_name', 'column_position', 'header', 'is_required'];
const AUDIT_HEADERS = ['checked_at', 'source_tab', 'issue_type', 'severity', 'header', 'expected_position', 'actual_position', 'message'];

/** Source headers each source tab must have, taken from the staging specs. */
function requiredSourceHeaders() {
  const req = {};
  Object.keys(STAGING_SPECS).forEach(function (stgKey) {
    const spec = STAGING_SPECS[stgKey];
    req[spec.src] = (req[spec.src] || []).concat(spec.columns.map(function (c) { return c[1]; }));
  });
  return req;
}

function sourceKeys() {
  return INDEX_DEFAULTS.filter(function (r) { return r[2] === 'src'; }).map(function (r) { return r[0]; });
}

/** Snapshots the current source headers as the new baseline. Re-run after an agreed source change. */
function setupSourceHeaderBaseline() {
  const ss = getPipelineSpreadsheet();
  const idx = getSheetIndex(ss);
  return writeSourceHeaderBaseline(ss, idx);
}

function writeSourceHeaderBaseline(ss, idx) {
  const src = getSourceSpreadsheet();
  const required = requiredSourceHeaders();
  const rows = [];
  sourceKeys().forEach(function (k) {
    const headers = readSheetWithHeaders(src, idx[k]).headers;
    headers.forEach(function (h, i) {
      if (h) rows.push([k, idx[k], i + 1, h, (required[k] || []).indexOf(h) !== -1]);
    });
  });
  return writeSheet(ss, idx.REF_SOURCE_HEADER_BASELINE, BASELINE_HEADERS, rows);
}

/** Returns { critical, warnings }. Throws nothing itself; the caller decides whether to stop. */
function runSourceHeaderCheck(ss, idx) {
  if (readSheetSafe(ss, idx.REF_SOURCE_HEADER_BASELINE).length === 0) {
    writeSourceHeaderBaseline(ss, idx);
    log(ss, idx, 'WARN', 'runSourceHeaderCheck', 0, 'No header baseline found; created one from the current source headers', null, 'SUCCESS');
  }
  const baseline = groupBy(readSheet(ss, idx.REF_SOURCE_HEADER_BASELINE), 'source_key');
  const required = requiredSourceHeaders();
  const src = getSourceSpreadsheet();
  const now = formatTimestamp(new Date());
  const issues = [];

  function issue(tab, type, severity, header, expected, actual, message) {
    issues.push([now, tab, type, severity, header, expected, actual, message]);
  }

  sourceKeys().forEach(function (k) {
    const tab = idx[k];
    if (!src.getSheetByName(tab)) {
      issue(tab, 'Missing Tab', 'CRITICAL', '', '', '', 'Source tab not found. Fix the tab name in the source or in the Index tab.');
      return;
    }
    const live = readSheetWithHeaders(src, tab).headers;
    const livePos = {};
    live.forEach(function (h, i) { if (h) livePos[h] = i + 1; });
    const expected = (baseline[k] || []).slice().sort(function (a, b) { return a.column_position - b.column_position; });
    const expectedSet = {};
    expected.forEach(function (e) { expectedSet[e.header] = e.column_position; });
    const req = required[k] || [];

    expected.forEach(function (e) {
      if (livePos[e.header]) return;
      const atSamePos = live[e.column_position - 1];
      const renamedTo = atSamePos && !expectedSet[atSamePos] ? atSamePos : '';
      const isReq = req.indexOf(e.header) !== -1;
      issue(tab, renamedTo ? 'Renamed Header' : 'Missing Column', isReq ? 'CRITICAL' : 'WARN', e.header, e.column_position,
        renamedTo ? e.column_position : '',
        (renamedTo ? 'Looks renamed to "' + renamedTo + '". ' : '') +
        (isReq ? 'Used by the pipeline: correct it in the source before running.' : 'Not used by the pipeline: update the baseline if this change is intended.'));
    });
    // Required headers that are not in the baseline either (e.g. baseline taken after a bad edit).
    req.forEach(function (h) {
      if (!livePos[h] && !expectedSet[h]) {
        issue(tab, 'Missing Column', 'CRITICAL', h, '', '', 'Used by the pipeline but missing from the source.');
      }
    });
    live.forEach(function (h, i) {
      if (h && !expectedSet[h]) {
        issue(tab, 'New Header Added', 'WARN', h, '', i + 1, 'Review whether the pipeline should use this column, then re-run setupSourceHeaderBaseline().');
      }
    });
    const moved = expected.filter(function (e) { return livePos[e.header] && livePos[e.header] !== e.column_position; });
    if (moved.length) {
      issue(tab, 'Header Order Changed', 'INFO', moved.map(function (e) { return e.header; }).slice(0, 5).join(', '), '', '',
        moved.length + ' column(s) moved. The pipeline reads columns by name, so no action is needed.');
    }
  });

  if (!issues.length) issue('(all source tabs)', 'OK', 'INFO', '', '', '', 'All source headers match the baseline.');
  writeSheet(ss, idx.UTIL_SOURCE_HEADER_AUDIT, AUDIT_HEADERS, issues);
  return {
    critical: issues.filter(function (r) { return r[3] === 'CRITICAL'; }).length,
    warnings: issues.filter(function (r) { return r[3] === 'WARN'; }).length,
  };
}
