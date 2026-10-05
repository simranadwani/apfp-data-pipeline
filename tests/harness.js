// Runs the Apps Script files in Node against in-memory spreadsheets.
// Only the SpreadsheetApp / Utilities / Session / MailApp / Logger calls the
// pipeline uses are mocked. Run with TZ=Asia/Kolkata (see package.json).
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
// Dates must be created with the script context's own Date, or `instanceof Date` fails there.
let RealmDate = Date;
const isDate = (v) => Object.prototype.toString.call(v) === '[object Date]';

const SCRIPT_FILES = ['Utilities.js', 'Index.js', 'Staging.js', 'Final.js', 'SourceHeaderCheck.js', 'Tests.js', 'Pipeline.js'];

class FakeRange {
  constructor(sheet, row, col, numRows, numCols) {
    Object.assign(this, { sheet, row, col, numRows, numCols });
  }
  getValues() {
    const out = [];
    for (let r = 0; r < this.numRows; r++) {
      const src = this.sheet.data[this.row - 1 + r] || [];
      const line = [];
      for (let c = 0; c < this.numCols; c++) {
        const v = src[this.col - 1 + c];
        line.push(v === undefined || v === null ? '' : v);
      }
      out.push(line);
    }
    return out;
  }
  setNumberFormat(fmt) {
    // A native Sheets Table owns its number formats: typed columns reject changes.
    if (this.sheet.table) {
      this.sheet.formatCalls++;
      throw new Error("You can't set the number format of cells in a typed column.");
    }
    for (let c = 0; c < this.numCols; c++) this.sheet.numberFormats[this.col + c] = fmt;
    this.sheet.formatCalls++;
    return this;
  }
  clearContent() {
    if (this.row === 1 && this.col === 1) this.sheet.headerClears++; // wiping the Table's own header (a leftover column to the right is harmless)
    for (let r = 0; r < this.numRows; r++) {
      const line = this.sheet.data[this.row - 1 + r];
      if (line) for (let c = 0; c < this.numCols; c++) delete line[this.col - 1 + c];
    }
    return this;
  }
  setValues(values) {
    if (this.sheet.failAllWrites) throw new Error('Service error: Spreadsheets');
    if (values.length !== this.numRows || values.some((r) => r.length !== this.numCols)) {
      throw new Error('setValues: dimensions do not match the range');
    }
    values.forEach((line, r) => {
      const target = (this.sheet.data[this.row - 1 + r] = this.sheet.data[this.row - 1 + r] || []);
      line.forEach((v, c) => {
        if (v === undefined || v === null) throw new Error('setValues: undefined/null cell at ' + (this.row + r) + ',' + (this.col + c));
        target[this.col - 1 + c] = isDate(v) ? new RealmDate(v.getTime()) : v;
      });
    });
    return this;
  }
}

class FakeSheet {
  constructor(name, data) {
    this.name = name;
    this.data = data || [];
    this.frozenRows = 0;
    this.numberFormats = {}; // column number → format
    this.table = false;      // true = native Sheets Table (typed columns)
    this.appendFails = false;   // appendRow throws
    this.failAllWrites = false; // appendRow and setValues throw
    this.formatCalls = 0;    // every setNumberFormat attempt
    this.headerClears = 0;   // times the header row was cleared
    this.clearAllCalls = 0;  // clearContents() calls
    this.deletedRows = 0;
  }
  getName() { return this.name; }
  // Like Sheets: the last row / column that actually holds content.
  getLastRow() {
    for (let r = this.data.length - 1; r >= 0; r--) if ((this.data[r] || []).some((v) => v !== undefined && v !== '')) return r + 1;
    return 0;
  }
  getLastColumn() {
    let m = 0;
    this.data.forEach((row) => (row || []).forEach((v, c) => { if (v !== undefined && v !== '') m = Math.max(m, c + 1); }));
    return m;
  }
  getDataRange() { return new FakeRange(this, 1, 1, Math.max(this.getLastRow(), 1), Math.max(this.getLastColumn(), 1)); }
  getRange(row, col, numRows, numCols) { return new FakeRange(this, row, col, numRows || 1, numCols || 1); }
  clearContents() {
    this.clearAllCalls++;
    if (this.getLastRow() >= 1) this.headerClears++;
    this.data = [];
    return this;
  }
  deleteRows(start, count) {
    if (start <= this.frozenRows) throw new Error("You can't delete a frozen row.");
    this.data.splice(start - 1, count);
    this.deletedRows += count;
  }
  setFrozenRows(n) { this.frozenRows = n; }
  appendRow(values) {
    if (this.appendFails || this.failAllWrites) throw new Error('Service error: Spreadsheets');
    this.data[this.getLastRow()] = values.slice();
    return this;
  }
  // Plain values, as a Looker/Sheets reader would see them (trailing blank rows and columns ignored).
  toObjects() {
    const lastRow = this.getLastRow();
    const width = this.getLastColumn();
    const cell = (r, c) => { const v = (this.data[r] || [])[c]; return v === undefined ? '' : v; };
    const headers = Array.from({ length: width }, (_, c) => cell(0, c));
    return Array.from({ length: Math.max(lastRow - 1, 0) }, (_, i) => Object.fromEntries(headers.map((h, c) => [h, cell(i + 1, c)])));
  }
}

