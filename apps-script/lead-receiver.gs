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

// Column header -> key in the JSON the website sends.
var TAXI_COLUMNS = [
  ['Received', '_received'], ['Lead ID', 'lead_id'], ['Status', '_status'], ['Type', 'type'], ['Source', 'source'],
  ['Service', 'service'], ['Name', 'name'], ['Mobile', 'mobile'], ['Pickup', 'pickup'], ['Drop', 'drop'],
  ['Travel date', 'travel_date'], ['Return date', 'return_date'], ['Passengers', 'passengers'], ['Vehicle', 'vehicle'],
  ['Trip type', 'trip_type'], ['Hotel required', 'hotel_required'], ['Sightseeing required', 'sightseeing_required'],
  ['Notes', 'notes'], ['Quote shown', 'quote_shown'], ['Follow-up consent', 'consent_followup'], ['Page', 'page'],
  ['Internal notes', '_blank']
];
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
}

/** Opening the web-app URL in a browser shows this, so you can check the deployment is live. */
function doGet() {
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

/** Plain text only: trims length and stops spreadsheet formulas ("=...", "+...", "@...") from running. */
function safeCell_(value, forceText) {
  if (value === undefined || value === null) return '';
  var s = String(value).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').slice(0, MAX_FIELD);
  if (forceText || /^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

function getSheet_(name, columns) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    var headers = columns.map(function (c) { return c[0]; });
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    var statusCol = headers.indexOf('Status') + 1;
    var rule = SpreadsheetApp.newDataValidation().requireValueInList(STATUSES, true).setAllowInvalid(false).build();
    sheet.getRange(2, statusCol, sheet.getMaxRows() - 1, 1).setDataValidation(rule);
  }
  return sheet;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
