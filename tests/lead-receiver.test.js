// Runs the REAL apps-script/lead-receiver.gs against an in-memory fake of the
// Google Sheets / Script services, to prove what it stores and what it refuses.
//   node tests/lead-receiver.test.js
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function makeEnv({ notify = '' } = {}) {
  const sheets = {};
  const mails = [];
  function Sheet(name) {
    const rows = [];
    return {
      name, rows, frozen: 0, validations: [],
      getLastRow: () => rows.length,
      getMaxRows: () => Math.max(rows.length, 1000),
      appendRow: r => { rows.push(r.slice()); },
      setFrozenRows: n => { sheets[name].frozen = n; },
      getRange(r, c, nr, nc) {
        return {
          setFontWeight() {}, setDataValidation(rule) { sheets[name].validations.push({ r, c, rule }); },
          createTextFinder(text) {
            return { matchEntireCell() { return this; }, findNext() { for (let i = r - 1; i < rows.length; i++) if (String(rows[i][c - 1]) === text) return {}; return null; } };
          }
        };
      }
    };
  }
  const ss = {
    getSheetByName: n => sheets[n] || null,
    insertSheet: n => (sheets[n] = Sheet(n))
  };
  const sandbox = {
    SpreadsheetApp: {
      getActiveSpreadsheet: () => ss,
      newDataValidation: () => ({ requireValueInList(list) { this.list = list; return this; }, setAllowInvalid(v) { this.allow = v; return this; }, build() { return { list: this.list, allowInvalid: this.allow }; } })
    },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: t => ({ text: t, setMimeType() { return this; } }) },
    MailApp: { sendEmail: (...a) => mails.push(a) },
    console
  };
  vm.createContext(sandbox);
  let code = fs.readFileSync(path.join(__dirname, '..', 'apps-script', 'lead-receiver.gs'), 'utf8');
  if (notify) code = code.replace("var NOTIFY_EMAIL = '';", "var NOTIFY_EMAIL = '" + notify + "';");
  vm.runInContext(code, sandbox);
  const post = obj => JSON.parse(sandbox.doPost({ postData: { contents: typeof obj === 'string' ? obj : JSON.stringify(obj) } }).text);
  return { sandbox, sheets, mails, post };
}

const good = (o = {}) => Object.assign({ lead_id: 'LABC123XYZ', type: 'taxi', source: 'agent', service: 'Katra to Patnitop', name: 'Asha', mobile: '98765 43210', pickup: 'Katra', drop: 'Patnitop', consent_followup: 'Yes' }, o);
let passed = 0, failed = 0;
function test(name, fn) { try { fn(); passed++; console.log('  ok   ' + name); } catch (e) { failed++; console.log('  FAIL ' + name + '\n       ' + e.message); } }

console.log('Lead receiver (apps-script/lead-receiver.gs)');

test('doGet reports the service is live', () => {
  const { sandbox } = makeEnv();
  assert.strictEqual(JSON.parse(sandbox.doGet().text).ok, true);
});

test('setup() creates both tabs with headers, frozen row and the 5-value Status dropdown', () => {
  const { sandbox, sheets } = makeEnv(); sandbox.setup();
  assert(sheets['Leads'] && sheets['Product Enquiries']);
  assert.strictEqual(sheets['Leads'].rows[0][2], 'Status');
  assert.strictEqual(sheets['Leads'].frozen, 1);
  assert.strictEqual(JSON.stringify(sheets['Leads'].validations[0].rule.list), JSON.stringify(['New', 'Quotation Sent', 'Follow-up Required', 'Confirmed', 'Cancelled']));
  assert.strictEqual(sheets['Leads'].validations[0].rule.allowInvalid, false);
});

test('a valid taxi lead is stored in Leads with status New and a cleaned mobile', () => {
  const { post, sheets } = makeEnv();
  assert.strictEqual(post(good()).ok, true);
  const row = sheets['Leads'].rows[1];
  assert.strictEqual(row[2], 'New');
  assert.strictEqual(row[7], "'9876543210");
  assert.strictEqual(row[19], 'Yes');
});

test('the website cannot set the status: a "Confirmed" status in the payload is ignored', () => {
  const { post, sheets } = makeEnv();
  post(good({ status: 'Confirmed', _status: 'Confirmed' }));
  assert.strictEqual(sheets['Leads'].rows[1][2], 'New');
});

test('product leads go to their own tab, never into Leads', () => {
  const { post, sheets } = makeEnv();
  assert.strictEqual(post(good({ lead_id: 'LPRODUCT01', type: 'product', products: 'Honey, Rajma', quantity: '2 kg' })).ok, true);
  assert.strictEqual(sheets['Product Enquiries'].rows.length, 2);
  assert(!sheets['Leads'] || sheets['Leads'].rows.length <= 1);
  assert.strictEqual(sheets['Product Enquiries'].rows[1][6], 'Honey, Rajma');
});

test('the same lead sent twice is stored once', () => {
  const { post, sheets } = makeEnv();
  post(good()); const second = post(good());
  assert.strictEqual(second.duplicate, true);
  assert.strictEqual(sheets['Leads'].rows.length, 2);
});

test('rejects bad mobile, missing name, bad type, bad id, malformed JSON', () => {
  const { post, sheets } = makeEnv();
  assert.strictEqual(post(good({ mobile: '123' })).error, 'bad mobile');
  assert.strictEqual(post(good({ name: '  ' })).error, 'name required');
  assert.strictEqual(post(good({ type: 'admin' })).error, 'bad type');
  assert.strictEqual(post(good({ lead_id: 'x' })).error, 'bad lead id');
  assert.strictEqual(post('not json').ok, false);
  assert(!sheets['Leads'] || sheets['Leads'].rows.length <= 1, 'nothing stored for rejected leads');
});

test('honeypot submissions are dropped without storing anything', () => {
  const { post, sheets } = makeEnv();
  assert.strictEqual(post(good({ website: 'http://spam' })).ignored, 'honeypot');
  assert(!sheets['Leads']);
});

test('spreadsheet formulas are neutralised and long text is capped', () => {
  const { post, sheets } = makeEnv();
  post(good({ name: '=HYPERLINK("http://evil","x")', notes: '+1+1', pickup: 'A'.repeat(5000) }));
  const row = sheets['Leads'].rows[1];
  assert(row[6].startsWith("'="), 'name formula escaped');
  assert(row[17].startsWith("'+"), 'notes formula escaped');
  assert(row[8].length <= 502, 'pickup capped, got ' + row[8].length);
});

test('email notification is optional, and a mail failure never loses the lead', () => {
  let env = makeEnv(); env.post(good()); assert.strictEqual(env.mails.length, 0, 'no email by default');
  env = makeEnv({ notify: 'owner@example.com' }); env.post(good());
  assert.strictEqual(env.mails.length, 1); assert.strictEqual(env.mails[0][0], 'owner@example.com');
  env = makeEnv({ notify: 'owner@example.com' });
  env.sandbox.MailApp.sendEmail = () => { throw new Error('quota'); };
  assert.strictEqual(env.post(good()).ok, true); assert.strictEqual(env.sheets['Leads'].rows.length, 2);
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
