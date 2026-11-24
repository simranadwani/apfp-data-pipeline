/**
 * Beneficiaries.gs — sorts the free-text Primary Beneficiary Group into a short list of dashboard
 * categories. The rules live in the Beneficiary_Buckets tab (edit there, no deploy); the defaults
 * below are written to that tab the first time and are used whenever the tab has no valid rule.
 * Rules are checked in rule_order, the first match wins, and the result depends only on the
 * text, the thematic area and the rules, so every run gives the same answer.
 */

const BENEFICIARY_BUCKETS = [
  'Children & youth', 'Educators & school leaders', 'Women & girls', 'Entrepreneurs & NGOs',
  'Families & households', 'Animals', 'Good Politician participants', 'Other',
];
const BENEFICIARY_NOT_SPECIFIED = 'Not specified';
const BENEFICIARY_RULE_HEADERS = ['rule_order', 'match_type', 'pattern', 'thematic_area', 'bucket', 'note'];
const BENEFICIARY_MATCH_TYPES = ['equals', 'contains', 'word_start'];
const BENEFICIARY_OTHER_SHARE_WARNING = 0.1;

// [rule_order, match_type, pattern, thematic_area, bucket, note]. Order matters: a more specific group must come
// before a general one ("Students and trainees" is Children & youth, so student comes before trainee).
const BENEFICIARY_DEFAULT_RULES = [
  [10, 'contains', '', 'Animal Welfare', 'Animals', 'Any Animal Welfare grant: the beneficiaries are animals even when the text reads like patients'],
  [11, 'word_start', 'dog', '', 'Animals', ''],
  [12, 'word_start', 'animal', '', 'Animals', ''],
  [20, 'contains', 'good politician', '', 'Good Politician participants', ''],
  [30, 'contains', 'women', '', 'Women & girls', 'Before children: "women ... with children under two" is Women & girls'],
  [31, 'word_start', 'girl', '', 'Women & girls', 'Girl-specific programmes, including adolescent girls'],
  [32, 'contains', 'she rep', '', 'Women & girls', 'Elected women representatives'],
  [40, 'contains', 'caregiver', '', 'Families & households', 'Before children: "children under five and their caregivers" is Families & households'],
  [41, 'contains', 'household', '', 'Families & households', ''],
  [42, 'word_start', 'famil', '', 'Families & households', ''],
  [50, 'word_start', 'entrepreneur', '', 'Entrepreneurs & NGOs', ''],
  [51, 'word_start', 'ngo', '', 'Entrepreneurs & NGOs', ''],
  [60, 'contains', 'student', '', 'Children & youth', 'Before trainee and fellow: "Students and trainees" is Children & youth'],
  [61, 'contains', 'child', '', 'Children & youth', 'Includes "children, young adults and adults with intellectual disabilities"'],
  [62, 'contains', 'learner', '', 'Children & youth', ''],
  [63, 'word_start', 'solver', '', 'Children & youth', ''],
  [64, 'contains', 'youth', '', 'Children & youth', ''],
  [65, 'contains', 'young adult', '', 'Children & youth', ''],
  [66, 'word_start', 'adolescent', '', 'Children & youth', ''],
  [70, 'word_start', 'teacher', '', 'Educators & school leaders', ''],
  [71, 'word_start', 'fellow', '', 'Educators & school leaders', 'Fellowships in this portfolio are for teachers and school leaders'],
  [72, 'contains', 'head master', '', 'Educators & school leaders', ''],
  [73, 'contains', 'headmaster', '', 'Educators & school leaders', ''],
  [74, 'word_start', 'crc', '', 'Educators & school leaders', 'Cluster Resource Coordinators'],
  [75, 'contains', 'cluster resource', '', 'Educators & school leaders', ''],
  [76, 'word_start', 'trainee', '', 'Educators & school leaders', ''],
  [77, 'word_start', 'educator', '', 'Educators & school leaders', ''],
  [78, 'word_start', 'mentor', '', 'Educators & school leaders', ''],
];

