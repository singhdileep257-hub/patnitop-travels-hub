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
  const props = {};
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
          getValues() { const out = []; for (let i = r - 1; i < Math.min(rows.length, r - 1 + nr); i++) out.push(rows[i].slice(c - 1, c - 1 + nc)); return out; },
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
    PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] || null, setProperty: (k, v) => { props[k] = v; } }) },
    Utilities: { formatDate: (d) => new Date(d).toISOString().slice(0, 10) },
    Session: { getScriptTimeZone: () => 'Asia/Kolkata' },
    Logger: { log() {} },
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


// ---------------------------------------------------------------
// Click events, attribution and the dashboard stats endpoint
// ---------------------------------------------------------------
test('leads store traffic source, landing page and referrer', () => {
  const { post, sheets } = makeEnv();
  post(good({ source: 'route-form', traffic_source: 'google_organic', landing_page: '/ramban-taxi-service.html', referrer: 'www.google.com' }));
  const head = sheets['Leads'].rows[0], row = sheets['Leads'].rows[1];
  assert.strictEqual(row[head.indexOf('Traffic source')], 'google_organic');
  assert.strictEqual(row[head.indexOf('Landing page')], '/ramban-taxi-service.html');
  assert.strictEqual(row[head.indexOf('Referrer')], 'www.google.com');
});

test('button-tap events go to the Events tab, never into Leads', () => {
  const { post, sheets } = makeEnv();
  assert.strictEqual(post({ type: 'event', event: 'phone_click', page: '/jammu-airport-taxi.html', link_location: 'mobile_bar', traffic_source: 'direct' }).ok, true);
  assert.strictEqual(post({ type: 'event', event: 'whatsapp_click', page: '/', link_location: 'hero' }).ok, true);
  assert.strictEqual(sheets['Events'].rows.length, 3);
  assert(!sheets['Leads'] || sheets['Leads'].rows.length <= 1, 'a click is not a lead');
});

test('unknown event names are rejected and nothing is stored', () => {
  const { post, sheets } = makeEnv();
  assert.strictEqual(post({ type: 'event', event: 'confirmed_booking' }).error, 'bad event');
  assert(!sheets['Events'] || sheets['Events'].rows.length <= 1);
});

test('stats are refused without a key, with a wrong key, and when no key was ever created', () => {
  const env = makeEnv();
  assert.strictEqual(JSON.parse(env.sandbox.doGet({ parameter: { action: 'stats', key: 'x' } }).text).ok, false);
  const key = env.sandbox.createDashboardKey();
  assert(/^[a-z0-9]{24}$/.test(key));
  assert.strictEqual(JSON.parse(env.sandbox.doGet({ parameter: { action: 'stats' } }).text).error, 'bad key');
  assert.strictEqual(JSON.parse(env.sandbox.doGet({ parameter: { action: 'stats', key: 'wrong' } }).text).error, 'bad key');
  assert.strictEqual(JSON.parse(env.sandbox.doGet({ parameter: { action: 'stats', key } }).text).ok, true);
});

test('stats count enquiries, clicks and confirmed bookings separately', () => {
  const env = makeEnv(); const { post, sheets, sandbox } = env;
  const key = sandbox.createDashboardKey();
  post(good({ lead_id: 'LAAAAAA01', source: 'route-form', traffic_source: 'google_organic', landing_page: '/katra-to-jammu-taxi.html' }));
  post(good({ lead_id: 'LAAAAAA02', source: 'agent', traffic_source: 'direct', landing_page: '/' }));
  post(good({ lead_id: 'LAAAAAA03', source: 'contact-form', traffic_source: 'google_organic', landing_page: '/' }));
  for (let i = 0; i < 5; i++) post({ type: 'event', event: 'phone_click', page: '/', link_location: 'mobile_bar' });
  for (let i = 0; i < 2; i++) post({ type: 'event', event: 'whatsapp_click', page: '/', link_location: 'hero' });
  let st = JSON.parse(sandbox.doGet({ parameter: { action: 'stats', key } }).text);
  assert.strictEqual(st.totals.enquiries, 3);
  assert.strictEqual(st.totals.confirmed, 0, 'nothing is confirmed until the owner sets Status by hand');
  assert.strictEqual(st.totals.call_clicks, 5);
  assert.strictEqual(st.totals.whatsapp_clicks, 2);
  assert.strictEqual(st.totals.form_submissions, 2);
  assert.strictEqual(st.totals.assistant_submissions, 1);
  assert.strictEqual(st.by_source.google_organic, 2);
  // owner marks one Confirmed and one Cancelled in the sheet
  sheets['Leads'].rows[1][2] = 'Confirmed'; sheets['Leads'].rows[2][2] = 'Cancelled';
  st = JSON.parse(sandbox.doGet({ parameter: { action: 'stats', key } }).text);
  assert.strictEqual(st.totals.confirmed, 1);
  assert.strictEqual(st.totals.cancelled, 1);
  assert.strictEqual(st.totals.genuine, 2, 'genuine = not marked Cancelled');
  assert.strictEqual(st.totals.call_clicks, 5, 'clicks never become bookings');
});

test('stats never contain names, mobile numbers or message text', () => {
  const env = makeEnv(); const { post, sandbox } = env;
  const key = sandbox.createDashboardKey();
  post(good({ lead_id: 'LPRIVATE01', name: 'Secret Person', mobile: '9876543210', notes: 'private note text' }));
  const text = sandbox.doGet({ parameter: { action: 'stats', key } }).text;
  assert(!/Secret Person|9876543210|private note text/.test(text), 'no personal data in stats');
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
