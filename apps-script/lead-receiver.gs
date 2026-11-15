/**
 * Patnitop Travels Hub — lead receiver (Google Apps Script web app).
 *
 * Receives enquiries from the website form and chat assistant and appends them
 * to a private Google Sheet that YOU own. Free: no server, no paid service.
 * Setup steps are in docs/SETUP.md.
 *
 * Two tabs are created automatically:
 *   "Leads"              taxi / hotel / sightseeing / package / vehicle enquiries
 *   "Product Enquiries"  local-product enquiries (kept separate on purpose)
 *
 * The Status column is a dropdown you change by hand as you work a lead:
 *   New -> Quotation Sent -> Follow-up Required -> Confirmed / Cancelled
 * The website can only ever create leads with status "New". It cannot mark
 * anything Confirmed, and it never sends a message to a customer.
 */

var STATUSES = ['New', 'Quotation Sent', 'Follow-up Required', 'Confirmed', 'Cancelled'];

// Optional: set to your email address to get one email per new lead.
// Leave '' for no emails. (Uses your free Apps Script email quota.)
var NOTIFY_EMAIL = '';

var TAXI_SHEET = 'Leads';
var PRODUCT_SHEET = 'Product Enquiries';
var EVENT_SHEET = 'Events';   // Call / WhatsApp / email button taps. No personal data.

// Column header -> key in the JSON the website sends.
var TAXI_COLUMNS = [
  ['Received', '_received'], ['Lead ID', 'lead_id'], ['Status', '_status'], ['Type', 'type'], ['Source', 'source'],
  ['Service', 'service'], ['Name', 'name'], ['Mobile', 'mobile'], ['Pickup', 'pickup'], ['Drop', 'drop'],
  ['Travel date', 'travel_date'], ['Return date', 'return_date'], ['Passengers', 'passengers'], ['Vehicle', 'vehicle'],
  ['Trip type', 'trip_type'], ['Hotel required', 'hotel_required'], ['Sightseeing required', 'sightseeing_required'],
  ['Notes', 'notes'], ['Quote shown', 'quote_shown'], ['Follow-up consent', 'consent_followup'], ['Page', 'page'],
  ['Traffic source', 'traffic_source'], ['Landing page', 'landing_page'], ['Referrer', 'referrer'],
  ['Internal notes', '_blank']
];
var EVENT_COLUMNS = [
  ['Time', '_received'], ['Event', 'event'], ['Page', 'page'], ['Button location', 'link_location'],
  ['Traffic source', 'traffic_source'], ['Landing page', 'landing_page'], ['Referrer', 'referrer']
];
var ALLOWED_EVENTS = ['phone_click', 'whatsapp_click', 'email_click'];
var PRODUCT_COLUMNS = [
  ['Received', '_received'], ['Lead ID', 'lead_id'], ['Status', '_status'], ['Source', 'source'], ['Name', 'name'],
  ['Mobile', 'mobile'], ['Products', 'products'], ['Quantity', 'quantity'], ['Delivery place', 'delivery_place'],
  ['Notes', 'notes'], ['Follow-up consent', 'consent_followup'], ['Page', 'page'], ['Internal notes', '_blank']
];

var ALLOWED_TYPES = ['taxi', 'hotel', 'sightseeing', 'package', 'vehicle', 'other', 'product'];
var MAX_FIELD = 500;

/** Run once from the editor (Run > setup) to create the tabs, headers and Status dropdown. */
function setup() {
  getSheet_(TAXI_SHEET, TAXI_COLUMNS);
  getSheet_(PRODUCT_SHEET, PRODUCT_COLUMNS);
  getSheet_(EVENT_SHEET, EVENT_COLUMNS, true);
}

/**
 * Run once (Run > createDashboardKey), then read the key in View > Logs.
 * Type that key into dashboard.html to unlock the numbers. Running it again makes a NEW key
 * and the old one stops working. The key is stored in Script Properties, never in the website.
 */
