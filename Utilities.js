/**
 * Utilities.gs — only reusable functions called by multiple build functions (SoP 2.1).
 * One-off helpers live in the file where they are used.
 */

const PIPELINE_LOG_HEADERS = ['timestamp', 'level', 'function', 'rows_written', 'message', 'duration_ms', 'status'];

function getPipelineSpreadsheet() {
  return SpreadsheetApp.openById(PIPELINE_SPREADSHEET_ID);
}

function getSourceSpreadsheet() {
  return SpreadsheetApp.openById(SOURCE_SPREADSHEET_ID);
}

/** Composite map key. Never join key parts with '_' — IDs contain underscores (SoP 2.3). */
function key() {
  return Array.prototype.slice.call(arguments).join('||');
}

function isBlank(v) {
  return v === null || v === undefined || (typeof v === 'string' && v.trim() === '');
}

/**
 * Reads a tab into { headers, rows }. The header row is the first non-empty row
 * (source tabs 2–7 leave row 1 empty; the registries start on row 1).
 * Fully blank rows are dropped. Each row is an object keyed by header text.
 */
function readSheetWithHeaders(ss, sheetName) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) throw new Error('Sheet not found: "' + sheetName + '"');
  const values = sheet.getDataRange().getValues();
  let h = 0;
  while (h < values.length && values[h].every(isBlank)) h++;
  if (h >= values.length) return { headers: [], rows: [] };

  const headers = values[h].map(function (v) { return String(v).trim(); });
  const rows = [];
  for (let i = h + 1; i < values.length; i++) {
    if (values[i].every(isBlank)) continue;
    const obj = {};
    headers.forEach(function (name, c) {
      if (name) obj[name] = values[i][c];
    });
    rows.push(obj);
  }
  return { headers: headers, rows: rows };
}

function readSheet(ss, sheetName) {
  return readSheetWithHeaders(ss, sheetName).rows;
}

/** Like readSheet, but returns [] when the tab does not exist yet. */
function readSheetSafe(ss, sheetName) {
  return ss.getSheetByName(sheetName) ? readSheet(ss, sheetName) : [];
}

/**
 * Clears the tab and writes headers + rows. Idempotent: never appends (SoP 5.3).
 * rows may be arrays (in header order) or objects keyed by header.
 */
function writeSheet(ss, sheetName, headers, rows) {
  const sheet = ss.getSheetByName(sheetName) || ss.insertSheet(sheetName);
  sheet.clearContents();
  const matrix = [headers].concat(rows.map(function (r) {
    if (Array.isArray(r)) return r;
    return headers.map(function (hd) {
      const v = r[hd];
      return v === null || v === undefined ? '' : v;
    });
  }));
  sheet.getRange(1, 1, matrix.length, headers.length).setValues(matrix);
  sheet.setFrozenRows(1);
  return rows.length;
}

function formatTimestamp(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
}

function formatIsoDate(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

/** Appends one entry to the Pipeline Log tab (SoP 5.1). */
function log(ss, idx, level, fnName, rowsWritten, message, durationMs, status) {
  const sheetName = (idx && idx.UTIL_PIPELINE_LOG) || 'Pipeline Log';
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    sheet.getRange(1, 1, 1, PIPELINE_LOG_HEADERS.length).setValues([PIPELINE_LOG_HEADERS]);
    sheet.setFrozenRows(1);
  }
  const entry = [formatTimestamp(new Date()), level, fnName, rowsWritten || 0, message || '',
    durationMs === null || durationMs === undefined ? '' : durationMs, status || ''];
  sheet.appendRow(entry);
  Logger.log(entry.join(' | '));
}

/** Runs one build function, logging SUCCESS or ERROR with its duration. fn returns rows written. */
function runLogged(ss, idx, fnName, fn) {
  const start = Date.now();
  try {
    const rows = fn();
    log(ss, idx, 'INFO', fnName, rows, 'Built successfully', Date.now() - start, 'SUCCESS');
    return rows;
  } catch (e) {
    log(ss, idx, 'ERROR', fnName, 0, e.toString(), Date.now() - start, 'ERROR');
    throw e;
  }
}

/** Source FY "2026-27" → next FY "2027-28". Returns '' for anything else. */
function nextFinancialYear(fy) {
  const m = /^(\d{4})-(\d{2})$/.exec(String(fy || '').trim());
  if (!m) return '';
  const start = Number(m[1]) + 1;
  return start + '-' + String((start + 1) % 100).padStart(2, '0');
}
