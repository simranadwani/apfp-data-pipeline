// Beneficiary categories: the 51 real group texts seen in fct1 on 2026-11-24, and the rules around them.
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadPipeline } = require('./harness');

const C = 'Children & youth', E = 'Educators & school leaders', W = 'Women & girls', N = 'Entrepreneurs & NGOs',
  F = 'Families & households', A = 'Animals', G = 'Good Politician participants';

// [raw text, thematic area, expected category]
const REAL_VALUES = [
  ['Children under five and their parents/primary caregivers', 'Health', F],
  ['Students in NMMC 91 and NMMC 92', 'Education', C],
  ['Trauma & Medical Treatment', 'Animal Welfare', A],
  ['Children in Grades 3 to 10 with large learning gaps, at risk of dropping out (Panaah Solvers: five community centres and six PMC schools)', 'Education', C],
  ['Children', 'Education', C],
  ['Entrepreneurs: Social entrepreneurs who are starting their schools and after-school programs. This includes entrepreneurs in Incubation and Network', 'Education', N],
  ['Entrepreneurs: school and after-school entrepreneurs in the Circle Incubation', 'Education', N],
  ['Fellows (teachers)', 'Education', E],
  ['Students (Maths & Science, Akanksha Foundation schools)', 'Education', C],
  ['She Rep - Elected Women Repr', 'Public Leadership', W],
  ['No. of students from marginalized communities receiving access to untapped scholarships', 'Education', C],
  ['CRCs (Cluster Resource Coordinators)', 'Education', E],
  ['Students', 'Education', C],
  ['Fellows trained (10 schools in Mumbai and Pune)', 'Education', E],
  ['Dogs', 'Animal Welfare', A],
  ['Students and trainees (all units)', 'Education', C],
  ['Fellows as Direct Beneficiaries (Overall)', 'Education', E],
  ['Fellows (first cohort)', 'Education', E],
  ['Teachers (government schools across Delhi)', 'Education', E],
  ['Adolescent Girls (below 18 yrs)', 'Education', W],
  ['Women reached (current outreach, Maternal Health and Early Care Program)', 'Health', W],
  ['Teacher mentors (~30 across 2 cities)', 'Education', E],
  ['Students across 5 REAP Centres and the RVS School', 'Education', C],
  ['Head Masters of government schools (Super 50 cohort, 24 wards)', 'Education', E],
  ['Teachers trained to take SEL for Grades 7-10', 'Education', E],
  ['Adolescent girls (Y1-Y3 total)', 'Education', W],
  ['Children reached by the Jijivisha Fellowship across 4 cities', 'Education', C],
  ['Students in vernacular medium schools, Grades 5 to 8 (2 centres in Beed district)', 'Education', C],
  ['Households (direct, Year 1, 50 Anganwadis)', 'Education', F],
  ['Class 12 students (33 science, 19 commerce)', 'Education', C],
  ['Students studying in government and low fee private schools', 'Education', C],
  ['Students sponsored with scholarships (95 new)', 'Education', C],
  ['Trainees to implement the personal safety education programme in schools (stated goal)', 'Education', E],
  ['Students with scholarships unlocked', 'Education', C],
  ['Children, young adults and adults with intellectual disabilities', 'Education', C],
  ['Solvers', 'Education', C],
  ['The Good Politician participants', 'Public Leadership', G],
  ['Students in the Realistic Mathematics Education (Calculus) pilot class', 'Education', C],
  ['Students and trainees', 'Education', C],
  ['Fellows trained across 10 schools', 'Education', E],
  ['Family units in Yerwada ward (about 60 families each in Lakshmi Nagar and Bhim Nagar)', 'Education', F],
  ['Students impacted (101 PCMC government schools)', 'Education', C],
  ['Solvers (includes 71 reintegration learners)', 'Education', C],
  ['Students in Grades 5-10 at NMMC 91 and NMMC 92', 'Education', C],
  ['NGOs supported to date', 'Capacity Building', N],
  ['Students at LAPMEMS', 'Education', C],
  ['First-generation learners', 'Education', C],
  ['Total students sponsored (scholarships)', 'Education', C],
  ['Grade X students', 'Education', C],
  ['Students in the Pune programme', 'Education', C],
  ['Slum-dwelling women aged 18 to 49 with children under two years (Sangamwadi, Dhole Patil and Bhawani Peth wards)', 'Health', W],
];

function load() { return loadPipeline(); }

