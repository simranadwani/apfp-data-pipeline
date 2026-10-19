// Dumps the real column lists from the Apps Script files as JSON, for the lineage generator.
// Usage: node docs/lineage/export_model.js > docs/lineage/code_columns.json
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.join(__dirname, '..', '..');
const FILES = ['Utilities.js', 'Index.js', 'Staging.js', 'Final.js', 'LineageData.js', 'Lineage.js', 'SourceHeaderCheck.js', 'Tests.js', 'Pipeline.js'];
const ctx = { Utilities: {}, Session: {}, SpreadsheetApp: {}, MailApp: {}, Logger: {}, console };
vm.createContext(ctx);
const code = FILES.map((f) => fs.readFileSync(path.join(ROOT, f), 'utf8')).join('\n;\n');
vm.runInContext(code + '\n;globalThis.__out = { STAGING_SPECS, INDEX_DEFAULTS, FCT: { fct1_grant_portfolio: FCT1_HEADERS, fct2_outcome_progress: FCT2_HEADERS, fct3_support_activity: FCT3_HEADERS, fct4_budget_year: FCT4_HEADERS, fct5_maturity_rag: FCT5_HEADERS, fct6_grantee_annual_info: FCT6_HEADERS }, CARDINALITY_SPECS };', ctx);
const o = ctx.__out;
const stg = {};
Object.keys(o.STAGING_SPECS).forEach((k) => {
  const sp = o.STAGING_SPECS[k];
  const idx = o.INDEX_DEFAULTS.find((r) => r[0] === k);
  const src = o.INDEX_DEFAULTS.find((r) => r[0] === sp.src);
  stg[idx[1]] = { source_tab: src[1], columns: sp.columns.map((c) => ({ name: c[0], source_header: c[1], type: c[2] })), required: sp.required || [] };
});
const card = {};
o.CARDINALITY_SPECS.forEach((sp) => {
  const idx = o.INDEX_DEFAULTS.find((r) => r[0] === sp.key);
  const cols = sp.pk.slice();
  if (sp.grantFk && !cols.includes('grant_id')) cols.push('grant_id');
  if (sp.orgFk && !cols.includes('organization_id')) cols.push('organization_id');
  card[idx[1]] = cols;
});
console.log(JSON.stringify({ staging: stg, final: o.FCT, cardinality: card }, null, 1));