function normaliseBeneficiaryText(v) {
  return String(v === null || v === undefined ? '' : v).toLowerCase().replace(/\s+/g, ' ').trim();
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Turns one rule row into a ready-to-use rule, or { error } when it cannot be used. */
function parseBeneficiaryRule(row) {
  const order = typeof row.rule_order === 'number' ? row.rule_order : parseFloat(String(row.rule_order).trim());
  const type = normaliseBeneficiaryText(row.match_type);
  const pattern = normaliseBeneficiaryText(row.pattern);
  const thematic = normaliseBeneficiaryText(row.thematic_area);
  const bucket = String(row.bucket === null || row.bucket === undefined ? '' : row.bucket).trim();
  if (isNaN(order)) return { error: 'rule_order is not a number' };
  if (BENEFICIARY_MATCH_TYPES.indexOf(type) === -1) return { error: 'match_type must be one of ' + BENEFICIARY_MATCH_TYPES.join(', ') };
  if (BENEFICIARY_BUCKETS.indexOf(bucket) === -1) return { error: 'bucket "' + bucket + '" is not an allowed category' };
  if (pattern === '' && thematic === '') return { error: 'needs a pattern or a thematic_area' };
  const rule = { order: order, type: type, pattern: pattern, thematic: thematic, bucket: bucket, re: null };
  if (type === 'word_start' && pattern !== '') rule.re = new RegExp('(^|[^a-z0-9])' + escapeRegExp(pattern));
  return { rule: rule };
}

function defaultBeneficiaryRules() {
  return BENEFICIARY_DEFAULT_RULES.map(function (r) {
    const row = {}; BENEFICIARY_RULE_HEADERS.forEach(function (h, i) { row[h] = r[i]; });
    return parseBeneficiaryRule(row).rule;
  });
}

/**
 * Reads the rules from the Beneficiary_Buckets tab. A missing tab is created from the defaults; unusable rows are
 * skipped and logged; a tab with no usable rule falls back to the defaults. Never throws.
 */
function loadBeneficiaryRules(ss, idx) {
  const sheetName = idx.CFG_BENEFICIARY_BUCKETS || 'Beneficiary_Buckets';
  try {
    if (!ss.getSheetByName(sheetName)) {
      writeSheet(ss, sheetName, BENEFICIARY_RULE_HEADERS, BENEFICIARY_DEFAULT_RULES);
      log(ss, idx, 'INFO', 'loadBeneficiaryRules', BENEFICIARY_DEFAULT_RULES.length, sheetName + ' did not exist: created it from the default rules', null, 'SUCCESS');
      return defaultBeneficiaryRules();
    }
    const rows = readSheet(ss, sheetName);
    const rules = [];
    const problems = [];
    rows.forEach(function (row, i) {
      const parsed = parseBeneficiaryRule(row);
      if (parsed.error) problems.push('row ' + (i + 2) + ': ' + parsed.error);
      else { parsed.rule.position = i; rules.push(parsed.rule); }
    });
    if (problems.length) {
      log(ss, idx, 'WARN', 'loadBeneficiaryRules', 0, sheetName + ': ' + problems.length + ' rule(s) skipped. ' + problems.slice(0, 5).join('; '), null, 'SUCCESS');
    }
    if (!rules.length) {
      log(ss, idx, 'WARN', 'loadBeneficiaryRules', 0, sheetName + ' has no usable rule: using the built-in default rules', null, 'SUCCESS');
      return defaultBeneficiaryRules();
    }
    rules.sort(function (a, b) { return a.order - b.order || a.position - b.position; });
    return rules;
  } catch (e) {
    log(ss, idx, 'WARN', 'loadBeneficiaryRules', 0, 'Could not read ' + sheetName + ' (' + e + '): using the built-in default rules', null, 'SUCCESS');
    return defaultBeneficiaryRules();
  }
}

/** Returns { bucket, matched }. Blank text is "Not specified"; text that matches no rule is "Other" (matched = false). */
function bucketForBeneficiary(rawText, thematicArea, rules) {
  const text = normaliseBeneficiaryText(rawText);
  if (text === '') return { bucket: BENEFICIARY_NOT_SPECIFIED, matched: true };
  const thematic = normaliseBeneficiaryText(thematicArea);
  for (let i = 0; i < rules.length; i++) {
    const r = rules[i];
    if (r.thematic !== '' && r.thematic !== thematic) continue;
    let hit;
    if (r.pattern === '') hit = true;
    else if (r.type === 'equals') hit = text === r.pattern;
    else if (r.type === 'contains') hit = text.indexOf(r.pattern) !== -1;
    else hit = r.re.test(text);
    if (hit) return { bucket: r.bucket, matched: true };
  }
  return { bucket: 'Other', matched: false };
}