class FakeSpreadsheet {
  constructor(id, tabs, timeZone) {
    this.id = id;
    this.timeZone = timeZone || 'Asia/Kolkata';
    this.sheets = {};
    Object.entries(tabs || {}).forEach(([name, data]) => { this.sheets[name] = new FakeSheet(name, data); });
  }
  getSheetByName(name) { return this.sheets[name] || null; }
  insertSheet(name) {
    if (this.sheets[name]) throw new Error('Sheet already exists: ' + name);
    return (this.sheets[name] = new FakeSheet(name));
  }
  getSheets() { return Object.values(this.sheets); }
  getSpreadsheetTimeZone() { return this.timeZone; }
  setSpreadsheetTimeZone(tz) { this.timeZone = tz; }
}

function reviveDates(tabs) {
  const out = {};
  Object.entries(tabs).forEach(([name, rows]) => {
    out[name] = rows.map((r) => r.map((v) => (v && typeof v === 'object' && v.__date__ ? new RealmDate(v.__date__) : v)));
  });
  return out;
}

function pad(n) { return String(n).padStart(2, '0'); }

// Like Utilities.formatDate: renders the instant as wall time in the given time zone.
function formatDate(date, tz, fmt) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  }).formatToParts(date).map((p) => [p.type, p.value]));
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const map = { yyyy: parts.year, MMM: MONTHS[Number(parts.month) - 1], MM: parts.month, dd: parts.day, HH: parts.hour, mm: parts.minute, ss: parts.second };
  return fmt.replace(/yyyy|MMM|MM|dd|HH|mm|ss/g, (t) => map[t]);
}

/**
 * Loads the Apps Script files into a fresh context.
 * sourceTabs: { tabName: rows[][] } for the source workbook (defaults to the fixture).
 * options.pipelineTimeZone / options.sourceTimeZone: spreadsheet time zones (default Asia/Kolkata).
 * Returns { ctx, source, pipeline, mails, logs }.
 */
function loadPipeline(sourceTabs, options) {
  options = options || {};
  const fixture = sourceTabs || JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'source_dummy.json'), 'utf8'));
  const mails = [];
  const logs = [];
  const books = {};
  const ctx = {
    SpreadsheetApp: {
      openById(id) {
        if (!books[id]) throw new Error('Unknown spreadsheet id ' + id);
        return books[id];
      },
    },
    Utilities: { formatDate },
    Session: {
      getScriptTimeZone: () => 'Asia/Kolkata',
      getEffectiveUser: () => ({ getEmail: () => 'owner@example.org' }),
    },
    MailApp: { sendEmail: (to, subject, body) => mails.push({ to, subject, body }) },
    Logger: { log: (m) => logs.push(m) },
    console,
  };
  vm.createContext(ctx);
  RealmDate = vm.runInContext('Date', ctx);
  const code = SCRIPT_FILES.map((f) => fs.readFileSync(path.join(ROOT, f), 'utf8')).join('\n;\n');
  // Expose top-level consts on the context so tests can read them.
  vm.runInContext(code + '\n;globalThis.__consts = { SOURCE_SPREADSHEET_ID, PIPELINE_SPREADSHEET_ID };', ctx, { filename: 'apps-script-bundle.js' });
  const source = new FakeSpreadsheet(ctx.__consts.SOURCE_SPREADSHEET_ID, reviveDates(fixture), options.sourceTimeZone);
  const pipeline = new FakeSpreadsheet(ctx.__consts.PIPELINE_SPREADSHEET_ID, { Sheet1: [] }, options.pipelineTimeZone);
  books[source.id] = source;
  books[pipeline.id] = pipeline;
  // Simulates converting every tab to a native Table (what the product owner did on 30 Sep).
  const convertToTables = () => Object.values(pipeline.sheets).forEach((sh) => { sh.table = true; });
  return { ctx, source, pipeline, mails, logs, convertToTables };
}

module.exports = { loadPipeline, FakeSpreadsheet, FakeSheet, isDate };