test('all 51 real beneficiary group texts land in the agreed category', () => {
  const h = load();
  assert.equal(REAL_VALUES.length, 51);
  const rules = h.ctx.defaultBeneficiaryRules();
  REAL_VALUES.forEach(([raw, theme, want]) => {
    const got = h.ctx.bucketForBeneficiary(raw, theme, rules);
    assert.equal(got.bucket, want, raw);
    assert.equal(got.matched, true, raw);
  });
});

test('blank is Not specified; unmatched text is Other and reported as unmatched; matching ignores case and spacing', () => {
  const h = load();
  const rules = h.ctx.defaultBeneficiaryRules();
  ['', '   ', null, undefined].forEach((v) => assert.equal(h.ctx.bucketForBeneficiary(v, 'Education', rules).bucket, 'Not specified'));
  assert.deepEqual(JSON.parse(JSON.stringify(h.ctx.bucketForBeneficiary('Community institutions', 'Education', rules))), { bucket: 'Other', matched: false });
  assert.equal(h.ctx.bucketForBeneficiary('  STUDENTS   and   TRAINEES ', 'Education', rules).bucket, C);
  assert.equal(h.ctx.bucketForBeneficiary('Bangor residents', 'Education', rules).bucket, 'Other'); // "ngo" only matches at the start of a word
});

test('the thematic area decides animals, and a mixed cell lands in one category by rule order', () => {
  const h = load();
  const rules = h.ctx.defaultBeneficiaryRules();
  assert.equal(h.ctx.bucketForBeneficiary('Trauma & Medical Treatment', 'Animal Welfare', rules).bucket, A);
  assert.notEqual(h.ctx.bucketForBeneficiary('Trauma & Medical Treatment', 'Health', rules).bucket, A);
  assert.equal(h.ctx.bucketForBeneficiary('Women and children', 'Health', rules).bucket, W);
});

test('the category list is capped: 8 categories plus Not specified', () => {
  const h = load();
  assert.equal(h.ctx.__consts.BENEFICIARY_BUCKETS.length + 1, 9);
  assert.ok(h.ctx.__consts.BENEFICIARY_BUCKETS.includes('Other'));
  h.ctx.defaultBeneficiaryRules().forEach((r) => assert.ok(h.ctx.__consts.BENEFICIARY_BUCKETS.includes(r.bucket), r.bucket));
});

test('fct1 holds a category in primary_beneficiary_group and the original text in primary_beneficiary_group_raw (last column, text)', () => {
  const h = load();
  h.ctx.runCompletePipeline();
  const sheet = h.pipeline.getSheetByName('fct1_grant_portfolio');
  assert.ok(sheet.data[0].includes('primary_beneficiary_group_raw'));
  const rows = sheet.toObjects();
  const allowed = new Set([...h.ctx.__consts.BENEFICIARY_BUCKETS, 'Not specified']);
  rows.forEach((r) => {
    assert.ok(allowed.has(r.primary_beneficiary_group), r.primary_beneficiary_group);
    assert.equal(typeof r.primary_beneficiary_group, 'string');
    assert.ok(r.primary_beneficiary_group_raw === '' || typeof r.primary_beneficiary_group_raw === 'string');
  });
  const stg = h.pipeline.getSheetByName('stg_grants').toObjects();
  rows.forEach((r) => assert.equal(r.primary_beneficiary_group_raw, String(stg.find((g) => g.grant_id === r.grant_id).primary_beneficiary_group || '')));
  assert.ok(new Set(rows.map((r) => r.primary_beneficiary_group)).size <= 9);
  // dummy data: Youth, Women, Children are matched; "Community institutions" is not
  const by = Object.fromEntries(rows.map((r) => [r.primary_beneficiary_group_raw, r.primary_beneficiary_group]));
  assert.equal(by.Youth, C);
  assert.equal(by.Women, W);
  assert.equal(by['Community institutions'], 'Other');
});

test('unmatched values are logged on every run, naming the value', () => {
  const h = load();
  h.ctx.runCompletePipeline();
  h.ctx.runCompletePipeline();
  const warns = h.pipeline.getSheetByName('Pipeline Log').toObjects().filter((r) => r.level === 'WARN' && /matched no rule/.test(r.message));
  assert.equal(warns.length, 2);
  assert.match(warns[0].message, /community institutions/);
});