function createDashboardKey() {
  var chars = 'abcdefghijkmnpqrstuvwxyz23456789', key = '';
  for (var i = 0; i < 24; i++) key += chars.charAt(Math.floor(Math.random() * chars.length));
  PropertiesService.getScriptProperties().setProperty('DASHBOARD_KEY', key);
  Logger.log('Dashboard key: ' + key);
  return key;
}

/**
 * Opening the web-app URL in a browser shows the status line, so you can check the deployment is live.
 * ?action=stats&key=... returns COUNTS ONLY (no names, no phone numbers) for dashboard.html.
 */
function doGet(e) {
  var params = (e && e.parameter) || {};
  if (params.action === 'stats') {
    var expected = '';
    try { expected = PropertiesService.getScriptProperties().getProperty('DASHBOARD_KEY') || ''; } catch (err) { expected = ''; }
    if (!expected) return json_({ ok: false, error: 'no dashboard key set (run createDashboardKey)' });
    if (String(params.key || '') !== expected) return json_({ ok: false, error: 'bad key' });
    return json_(buildStats_());
  }
  return json_({ ok: true, service: 'Patnitop Travels Hub lead receiver' });
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var data = JSON.parse(e.postData.contents);
    return json_(handleLead_(data));
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  } finally {
    try { lock.releaseLock(); } catch (ignore) {}
  }
}

function handleLead_(d) {
  if (d.website) return { ok: true, ignored: 'honeypot' }; // a bot filled the hidden field

  var type = String(d.type || '');
  if (type === 'event') return handleEvent_(d);
  if (ALLOWED_TYPES.indexOf(type) === -1) return { ok: false, error: 'bad type' };
  var mobile = String(d.mobile || '').replace(/[\s\-().]/g, '');
  if (!/^\+?\d{10,15}$/.test(mobile)) return { ok: false, error: 'bad mobile' };
  var name = String(d.name || '').trim();
  if (!name) return { ok: false, error: 'name required' };
  var leadId = String(d.lead_id || '').trim();
  if (!/^[A-Z0-9]{6,24}$/.test(leadId)) return { ok: false, error: 'bad lead id' };

  var isProduct = type === 'product';
  var columns = isProduct ? PRODUCT_COLUMNS : TAXI_COLUMNS;
  var sheet = getSheet_(isProduct ? PRODUCT_SHEET : TAXI_SHEET, columns);

  // The same lead can arrive twice (double tap, retry): store it once.
  var last = sheet.getLastRow();
  if (last > 1) {
    var found = sheet.getRange(2, 2, last - 1, 1).createTextFinder(leadId).matchEntireCell(true).findNext();
    if (found) return { ok: true, duplicate: true };
  }

  d.mobile = mobile;
  d.consent_followup = String(d.consent_followup) === 'Yes' ? 'Yes' : 'No';
  d._received = new Date();
  d._status = 'New';
  var row = columns.map(function (c) {
    var key = c[1];
    if (key === '_blank') return '';
    if (key === '_received') return d._received;
    if (key === '_status') return d._status;
    return safeCell_(d[key], key === 'mobile');
  });
  sheet.appendRow(row);

  if (NOTIFY_EMAIL) {
    try {
      MailApp.sendEmail(NOTIFY_EMAIL, 'New ' + (isProduct ? 'product' : type) + ' enquiry: ' + name,
        'Lead ' + leadId + '\nName: ' + name + '\nMobile: ' + mobile + '\nOpen the sheet to see full details.');
    } catch (mailErr) { /* a failed email must never lose the lead */ }
  }
  return { ok: true, lead_id: leadId };
}

function handleEvent_(d) {
  var ev = String(d.event || '');
  if (ALLOWED_EVENTS.indexOf(ev) === -1) return { ok: false, error: 'bad event' };
  var sheet = getSheet_(EVENT_SHEET, EVENT_COLUMNS, true);
  d._received = new Date();
  sheet.appendRow(EVENT_COLUMNS.map(function (c) { return c[1] === '_received' ? d._received : safeCell_(d[c[1]], false); }));
  return { ok: true };
}

