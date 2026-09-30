/**
 * Utilities.gs — only reusable functions called by multiple build functions (SoP 2.1).
 * One-off helpers live in the file where they are used.
 *
 * Output tabs are native Google Sheets Tables. A Table owns its column types and number /
 * date formats, and rejects attempts to change them. So this pipeline only ever writes
 * VALUES (Date, number, boolean, text, '' for blank). It never sets a number format, and it
 * never clears a Table's header row. Formatting belongs to the sheet (see docs/TABLE_FORMATS.md).
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
 * Runs a purely cosmetic or tidy-up step. A failure is noted in the Apps Script log and
 * never stops the pipeline.
 */
function bestEffort(label, fn) {
  try {
    return fn();
  } catch (e) {
    Logger.log('Skipped (' + label + '): ' + e);
    return undefined;
  }
}

/**
 * Writes headers + rows to a tab, in place. Idempotent: the tab always ends up holding
 * exactly this data (SoP 5.3). rows may be arrays (in header order) or objects keyed by header.
 *
 * Table-safe: the header and body go out in a single setValues (so the Table keeps its
 * columns and types), nothing is formatted, and only what is left over from a bigger
 * previous run is removed: surplus rows are deleted (the Table shrinks), or blanked if the
 * sheet refuses; surplus columns are blanked. Returns the number of data rows written.
 */
function writeSheet(ss, sheetName, headers, rows) {
  const sheet = ss.getSheetByName(sheetName) || ss.insertSheet(sheetName);
  const previousLastRow = sheet.getLastRow();
  const previousLastCol = sheet.getLastColumn();

  const matrix = [headers].concat(rows.map(function (r) {
    if (Array.isArray(r)) return r.map(blankIfMissing);
    return headers.map(function (hd) { return blankIfMissing(r[hd]); });
  }));
  sheet.getRange(1, 1, matrix.length, headers.length).setValues(matrix);

  // A Table needs a header and at least one body row: keep row 2 even when there is no data.
  const keepRows = Math.max(matrix.length, 2);
  if (previousLastRow > keepRows) removeSurplusRows(sheet, keepRows, previousLastRow, Math.max(previousLastCol, headers.length));
  if (matrix.length < 2 && previousLastRow >= 2) {
    bestEffort('blank row 2 of ' + sheetName, function () { sheet.getRange(2, 1, 1, Math.max(previousLastCol, headers.length)).clearContent(); });
  }
  if (previousLastCol > headers.length) {
    bestEffort('blank surplus columns of ' + sheetName, function () {
      sheet.getRange(1, headers.length + 1, Math.max(previousLastRow, keepRows), previousLastCol - headers.length).clearContent();
    });
  }
  bestEffort('freeze header of ' + sheetName, function () { sheet.setFrozenRows(1); });
  return rows.length;
}

function blankIfMissing(v) {
  return v === null || v === undefined ? '' : v;
}

/** Deletes rows keepRows+1 … lastRow so a Table shrinks with its data; blanks them if deletion is refused. */
function removeSurplusRows(sheet, keepRows, lastRow, width) {
  const first = keepRows + 1;
  const count = lastRow - keepRows;
  const deleted = bestEffort('delete surplus rows', function () { sheet.deleteRows(first, count); return true; });
  if (!deleted) bestEffort('blank surplus rows', function () { sheet.getRange(first, 1, count, width).clearContent(); });
}

function formatTimestamp(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
}

function formatIsoDate(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

/**
 * Appends one entry to the Pipeline Log tab (SoP 5.1). Logging must never break a run, so this
 * never throws: appendRow, else setValues on the next free row, else the Apps Script log only.
 */
function log(ss, idx, level, fnName, rowsWritten, message, durationMs, status) {
  const entry = [formatTimestamp(new Date()), level, fnName, rowsWritten || 0, message || '',
    durationMs === null || durationMs === undefined ? '' : durationMs, status || ''];
  Logger.log(entry.join(' | '));
  bestEffort('write Pipeline Log', function () {
    const sheetName = (idx && idx.UTIL_PIPELINE_LOG) || 'Pipeline Log';
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      sheet.getRange(1, 1, 1, PIPELINE_LOG_HEADERS.length).setValues([PIPELINE_LOG_HEADERS]);
      bestEffort('freeze header of ' + sheetName, function () { sheet.setFrozenRows(1); });
    }
    try {
      sheet.appendRow(entry);
    } catch (e) {
      sheet.getRange(sheet.getLastRow() + 1, 1, 1, entry.length).setValues([entry]);
    }
  });
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
