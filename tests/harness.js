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
    for (let c = 0; c < this.numCols; c++) this.sheet.numberFormats[this.col + c] = fmt;
    return this;
  }
  setValues(values) {
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
    this.numberFormats = {}; // column number → format, kept across clearContents like Sheets
  }
  getName() { return this.name; }
  getLastRow() { return this.data.length; }
  getLastColumn() { return this.data.reduce((m, r) => Math.max(m, r.length), 0); }
  getDataRange() { return new FakeRange(this, 1, 1, Math.max(this.getLastRow(), 1), Math.max(this.getLastColumn(), 1)); }
  getRange(row, col, numRows, numCols) { return new FakeRange(this, row, col, numRows || 1, numCols || 1); }
  clearContents() { this.data = []; return this; }
  setFrozenRows(n) { this.frozenRows = n; }
  appendRow(values) { this.data.push(values.slice()); return this; }
  // Plain values, as a Looker/Sheets reader would see them.
  toObjects() {
    const [headers, ...rows] = this.data;
    return rows.map((r) => Object.fromEntries(headers.map((h, i) => [h, r[i] === undefined ? '' : r[i]])));
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
  const map = { yyyy: parts.year, MM: parts.month, dd: parts.day, HH: parts.hour, mm: parts.minute, ss: parts.second };
  return fmt.replace(/yyyy|MM|dd|HH|mm|ss/g, (t) => map[t]);
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
  return { ctx, source, pipeline, mails, logs };
}

module.exports = { loadPipeline, FakeSpreadsheet, FakeSheet, isDate };
