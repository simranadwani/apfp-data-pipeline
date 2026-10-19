// Compares the draw.io lineage diagram with the real column lists in the scripts.
// Usage: npm run lineage      (exit code 1 when something is missing or stale)
// - every staging column and every final column must appear in the diagram, under its table;
// - every column in the diagram must still exist in the code (stale rows are listed).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const FILE = path.join(ROOT, 'docs', 'lineage', 'APFP_Data_Lineage.drawio');
const code = JSON.parse(execFileSync('node', [path.join(ROOT, 'docs', 'lineage', 'export_model.js')], { encoding: 'utf8' }));
const xml = fs.readFileSync(FILE, 'utf8');

function attr(tag, name) {
  const m = new RegExp(name + '="([^"]*)"').exec(tag);
  return m ? m[1] : null;
}
// Ids repeat from page to page, so every <diagram> page is read on its own.
// <object label=".." id=".." tech="..."><mxCell ... parent="..."> ... </object>
const expected = {};
Object.entries(code.staging).forEach(([t, v]) => { expected[t] = new Set(v.columns.map((c) => c.name)); });
Object.entries(code.final).forEach(([t, cols]) => { expected[t] = new Set(cols); });

const seen = {};
(xml.match(/<diagram [\s\S]*?<\/diagram>/g) || []).forEach((page) => {
  const objects = [];
  const re = /<object ([^>]*)>\s*<mxCell ([^>]*)>/g;
  let m;
  while ((m = re.exec(page))) objects.push({ id: attr(m[1], 'id'), tech: attr(m[1], 'tech'), parent: attr(m[2], 'parent') });
  const byParent = {};
  objects.forEach((o) => { (byParent[o.parent] = byParent[o.parent] || []).push(o); });
  objects.filter((o) => o.tech && expected[o.tech] && (byParent[o.id] || []).length).forEach((table) => {
    seen[table.tech] = seen[table.tech] || new Set();
    (byParent[table.id] || []).forEach((r) => { if (r.tech) seen[table.tech].add(r.tech); });
  });
});

let problems = 0;
Object.keys(expected).forEach((t) => {
  const have = seen[t] || new Set();
  const missing = [...expected[t]].filter((c) => !have.has(c));
  const stale = [...have].filter((c) => !expected[t].has(c));
  if (!seen[t]) { console.log('MISSING TABLE in the diagram: ' + t); problems++; return; }
  if (missing.length) { console.log(t + ': in the code, not in the diagram -> ' + missing.join(', ')); problems += missing.length; }
  if (stale.length) { console.log(t + ': in the diagram, no longer in the code -> ' + stale.join(', ')); problems += stale.length; }
});
console.log(problems ? '\n' + problems + ' difference(s). Update docs/lineage/lineage_model.py and rebuild, or edit the diagram by hand.' : 'Lineage diagram matches the code (' + Object.keys(expected).length + ' tables checked).');

// Second diagram: docs/lineage/APFP_Data_Lineage_v2.drawio (native tables; every row object carries layer, table, column).
const V2 = path.join(ROOT, 'docs', 'lineage', 'APFP_Data_Lineage_v2.drawio');
if (fs.existsSync(V2)) {
  const xml2 = fs.readFileSync(V2, 'utf8');
  const seen2 = {};
  const re2 = /<object [^>]*?layer="([^"]*)" table="([^"]*)" column="([^"]*)"/g;
  let m2;
  while ((m2 = re2.exec(xml2))) {
    if (m2[1] === 'stg' || m2[1] === 'fct') (seen2[m2[2]] = seen2[m2[2]] || new Set()).add(m2[3]);
  }
  let p2 = 0;
  Object.keys(expected).forEach((t) => {
    const have = seen2[t] || new Set();
    const missing = [...expected[t]].filter((c) => !have.has(c));
    const stale = [...have].filter((c) => !expected[t].has(c));
    if (missing.length) { console.log('v2 ' + t + ': in the code, not in the diagram -> ' + missing.join(', ')); p2 += missing.length; }
    if (stale.length) { console.log('v2 ' + t + ': in the diagram, no longer in the code -> ' + stale.join(', ')); p2 += stale.length; }
  });
  console.log(p2 ? p2 + ' difference(s) in APFP_Data_Lineage_v2.drawio. Run python3 docs/lineage/lineage_pages.py' : 'APFP_Data_Lineage_v2.drawio matches the code (' + Object.keys(expected).length + ' tables checked).');
  problems += p2;
}
process.exit(problems ? 1 : 0);