/** Counts only. Never returns names, mobile numbers or message text. */
function buildStats_() {
  var out = {
    ok: true, generated_at: new Date().toISOString(),
    totals: { enquiries: 0, genuine: 0, confirmed: 0, quotation_sent: 0, follow_up: 0, cancelled: 0, call_clicks: 0, whatsapp_clicks: 0, email_clicks: 0, form_submissions: 0, assistant_submissions: 0, product_enquiries: 0 },
    by_source: {}, by_landing_page: {}, by_service: {}, by_day: {}, clicks_by_page: {}, clicks_by_location: {}
  };
  function bump(o, k, n) { k = k || '(unknown)'; o[k] = (o[k] || 0) + (n || 1); }
  function dayKey(v) { var dt = v instanceof Date ? v : new Date(v); return isNaN(dt) ? '' : Utilities.formatDate(dt, Session.getScriptTimeZone(), 'yyyy-MM-dd'); }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var leads = ss.getSheetByName(TAXI_SHEET);
  if (leads && leads.getLastRow() > 1) {
    var rows = leads.getRange(2, 1, leads.getLastRow() - 1, TAXI_COLUMNS.length).getValues();
    var idx = {}; TAXI_COLUMNS.forEach(function (c, i) { idx[c[1]] = i; });
    rows.forEach(function (r) {
      var status = String(r[idx._status] || 'New');
      var src = String(r[idx.source] || '');
      out.totals.enquiries++;
      if (status === 'Cancelled') out.totals.cancelled++; else out.totals.genuine++;
      if (status === 'Confirmed') out.totals.confirmed++;
      if (status === 'Quotation Sent') out.totals.quotation_sent++;
      if (status === 'Follow-up Required') out.totals.follow_up++;
      if (/form$/.test(src)) out.totals.form_submissions++; else out.totals.assistant_submissions++;
      bump(out.by_source, String(r[idx.traffic_source] || 'unknown'));
      bump(out.by_landing_page, String(r[idx.landing_page] || r[idx.page] || '(unknown)'));
      bump(out.by_service, String(r[idx.service] || '(unknown)'));
      var dk = dayKey(r[idx._received]); if (dk) bump(out.by_day, dk);
    });
  }
  var prod = ss.getSheetByName(PRODUCT_SHEET);
  if (prod && prod.getLastRow() > 1) out.totals.product_enquiries = prod.getLastRow() - 1;

  var ev = ss.getSheetByName(EVENT_SHEET);
  if (ev && ev.getLastRow() > 1) {
    var erows = ev.getRange(2, 1, ev.getLastRow() - 1, EVENT_COLUMNS.length).getValues();
    erows.forEach(function (r) {
      var name = String(r[1]);
      if (name === 'phone_click') out.totals.call_clicks++;
      else if (name === 'whatsapp_click') out.totals.whatsapp_clicks++;
      else if (name === 'email_click') out.totals.email_clicks++;
      else return;
      bump(out.clicks_by_page, String(r[2] || '(unknown)') + ' | ' + name);
      bump(out.clicks_by_location, String(r[3] || 'content') + ' | ' + name);
    });
  }
  return out;
}

/** Plain text only: trims length and stops spreadsheet formulas ("=...", "+...", "@...") from running. */
function safeCell_(value, forceText) {
  if (value === undefined || value === null) return '';
  var s = String(value).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').slice(0, MAX_FIELD);
  if (forceText || /^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

function getSheet_(name, columns, noStatus) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    var headers = columns.map(function (c) { return c[0]; });
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    var statusCol = headers.indexOf('Status') + 1;
    if (noStatus || !statusCol) return sheet;
    var rule = SpreadsheetApp.newDataValidation().requireValueInList(STATUSES, true).setAllowInvalid(false).build();
    sheet.getRange(2, statusCol, sheet.getMaxRows() - 1, 1).setDataValidation(rule);
  }
  return sheet;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