test('the rules tab is created on first run, and re-running does not overwrite edits', () => {
  const h = load();
  h.ctx.runCompletePipeline();
  const sheet = h.pipeline.getSheetByName('Beneficiary_Buckets');
  assert.ok(sheet, 'tab is created');
  assert.deepEqual(sheet.data[0], ['rule_order', 'match_type', 'pattern', 'thematic_area', 'bucket', 'note']);
  assert.equal(sheet.data.length - 1, h.ctx.__consts.BENEFICIARY_DEFAULT_RULES.length);
  // a manager adds a rule for the unmatched value
  sheet.data.push([5, 'contains', 'community institutions', '', 'Families & households', 'added by hand']);
  h.ctx.runCompletePipeline();
  const rows = h.pipeline.getSheetByName('fct1_grant_portfolio').toObjects();
  assert.equal(rows.find((r) => r.primary_beneficiary_group_raw === 'Community institutions').primary_beneficiary_group, F);
  assert.equal(h.pipeline.getSheetByName('Beneficiary_Buckets').data.length - 1, h.ctx.__consts.BENEFICIARY_DEFAULT_RULES.length + 1);
});

test('rule_order decides between two rules that both match', () => {
  const h = load();
  h.ctx.runCompletePipeline();
  const sheet = h.pipeline.getSheetByName('Beneficiary_Buckets');
  sheet.data.push([1, 'contains', 'youth', '', 'Educators & school leaders', 'wins: lowest rule_order']);
  h.ctx.runCompletePipeline();
  const rows = h.pipeline.getSheetByName('fct1_grant_portfolio').toObjects();
  assert.equal(rows.find((r) => r.primary_beneficiary_group_raw === 'Youth').primary_beneficiary_group, E);
});

test('bad rules are skipped with a warning, and a tab with no usable rule falls back to the defaults', () => {
  const h = load();
  h.ctx.runCompletePipeline();
  const sheet = h.pipeline.getSheetByName('Beneficiary_Buckets');
  sheet.data.push([2, 'contains', 'youth', '', 'Made Up Category', ''], ['x', 'contains', 'youth', '', 'Animals', ''], [3, 'regex', 'youth', '', 'Animals', ''], [4, 'contains', '', '', 'Animals', '']);
  h.ctx.runCompletePipeline();
  let rows = h.pipeline.getSheetByName('fct1_grant_portfolio').toObjects();
  assert.equal(rows.find((r) => r.primary_beneficiary_group_raw === 'Youth').primary_beneficiary_group, C);
  let warn = h.pipeline.getSheetByName('Pipeline Log').toObjects().filter((r) => r.level === 'WARN' && /rule\(s\) skipped/.test(r.message));
  assert.equal(warn.length, 1);
  assert.match(warn[0].message, /4 rule\(s\) skipped/);
  sheet.data = [sheet.data[0], [2, 'contains', 'youth', '', 'Made Up Category', '']];
  h.ctx.runCompletePipeline();
  rows = h.pipeline.getSheetByName('fct1_grant_portfolio').toObjects();
  assert.equal(rows.find((r) => r.primary_beneficiary_group_raw === 'Youth').primary_beneficiary_group, C);
  warn = h.pipeline.getSheetByName('Pipeline Log').toObjects().filter((r) => r.level === 'WARN' && /no usable rule/.test(r.message));
  assert.equal(warn.length, 1);
});

test('primary_beneficiary_group_order is a plain number: one per category, Not specified last, A to Z before it', () => {
  const h = load();
  const order = h.ctx.__consts.BENEFICIARY_GROUP_ORDER;
  const cats = [...h.ctx.__consts.BENEFICIARY_BUCKETS, 'Not specified'];
  assert.deepEqual(Object.keys(order).sort(), [...cats].sort());
  assert.equal(new Set(Object.values(order)).size, cats.length);
  assert.equal(order['Not specified'], Math.max(...Object.values(order)));
  assert.equal(order.Other, order['Not specified'] - 1);
  const named = Object.keys(order).filter((c) => c !== 'Other' && c !== 'Not specified');
  assert.deepEqual([...named].sort((a, b) => order[a] - order[b]), [...named].sort());
  h.ctx.runCompletePipeline();
  const sheet = h.pipeline.getSheetByName('fct1_grant_portfolio');
  assert.equal(sheet.data[0][sheet.data[0].length - 1], 'primary_beneficiary_group_order');
  sheet.toObjects().forEach((r) => {
    assert.equal(typeof r.primary_beneficiary_group_order, 'number');
    assert.equal(r.primary_beneficiary_group_order, order[r.primary_beneficiary_group]);
  });
});

test('the pipeline stays in step: no other fct1 column changes (the raw text is appended, the category replaces the group)', () => {
  const h = load();
  h.ctx.runCompletePipeline();
  const hdr = h.pipeline.getSheetByName('fct1_grant_portfolio').data[0];
  assert.equal(hdr.indexOf('primary_beneficiary_group'), 15);
  assert.equal(hdr.indexOf('primary_beneficiary_count'), 16);
});
