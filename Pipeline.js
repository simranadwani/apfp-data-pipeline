/**
 * Pipeline.gs — single entry point and layer runners (SoP 2.1, 2.2, 5.2).
 * Flow: source header check → staging (stg_) → final (fct_) → cardinality tests.
 * There is no int_ layer: every fct_ table is built directly from stg_ tables
 * (see PIPELINE_LOGIC.md for why). No triggers are installed; run it by hand.
 */

const SOURCE_SPREADSHEET_ID = '18waNT2rH8HtErPqL3ERGNPNlSTXD-DfJc4quzzEhfkw'; // APFP Central Administration (source)
const PIPELINE_SPREADSHEET_ID = '1bjMmSxdN9RYJ6-Odgobqs4MedVy2QOMDYKLdKX08L00'; // Data Pipeline (output)

function runCompletePipeline() {
  const ss = getPipelineSpreadsheet();
  const idx = getSheetIndex(ss);
  const start = Date.now();
  try {
    alignTimeZones(ss, idx);
    const headerCheck = runSourceHeaderCheck(ss, idx);
    if (headerCheck.critical) {
      throw new Error(headerCheck.critical + ' critical source header issue(s). See the Source_Header_Audit tab.');
    }
    runStagingLayer(ss, idx);
    runFinalLayer(ss, idx);
    const failedTests = runCardinalityTests(ss, idx);
    log(ss, idx, failedTests ? 'WARN' : 'INFO', 'runCompletePipeline', 0,
      failedTests ? 'Completed with ' + failedTests + ' failed cardinality test(s)' : 'Completed',
      Date.now() - start, 'SUCCESS');
  } catch (e) {
    log(ss, idx, 'ERROR', 'runCompletePipeline', 0, e.toString(), Date.now() - start, 'ERROR');
    MailApp.sendEmail(Session.getEffectiveUser().getEmail(), 'APFP Pipeline Error', e.toString());
    throw e;
  }
}

/**
 * Dates shift on every write/read when a spreadsheet's time zone differs from the
 * script's (appsscript.json). The pipeline workbook is set to the script's zone;
 * the source workbook is only reported, never changed (staging reads it in its own zone).
 */
function alignTimeZones(ss, idx) {
  const scriptTz = Session.getScriptTimeZone();
  const pipelineTz = ss.getSpreadsheetTimeZone();
  if (pipelineTz !== scriptTz) {
    ss.setSpreadsheetTimeZone(scriptTz);
    log(ss, idx, 'WARN', 'alignTimeZones', 0,
      'Pipeline workbook time zone changed from ' + pipelineTz + ' to ' + scriptTz + ' to match the script', null, 'SUCCESS');
  }
  const sourceTz = getSourceSpreadsheet().getSpreadsheetTimeZone();
  if (sourceTz !== scriptTz) {
    log(ss, idx, 'WARN', 'alignTimeZones', 0,
      'Source workbook time zone is ' + sourceTz + ' (script: ' + scriptTz + '). Dates are read in the source zone, so values stay correct.', null, 'SUCCESS');
  }
}

function runStagingLayer(ss, idx) {
  runLogged(ss, idx, 'buildStgGrants', function () { return buildStgGrants(ss, idx); });
  runLogged(ss, idx, 'buildStgOrganisations', function () { return buildStgOrganisations(ss, idx); });
  runLogged(ss, idx, 'buildStgOutcomeProgress', function () { return buildStgOutcomeProgress(ss, idx); });
  runLogged(ss, idx, 'buildStgSupport', function () { return buildStgSupport(ss, idx); });
  runLogged(ss, idx, 'buildStgDecisions', function () { return buildStgDecisions(ss, idx); });
  runLogged(ss, idx, 'buildStgDividends', function () { return buildStgDividends(ss, idx); });
  runLogged(ss, idx, 'buildStgDisbursements', function () { return buildStgDisbursements(ss, idx); });
  runLogged(ss, idx, 'buildStgMaturity', function () { return buildStgMaturity(ss, idx); });
}

function runFinalLayer(ss, idx) {
  runLogged(ss, idx, 'buildFct1GrantPortfolio', function () { return buildFct1GrantPortfolio(ss, idx); });
  runLogged(ss, idx, 'buildFct2OutcomeProgress', function () { return buildFct2OutcomeProgress(ss, idx); });
  runLogged(ss, idx, 'buildFct3SupportActivity', function () { return buildFct3SupportActivity(ss, idx); });
  runLogged(ss, idx, 'buildFct4BudgetYear', function () { return buildFct4BudgetYear(ss, idx); });
  runLogged(ss, idx, 'buildFct5MaturityRag', function () { return buildFct5MaturityRag(ss, idx); });
}

// Zero-argument wrappers so each layer can be run from the Apps Script editor
// (and later from a menu, once an onOpen trigger is added).
function runStagingLayerMenu() {
  const ss = getPipelineSpreadsheet();
  alignTimeZones(ss, getSheetIndex(ss));
  runStagingLayer(ss, getSheetIndex(ss));
}

function runFinalLayerMenu() {
  const ss = getPipelineSpreadsheet();
  alignTimeZones(ss, getSheetIndex(ss));
  runFinalLayer(ss, getSheetIndex(ss));
}

function runSourceHeaderCheckMenu() {
  const ss = getPipelineSpreadsheet();
  return runSourceHeaderCheck(ss, getSheetIndex(ss));
}
