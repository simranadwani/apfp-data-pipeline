/**
 * Final.gs — one buildFct*() per dashboard fact table (SoP 3, Step 6).
 * Reads only stg_ tabs. Every derived field is documented in PIPELINE_LOGIC.md.
 * Dashboard metrics (distinct counts, sums, ratios) are Looker Studio calculated
 * fields, not stored columns, so they never double count.
 */

const CORE_POLICY_COLUMNS = ['has_code_of_conduct_policy', 'has_posh_policy', 'has_child_protection_policy', 'has_data_protection_policy'];
const COMMITTED_DISBURSEMENT_STATUSES = ['committed', 'disbursed'];
const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4'];
// Sort helpers for the dashboard (the text bands do not sort in the right order by themselves).
const DUE_WINDOW_ORDER = { 'Overdue': 1, '0\u201330 days': 2, '31\u201360 days': 3, '61+ days': 4 };
const FUNDING_RANGE_ORDER = { '<\u20B91 lakh': 1, '\u20B91\u201310 lakh': 2, '\u20B911\u201320 lakh': 3, '\u20B921\u201350 lakh': 4, '>\u20B950 lakh': 5 };
const RAG_SEVERITY = { green: 1, amber: 2, red: 3 };
// Sort helpers for the dashboard (legend / axis order): Clarity, Capacity, Compliance and Red, Amber, Green.
const ASPECT_ORDER = { clarity: 1, capacity: 2, compliance: 3 };
const STATUS_ORDER = { red: 1, amber: 2, green: 3 };

const FCT1_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'mission', 'thematic_area',
  'education_sub_category', 'proximity_to_children_beneficiary', 'grant_status', 'grant_type',
  'grant_performance_status', 'grant_start_date', 'grant_end_date', 'funding_year',
  'duration_of_support_bucket', 'primary_beneficiary_group', 'primary_beneficiary_count',
  'clarity_status', 'capacity_status', 'compliance_status', 'fcra_registration',
  'has_completed_program_lifecycle', 'annual_budget', 'team_size', 'attrition_rate',
  'foreign_contribution_rate', 'core_policies_met_count', 'core_policies_total_count',
  'approved_amount', 'committed_amount', 'disbursed_amount', 'funding_range',
  'decision_type', 'decision_status', 'due_window', 'recommendation', 'decision_due_date',
  'reason_for_recommendation', 'grantee_360_link', 'proposed_amount', 'total_outcomes_count',
  'achieved_outcomes_count', 'annual_report_link', 'grant_period', 'grant_status_type_amount',
  'cost_per_beneficiary', 'is_active_grant', 'is_funded_grantee', 'is_pending_decision',
  'is_overdue_decision', 'is_due_within_30_days', 'is_on_track_active_grant',
  'is_off_track_active_grant', 'as_of_date', 'sub_category_line', 'due_window_order', 'funding_range_order',
];

const FCT2_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'thematic_area', 'grant_status',
  'outcome_id', 'outcome_indicator', 'quarter', 'status', 'target_text', 'target_value',
  'achieved_value', 'outcome_achievement_pct', 'final_actual_value', 'annual_achievement_pct',
  'outcome_notes', 'latest_notes', 'evidence_link', 'is_latest_update',
];

const FCT3_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'thematic_area', 'grant_status', 'support_id',
  'quarter', 'support_category', 'request_description', 'support_status', 'is_open_support_need',
  'response_notes', 'response_date', 'evidence_link', 'response_category',
];

const FCT4_HEADERS = [
  'financial_year', 'dividend_income', 'prior_year_carry_forward', 'available_budget',
  'annual_committed_funding', 'next_year_q1_committed_funding', 'annual_disbursed_funding',
  'unallocated_balance',
];

const FCT5_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'thematic_area', 'grant_status', 'aspect',
  'indicator', 'status', 'aspect_display', 'aspect_order', 'status_order',
];

const FCT6_HEADERS = [
  'financial_year', 'previous_financial_year', 'grant_id', 'organization_id', 'organisation', 'grant_status',
  'metric_order', 'metric', 'current_value', 'previous_value',
];

