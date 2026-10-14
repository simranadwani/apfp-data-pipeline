/**
 * Lineage.gs - two plain-language tabs that answer "where does this number come from?".
 *   Data_Dictionary: one row per dashboard-ready column (what it holds, how it is made, source tab and column, charts that use it).
 *   Chart_Passport:  one row per dashboard chart or tile (what it shows, filter, table, columns, source tabs).
 * The wording lives in LineageData.js, generated from docs/lineage/lineage_model.py and chart_passport.py.
 */

const DATA_DICTIONARY_HEADERS = ['dashboard_table', 'table_tab', 'column', 'what_it_holds', 'how_it_is_made', 'source_tabs', 'source_columns', 'used_in_charts', 'last_refreshed'];
const CHART_PASSPORT_HEADERS = ['chart', 'dashboard_page', 'chart_name', 'what_it_shows', 'filter_applied', 'dashboard_table', 'table_tab', 'columns_used', 'source_tabs', 'last_refreshed'];

/** [LINEAGE_DATA table key, Index key, live header list] for the final tables. */
function lineageTables() {
  return [
    ['fct1_grant_portfolio', 'FCT1_GRANT_PORTFOLIO', FCT1_HEADERS],
    ['fct2_outcome_progress', 'FCT2_OUTCOME_PROGRESS', FCT2_HEADERS],
    ['fct3_support_activity', 'FCT3_SUPPORT_ACTIVITY', FCT3_HEADERS],
    ['fct4_budget_year', 'FCT4_BUDGET_YEAR', FCT4_HEADERS],
    ['fct5_maturity_rag', 'FCT5_MATURITY_RAG', FCT5_HEADERS],
    ['fct6_grantee_annual_info', 'FCT6_GRANTEE_ANNUAL_INFO', FCT6_HEADERS],
  ];
}

function buildDataDictionary(ss, idx) {
  const today = formatIsoDate(new Date());
  const chartNames = {};
  LINEAGE_DATA.charts.forEach(function (c) { chartNames[c.id] = c.id + ' ' + c.name; });
  const rows = [];
  lineageTables().forEach(function (t) {
    const info = LINEAGE_DATA.tables[t[0]];
    t[2].forEach(function (col) {
      const e = LINEAGE_DATA.columns[t[0] + '.' + col] || { meaning: '', how: '', source_tabs: [], source_columns: [], charts: [] };
      rows.push([info.name, idx[t[1]] || t[0], col, e.meaning, e.how, e.source_tabs.join('; '), e.source_columns.join('; '),
        e.charts.map(function (id) { return chartNames[id]; }).join('; '), today]);
    });
  });
  return writeSheet(ss, idx.DOC_DATA_DICTIONARY, DATA_DICTIONARY_HEADERS, rows);
}

function buildChartPassport(ss, idx) {
  const today = formatIsoDate(new Date());
  const rows = LINEAGE_DATA.charts.map(function (c) {
    const key = lineageTables().filter(function (t) { return t[0] === c.table; })[0][1];
    return [c.id, c.page, c.name, c.shows, c.filter, LINEAGE_DATA.tables[c.table].name, idx[key] || c.table,
      c.columns.join(', '), c.source_tabs.join('; '), today];
  });
  return writeSheet(ss, idx.DOC_CHART_PASSPORT, CHART_PASSPORT_HEADERS, rows);
}