// ---------------------------------------------------------------------------
// fct1_grant_portfolio — one row per grant_id
// ---------------------------------------------------------------------------
function buildFct1GrantPortfolio(ss, idx) {
  const today = pipelineToday();
  const grants = readSheet(ss, idx.STG_GRANTS);
  const orgById = indexBy(readSheet(ss, idx.STG_ORGANISATIONS), 'organization_id');
  const decisionByGrant = indexBy(readSheet(ss, idx.STG_DECISIONS), 'grant_id');
  const disbByGrant = groupBy(readSheet(ss, idx.STG_DISBURSEMENTS), 'grant_id');
  const maturityByGrant = groupBy(readSheet(ss, idx.STG_MATURITY), 'grant_id');
  const outcomesByGrant = groupBy(readSheet(ss, idx.STG_OUTCOME_PROGRESS), 'grant_id');
  warnOrphanGrantIds(ss, idx, 'buildFct1GrantPortfolio', grants, {
    stg_decisions: decisionByGrant, stg_disbursements: disbByGrant,
    stg_maturity: maturityByGrant, stg_outcome_progress: outcomesByGrant,
  });

  // Distinct funded financial years per organisation, for funding_year.
  const fysByOrg = {};
  grants.forEach(function (g) {
    if (isBlank(g.organization_id) || isBlank(g.financial_year)) return;
    (fysByOrg[g.organization_id] = fysByOrg[g.organization_id] || {})[g.financial_year] = true;
  });

  const rows = grants.map(function (g) {
    const org = orgById[g.organization_id] || {};
    const dec = decisionByGrant[g.grant_id] || {};
    const funding = sumDisbursements(disbByGrant[g.grant_id] || []);
    const outcomes = outcomesByGrant[g.grant_id] || [];
    const maturity = maturityByGrant[g.grant_id] || [];
    const performance = grantPerformanceStatus(outcomes);
    const decisionStatus = mapDecisionStatus(dec.decision_status);
    const isPending = decisionStatus === 'Pending';
    const daysToDue = dec.decision_due_date instanceof Date ? daysBetween(today, dec.decision_due_date) : null;
    const fundingYearNumber = fysByOrg[g.organization_id]
      ? Object.keys(fysByOrg[g.organization_id]).filter(function (fy) { return fy <= g.financial_year; }).length
      : null;
    const isActive = String(g.grant_status).trim().toLowerCase() === 'active';

    return {
      financial_year: g.financial_year,
      grant_id: g.grant_id,
      organization_id: g.organization_id,
      organisation: g.organisation,
      mission: org.mission_statement,
      thematic_area: g.thematic_area,
      education_sub_category: g.thematic_sub_area,
      proximity_to_children_beneficiary: g.proximity_to_children_beneficiary,
      grant_status: g.grant_status,
      grant_type: g.grant_type,
      grant_performance_status: performance,
      grant_start_date: g.grant_start_date,
      grant_end_date: g.grant_end_date,
      funding_year: fundingYearNumber ? 'Year ' + fundingYearNumber : '',
      duration_of_support_bucket: durationBucket(fundingYearNumber),
      primary_beneficiary_group: g.primary_beneficiary_group,
      primary_beneficiary_count: g.primary_beneficiary_count,
      clarity_status: worstRag(maturity, 'Clarity'),
      capacity_status: worstRag(maturity, 'Capacity'),
      compliance_status: worstRag(maturity, 'Compliance'),
      fcra_registration: org.fcra_registration_status,
      has_completed_program_lifecycle: String(g.grant_status).trim().toLowerCase() === 'complete',
      annual_budget: g.annual_budget,
      team_size: g.team_size,
      attrition_rate: g.attrition_rate,
      foreign_contribution_rate: g.foreign_contribution_rate,
      core_policies_met_count: orgById[g.organization_id] ? countCorePolicies(org) : '',
      core_policies_total_count: CORE_POLICY_COLUMNS.length,
      approved_amount: g.approved_amount,
      committed_amount: funding.committed,
      disbursed_amount: funding.disbursed,
      funding_range: '', // filled below: needs the organisation × FY total
      decision_type: isBlank(dec.decision_type) ? '' : (String(dec.decision_type).trim().toLowerCase() === 'close' ? 'Closure' : 'Renewal'),
      decision_status: decisionStatus,
      due_window: isPending && daysToDue !== null ? dueWindow(daysToDue) : '',
      recommendation: dec.decision_type,
      decision_due_date: dec.decision_due_date,
      reason_for_recommendation: dec.decision_rationale,
      grantee_360_link: '',
      proposed_amount: dec.proposed_amount,
      total_outcomes_count: countDistinct(outcomes, 'outcome_id'),
      achieved_outcomes_count: countAchievedOutcomes(outcomes),
      annual_report_link: !isBlank(dec.annual_report_link) ? dec.annual_report_link : org.latest_annual_report_link,
      // Display text for the dashboard (one source of truth): "01 Apr 2026 – 31 Mar 2027" and "Active · Restricted · ₹7,50,000".
      grant_period: (g.grant_start_date instanceof Date && g.grant_end_date instanceof Date)
        ? formatDisplayDate(g.grant_start_date) + ' \u2013 ' + formatDisplayDate(g.grant_end_date) : '',
      grant_status_type_amount: [g.grant_status, g.grant_type, formatInr(g.approved_amount)].filter(function (v) { return !isBlank(v); }).join(' \u00B7 '),
      cost_per_beneficiary: (typeof g.approved_amount === 'number' && typeof g.primary_beneficiary_count === 'number' && g.primary_beneficiary_count > 0)
        ? Math.round((g.approved_amount / g.primary_beneficiary_count) * 100) / 100 : '',
      is_active_grant: isActive,
      is_funded_grantee: funding.disbursed > 0,
      is_pending_decision: isPending,
      is_overdue_decision: isPending && daysToDue !== null && daysToDue < 0,
      is_due_within_30_days: isPending && daysToDue !== null && daysToDue >= 0 && daysToDue <= 30,
      is_on_track_active_grant: isActive && performance === 'On Track',
      is_off_track_active_grant: isActive && performance === 'Off Track',
      as_of_date: today,
      sub_category_line: [g.thematic_sub_area, g.proximity_to_children_beneficiary].filter(function (v) { return !isBlank(v); }).join(' \u00B7 '),
      due_window_order: '',
      funding_range_order: '',
    };
  });

  // funding_range: band on total disbursed per organisation × financial year.
  const disbursedByOrgFy = {};
  rows.forEach(function (r) {
    const k = key(r.organization_id, r.financial_year);
    disbursedByOrgFy[k] = (disbursedByOrgFy[k] || 0) + r.disbursed_amount;
  });
  rows.forEach(function (r) {
    r.funding_range = fundingRange(disbursedByOrgFy[key(r.organization_id, r.financial_year)]);
    r.funding_range_order = FUNDING_RANGE_ORDER[r.funding_range] || '';
    r.due_window_order = DUE_WINDOW_ORDER[r.due_window] || '';
  });

  return writeSheet(ss, idx.FCT1_GRANT_PORTFOLIO, FCT1_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct2_outcome_progress — one row per grant_id × outcome_id × reported quarter
// ---------------------------------------------------------------------------
function buildFct2OutcomeProgress(ss, idx) {
  const grantById = indexBy(readSheet(ss, idx.STG_GRANTS), 'grant_id');
  const outcomes = readSheet(ss, idx.STG_OUTCOME_PROGRESS);
  warnOrphanGrantIds(ss, idx, 'buildFct2OutcomeProgress', null, { stg_outcome_progress: groupBy(outcomes, 'grant_id') }, grantById);

  const rows = [];
  outcomes.forEach(function (o) {
    const g = grantById[o.grant_id] || {};
    const target = parseMeasure(o.target_text);
    const latest = latestReportedQuarter(o);
    const finalActual = parseMeasure(o.final_actual_text);
    const latestNotes = latest ? o[latest.toLowerCase() + '_notes'] : '';
    QUARTERS.forEach(function (q) {
      const p = q.toLowerCase();
      const status = o[p + '_status'];
      const progress = o[p + '_progress'];
      if (isBlank(status) && isBlank(progress) && isBlank(o[p + '_notes'])) return; // quarter not reported yet
      const achieved = parseMeasure(progress);
      rows.push({
        financial_year: o.financial_year,
        grant_id: o.grant_id,
        organization_id: g.organization_id,
        organisation: g.organisation || o.organisation,
        thematic_area: g.thematic_area,
        grant_status: g.grant_status,
        outcome_id: o.outcome_id,
        outcome_indicator: o.outcome_indicator,
        quarter: q,
        status: status,
        target_text: o.target_text,
        target_value: target === null ? '' : target,
        achieved_value: achieved === null ? '' : achieved,
        outcome_achievement_pct: (target && achieved !== null) ? achieved / target : '',
        final_actual_value: finalActual === null ? '' : finalActual,
        annual_achievement_pct: (target && finalActual !== null) ? finalActual / target : '',
        outcome_notes: o[p + '_notes'],
        latest_notes: latestNotes,
        evidence_link: o[p + '_evidence_link'],
        is_latest_update: q === latest,
      });
    });
  });
  return writeSheet(ss, idx.FCT2_OUTCOME_PROGRESS, FCT2_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct3_support_activity — one row per support request
// ---------------------------------------------------------------------------
function buildFct3SupportActivity(ss, idx) {
  const grantById = indexBy(readSheet(ss, idx.STG_GRANTS), 'grant_id');
  const support = readSheet(ss, idx.STG_SUPPORT);
  warnOrphanGrantIds(ss, idx, 'buildFct3SupportActivity', null, { stg_support: groupBy(support, 'grant_id') }, grantById);

  const seq = {};
  const rows = support.map(function (s) {
    const g = grantById[s.grant_id] || {};
    const k = key(s.grant_id, s.quarter);
    seq[k] = (seq[k] || 0) + 1;
    const status = String(s.status).trim().toLowerCase() === 'in progress' ? 'Open' : s.status;
    return {
      financial_year: s.financial_year,
      grant_id: s.grant_id,
      organization_id: g.organization_id,
      organisation: g.organisation || s.organisation,
      thematic_area: g.thematic_area,
      grant_status: g.grant_status,
      support_id: 'SUP-' + s.grant_id + '-' + (s.quarter || 'NQ') + '-' + seq[k],
      quarter: s.quarter,
      support_category: s.support_type,
      request_description: s.support_required,
      support_status: status,
      is_open_support_need: String(status).trim().toLowerCase() === 'open',
      response_notes: s.notes,
      response_date: '', // the source has no response date yet
      evidence_link: s.evidence_link,
      response_category: s.support_provided, // "Support Provided" dropdown in the source, value kept as entered
    };
  });
  return writeSheet(ss, idx.FCT3_SUPPORT_ACTIVITY, FCT3_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct4_budget_year — one row per financial_year
// ---------------------------------------------------------------------------
function buildFct4BudgetYear(ss, idx) {
  const dividends = readSheet(ss, idx.STG_DIVIDENDS);
  const disbursements = readSheet(ss, idx.STG_DISBURSEMENTS);

  const fySet = {};
  dividends.forEach(function (d) { if (!isBlank(d.financial_year)) fySet[d.financial_year] = true; });
  disbursements.forEach(function (d) { if (!isBlank(d.financial_year)) fySet[d.financial_year] = true; });
  const fys = Object.keys(fySet).sort();

  let carryForward = 0;
  const rows = fys.map(function (fy) {
    const dividend = sumWhere(dividends, 'dividend_income', function (d) { return d.financial_year === fy; });
    const committed = sumWhere(disbursements, 'planned_amount', function (d) {
      return d.financial_year === fy && isCommittedStatus(d.status);
    });
    const nextFy = nextFinancialYear(fy);
    const nextQ1 = sumWhere(disbursements, 'planned_amount', function (d) {
      return d.financial_year === nextFy && /^Q1\b/i.test(String(d.quarter).trim()) && isCommittedStatus(d.status);
    });
    const disbursed = sumWhere(disbursements, 'actual_amount', function (d) {
      return d.financial_year === fy && String(d.status).trim().toLowerCase() === 'disbursed';
    });
    const available = dividend + carryForward;
    const row = {
      financial_year: fy,
      dividend_income: dividend,
      prior_year_carry_forward: carryForward,
      available_budget: available,
      annual_committed_funding: committed,
      next_year_q1_committed_funding: nextQ1,
      annual_disbursed_funding: disbursed,
      unallocated_balance: available - committed - nextQ1,
    };
    // Next Q1 is only reserved here, not spent: it is counted in next year's own commitments.
    carryForward = available - committed;
    return row;
  });
  return writeSheet(ss, idx.FCT4_BUDGET_YEAR, FCT4_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct5_maturity_rag — one row per grant_id × aspect × indicator
// ---------------------------------------------------------------------------
function buildFct5MaturityRag(ss, idx) {
  const grantById = indexBy(readSheet(ss, idx.STG_GRANTS), 'grant_id');
  const maturity = readSheet(ss, idx.STG_MATURITY);
  warnOrphanGrantIds(ss, idx, 'buildFct5MaturityRag', null, { stg_maturity: groupBy(maturity, 'grant_id') }, grantById);

  const rows = maturity.map(function (m) {
    const g = grantById[m.grant_id] || {};
    return {
      financial_year: m.financial_year,
      grant_id: m.grant_id,
      organization_id: g.organization_id,
      organisation: g.organisation || m.organisation,
      thematic_area: g.thematic_area,
      grant_status: g.grant_status,
      aspect: m.aspect,
      indicator: m.indicator,
      status: m.status,
      aspect_display: '',
      aspect_order: ASPECT_ORDER[String(m.aspect).trim().toLowerCase()] || '',
      status_order: STATUS_ORDER[String(m.status).trim().toLowerCase()] || '',
    };
  });
  // aspect_display: the aspect on the first row of each aspect block, blank on the rest (a Looker
  // table cannot merge cells). Rows are ordered by grant, aspect, indicator, so a block is contiguous.
  rows.sort(function (a, b) {
    return String(a.grant_id).localeCompare(String(b.grant_id)) || String(a.aspect).localeCompare(String(b.aspect)) || String(a.indicator).localeCompare(String(b.indicator));
  });
  rows.forEach(function (r, i) {
    const prev = rows[i - 1];
    r.aspect_display = (prev && prev.grant_id === r.grant_id && prev.aspect === r.aspect) ? '' : r.aspect;
  });
  return writeSheet(ss, idx.FCT5_MATURITY_RAG, FCT5_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct6_grantee_annual_info — one row per grant_id x metric (Grantee 360, chart 4.02)
// Looker Studio cannot transpose a table, so the metrics-down-the-side layout of the mockup is
// built here: each row holds the metric's value for the grant's financial year and for the
// previous financial year of the same organisation, both as display text. Filter the table by the
// Financial Year control (financial_year): it then shows exactly that year and the one before it.
// ---------------------------------------------------------------------------
const FCT6_METRICS = [
  ['Financial year', function (g) { return g.financial_year || ''; }],
  ['Annual budget', function (g) { return formatInr(g.annual_budget); }],
  ['% Annual Budget funded by APFP', function (g) {
    return (typeof g.approved_amount === 'number' && typeof g.annual_budget === 'number' && g.annual_budget > 0)
      ? Math.round(g.approved_amount / g.annual_budget * 100) + '%' : '';
  }],
  ['Team size', function (g) { return typeof g.team_size === 'number' ? String(g.team_size) : ''; }],
  ['Attrition', function (g) { return typeof g.attrition_rate === 'number' ? Math.round(g.attrition_rate * 100) + '%' : ''; }],
  ['Core policies', function (g) {
    return (typeof g.core_policies_met_count === 'number' && typeof g.core_policies_total_count === 'number')
      ? g.core_policies_met_count + ' / ' + g.core_policies_total_count : '';
  }],
  ['FCRA registration', function (g) { return isBlank(g.fcra_registration) ? '' : String(g.fcra_registration); }],
  ['Foreign contribution share', function (g) { return typeof g.foreign_contribution_rate === 'number' ? Math.round(g.foreign_contribution_rate * 100) + '%' : ''; }],
];

function buildFct6GranteeAnnualInfo(ss, idx) {
  const portfolio = readSheet(ss, idx.FCT1_GRANT_PORTFOLIO);
  const byOrgYear = {};
  portfolio.forEach(function (g) { byOrgYear[key(g.organization_id, g.financial_year)] = g; });

  const rows = [];
  portfolio.forEach(function (g) {
    const prevFy = previousFinancialYear(g.financial_year);
    const prev = byOrgYear[key(g.organization_id, prevFy)];
    FCT6_METRICS.forEach(function (metric, i) {
      const current = metric[1](g);
      // The Financial year row always names the previous year, so the column header is right even
      // when the organisation had no grant that year; every other row is blank (a dash) then.
      const previous = i === 0 ? prevFy : (prev ? metric[1](prev) : '');
      rows.push({
        financial_year: g.financial_year,
        previous_financial_year: prevFy,
        grant_id: g.grant_id,
        organization_id: g.organization_id,
        organisation: g.organisation,
        grant_status: g.grant_status,
        metric_order: i + 1,
        metric: metric[0],
        current_value: current === '' ? '\u2013' : current,
        previous_value: previous === '' ? '\u2013' : previous,
      });
    });
  });
  return writeSheet(ss, idx.FCT6_GRANTEE_ANNUAL_INFO, FCT6_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// Helpers used only by the final layer
// ---------------------------------------------------------------------------

/** Today at midnight in the script time zone — the reference date for due windows. */
function pipelineToday() {
  const parts = formatIsoDate(new Date()).split('-').map(Number);
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function daysBetween(from, to) {
  const a = Date.UTC(from.getFullYear(), from.getMonth(), from.getDate());
  const b = Date.UTC(to.getFullYear(), to.getMonth(), to.getDate());
  return Math.round((b - a) / 86400000);
}

function indexBy(rows, field) {
  const map = {};
  rows.forEach(function (r) { if (!isBlank(r[field])) map[r[field]] = r; });
  return map;
}

function groupBy(rows, field) {
  const map = {};
  rows.forEach(function (r) {
    if (isBlank(r[field])) return;
    (map[r[field]] = map[r[field]] || []).push(r);
  });
  return map;
}

function countDistinct(rows, field) {
  const seen = {};
  rows.forEach(function (r) { if (!isBlank(r[field])) seen[r[field]] = true; });
  return Object.keys(seen).length;
}

function sumWhere(rows, field, predicate) {
  return rows.reduce(function (acc, r) {
    return predicate(r) && typeof r[field] === 'number' ? acc + r[field] : acc;
  }, 0);
}

function isCommittedStatus(status) {
  return COMMITTED_DISBURSEMENT_STATUSES.indexOf(String(status).trim().toLowerCase()) !== -1;
}

function sumDisbursements(rows) {
  return {
    committed: sumWhere(rows, 'planned_amount', function (d) { return isCommittedStatus(d.status); }),
    disbursed: sumWhere(rows, 'actual_amount', function (d) { return String(d.status).trim().toLowerCase() === 'disbursed'; }),
  };
}

/** "70% of annual target" → 0.7, "35% achieved" → 0.35, "732 learners" → 732. null if no number. */
function parseMeasure(text) {
  if (typeof text === 'number') return text;
  const m = /(-?\d+(?:\.\d+)?)\s*(%)?/.exec(String(text || '').replace(/,/g, ''));
  if (!m) return null;
  const n = Number(m[1]);
  return m[2] ? n / 100 : n;
}

/** Latest quarter (Q4 → Q1) with a status for this outcome row, or ''. */
function latestReportedQuarter(outcomeRow) {
  for (let i = QUARTERS.length - 1; i >= 0; i--) {
    if (!isBlank(outcomeRow[QUARTERS[i].toLowerCase() + '_status'])) return QUARTERS[i];
  }
  return '';
}

/**
 * Grant is Off Track if any of its outcomes is Off Track in the latest quarter
 * that has any status for the grant; otherwise On Track. '' when nothing is reported.
 */
function grantPerformanceStatus(outcomes) {
  for (let i = QUARTERS.length - 1; i >= 0; i--) {
    const col = QUARTERS[i].toLowerCase() + '_status';
    const statuses = outcomes.map(function (o) { return String(o[col] || '').trim().toLowerCase(); })
      .filter(function (s) { return s !== ''; });
    if (!statuses.length) continue;
    return statuses.indexOf('off track') !== -1 ? 'Off Track' : 'On Track';
  }
  return '';
}

/** Outcome is achieved when Final Actual ≥ End-of-Program Cycle Target (both parsed as numbers). */
function countAchievedOutcomes(outcomes) {
  return outcomes.filter(function (o) {
    const target = parseMeasure(o.target_text);
    const actual = parseMeasure(o.final_actual_text);
    return target !== null && actual !== null && actual >= target;
  }).length;
}

/** Worst RAG (Red > Amber > Green) across the grant's indicators for one aspect. */
function worstRag(maturityRows, aspect) {
  let worst = '';
  maturityRows.forEach(function (m) {
    if (String(m.aspect).trim().toLowerCase() !== aspect.toLowerCase()) return;
    const sev = RAG_SEVERITY[String(m.status).trim().toLowerCase()];
    if (sev && (!worst || sev > RAG_SEVERITY[worst.toLowerCase()])) worst = String(m.status).trim();
  });
  return worst;
}

function countCorePolicies(org) {
  return CORE_POLICY_COLUMNS.filter(function (c) { return String(org[c]).trim().toLowerCase() === 'yes'; }).length;
}

function durationBucket(n) {
  if (!n) return '';
  if (n === 1) return 'Year 1';
  if (n <= 5) return 'Years 2–5';
  if (n <= 10) return 'Years 6–10';
  return 'Years 11+';
}

function mapDecisionStatus(status) {
  if (isBlank(status)) return '';
  const s = String(status).toLowerCase();
  if (s.indexOf('locked') !== -1) return 'Decided';
  if (s.indexOf('recommendation') !== -1) return 'Pending';
  return String(status).trim();
}

function dueWindow(days) {
  if (days < 0) return 'Overdue';
  if (days <= 30) return '0–30 days';
  if (days <= 60) return '31–60 days';
  return '61+ days';
}

function fundingRange(amount) {
  if (!amount || amount <= 0) return '';
  const LAKH = 100000;
  if (amount < 1 * LAKH) return '<₹1 lakh';
  if (amount <= 10 * LAKH) return '₹1–10 lakh';
  if (amount <= 20 * LAKH) return '₹11–20 lakh';
  if (amount <= 50 * LAKH) return '₹21–50 lakh';
  return '>₹50 lakh';
}

/** Logs a WARN listing grant_ids found in stg tables but not in stg_grants. */
function warnOrphanGrantIds(ss, idx, fnName, grants, groupedByTable, grantById) {
  const known = grantById || indexBy(grants, 'grant_id');
  Object.keys(groupedByTable).forEach(function (table) {
    const orphans = Object.keys(groupedByTable[table]).filter(function (id) { return !known[id]; });
    if (orphans.length) {
      log(ss, idx, 'WARN', fnName, 0, orphans.length + ' grant_id(s) in ' + table + ' not found in stg_grants: ' + orphans.slice(0, 10).join(', '), null, 'SUCCESS');
    }
  });
}
