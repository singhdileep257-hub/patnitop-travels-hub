// Patnitop Travels Hub — owner lead dashboard (dashboard.html).
// Reads COUNTS ONLY from the private Google Apps Script web app (?action=stats&key=...).
// No names or phone numbers are ever sent to this page. The key is kept only in this
// browser tab (sessionStorage) and is forgotten when the tab is closed.
// Search keywords come from a Search Console export you pick on your own device; the file
// is read in the browser and is never uploaded anywhere.
(function () {
  'use strict';
  var ENDPOINT = window.DASH_ENDPOINT || '';
  var $ = function (id) { return document.getElementById(id); };

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = String(text);
    return n;
  }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
  function msg(text, isErr) { var m = $('dash-msg'); m.textContent = text || ''; m.className = 'dash-msg' + (isErr ? ' err' : ''); }
  function store(k, v) { try { if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v); } catch (e) { /* storage blocked */ } }
  function load(k) { try { return sessionStorage.getItem(k) || ''; } catch (e) { return ''; } }

  function tile(n, label, hint, cls) {
    var t = el('div', 'dash-tile' + (cls ? ' ' + cls : ''));
    t.appendChild(el('div', 'n', n)); t.appendChild(el('div', 'l', label));
    if (hint) t.appendChild(el('div', 'h', hint));
    return t;
  }

  function table(box, headers, rows, emptyText) {
    clear(box);
    if (!rows.length) { box.appendChild(el('p', 'dash-empty', emptyText || 'Nothing recorded yet.')); return; }
    var t = el('table', 'dash-table'), thead = el('thead'), hr = el('tr');
    headers.forEach(function (h, i) { hr.appendChild(el('th', i > 0 ? 'num' : '', h)); });
    thead.appendChild(hr); t.appendChild(thead);
    var tb = el('tbody');
    rows.forEach(function (r) {
      var tr = el('tr');
      r.forEach(function (c, i) { tr.appendChild(el('td', i > 0 ? 'num' : '', c)); });
      tb.appendChild(tr);
    });
    t.appendChild(tb); box.appendChild(t);
  }

  function sortedPairs(obj) {
    return Object.keys(obj || {}).map(function (k) { return [k, obj[k]]; }).sort(function (a, b) { return b[1] - a[1]; });
  }

  // clicks_by_page keys look like "/page.html | phone_click"
  function clicksPerPage(map) {
    var out = {};
    Object.keys(map || {}).forEach(function (k) {
      var parts = k.split(' | '), page = parts[0], ev = parts[1];
      out[page] = out[page] || { call: 0, wa: 0 };
      if (ev === 'phone_click') out[page].call += map[k];
      else if (ev === 'whatsapp_click') out[page].wa += map[k];
    });
    return out;
  }

  function render(st) {
    var t = st.totals || {};
    var tiles = $('dash-tiles'); clear(tiles);
    tiles.appendChild(tile(t.enquiries || 0, 'Total enquiries', 'Form + chat assistant submissions'));
    tiles.appendChild(tile(t.genuine || 0, 'Genuine leads', 'Enquiries not marked Cancelled'));
    tiles.appendChild(tile(t.call_clicks || 0, 'Call button taps', 'Call attempts, not answered calls'));
    tiles.appendChild(tile(t.whatsapp_clicks || 0, 'WhatsApp taps', 'Chats opened, not messages sent'));
    tiles.appendChild(tile(t.form_submissions || 0, 'Form submissions', (t.assistant_submissions || 0) + ' more via chat assistant'));
    tiles.appendChild(tile(t.confirmed || 0, 'Confirmed bookings', 'Only when you set Status = Confirmed', 'conf'));

    var pages = {};
    Object.keys(st.by_landing_page || {}).forEach(function (p) { pages[p] = pages[p] || { enq: 0, call: 0, wa: 0 }; pages[p].enq = st.by_landing_page[p]; });
    var cp = clicksPerPage(st.clicks_by_page);
    Object.keys(cp).forEach(function (p) { pages[p] = pages[p] || { enq: 0, call: 0, wa: 0 }; pages[p].call = cp[p].call; pages[p].wa = cp[p].wa; });
    var prow = Object.keys(pages).map(function (p) { return [p, pages[p].enq, pages[p].call, pages[p].wa]; })
      .sort(function (a, b) { return (b[1] * 5 + b[2] + b[3]) - (a[1] * 5 + a[2] + a[3]); }).slice(0, 15);
    table($('dash-pages'), ['Page', 'Enquiries (landing)', 'Call taps', 'WhatsApp taps'], prow);

    table($('dash-sources'), ['Enquiry source', 'Enquiries'], sortedPairs(st.by_source).map(function (p) { return [p[0], p[1]]; }));
    table($('dash-services'), ['Service / page asked about', 'Enquiries'], sortedPairs(st.by_service).slice(0, 15).map(function (p) { return [p[0], p[1]]; }));

    var loc = {};
    Object.keys(st.clicks_by_location || {}).forEach(function (k) {
      var parts = k.split(' | '), where = parts[0], ev = parts[1];
      loc[where] = loc[where] || { call: 0, wa: 0 };
      if (ev === 'phone_click') loc[where].call += st.clicks_by_location[k];
      else if (ev === 'whatsapp_click') loc[where].wa += st.clicks_by_location[k];
    });
    table($('dash-buttons'), ['Button position', 'Call taps', 'WhatsApp taps'],
      Object.keys(loc).map(function (w) { return [w, loc[w].call, loc[w].wa]; }).sort(function (a, b) { return (b[1] + b[2]) - (a[1] + a[2]); }));

    // last 30 days of enquiries
    var bars = $('dash-bars'); clear(bars);
    var days = [], now = new Date(), max = 1;
    for (var i = 29; i >= 0; i--) {
      var d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
      var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
      var n = (st.by_day || {})[key] || 0; if (n > max) max = n; days.push([key, n]);
    }
    days.forEach(function (x) { var b = el('span'); b.style.height = Math.max(2, Math.round(x[1] / max * 100)) + '%'; b.title = x[0] + ': ' + x[1]; bars.appendChild(b); });
    $('dash-updated').textContent = 'Updated ' + new Date(st.generated_at).toLocaleString();
    $('dash-results').hidden = false;
  }

  function loadStats() {
    var key = $('dash-key').value.trim() || load('ptv_dash_key');
    if (!ENDPOINT) { msg('The lead sheet is not connected yet. Set lead_endpoint in site.config.json, rebuild and deploy (see docs/SETUP.md).', true); return; }
    if (!key) { msg('Enter your dashboard key first.', true); return; }
    msg('Loading…');
    fetch(ENDPOINT + (ENDPOINT.indexOf('?') === -1 ? '?' : '&') + 'action=stats&key=' + encodeURIComponent(key), { method: 'GET', redirect: 'follow' })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) { msg(j && j.error === 'bad key' ? 'That key is not correct.' : ('Could not load: ' + ((j && j.error) || 'unknown error')), true); return; }
        store('ptv_dash_key', key); $('dash-key').value = ''; msg(''); render(j);
      })
      .catch(function () { msg('Could not reach the lead sheet. Check your internet connection and that the Apps Script web app is deployed for "Anyone".', true); });
  }

  // --- minimal CSV parser (handles quoted fields) for a Search Console export ---
  function parseCSV(text) {
    var rows = [], row = [], cur = '', q = false, i, c;
    text = text.replace(/^﻿/, '');
    for (i = 0; i < text.length; i++) {
      c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c;
      } else if (c === '"') q = true;
      else if (c === ',') { row.push(cur); cur = ''; }
      else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cur); cur = ''; if (row.length > 1 || row[0] !== '') rows.push(row); row = []; }
      else cur += c;
    }
    if (cur !== '' || row.length) { row.push(cur); rows.push(row); }
    return rows;
  }

  function showGsc(text) {
    var rows = parseCSV(text), box = $('dash-gsc');
    if (rows.length < 2) { clear(box); box.appendChild(el('p', 'dash-err dash-empty', 'That file has no rows.')); return; }
    var h = rows[0].map(function (x) { return x.trim().toLowerCase(); });
    var iq = h.findIndex(function (x) { return /query|queries|page/.test(x); });
    var ic = h.indexOf('clicks'), ii = h.indexOf('impressions'), ip = h.indexOf('position');
    if (iq < 0 || ic < 0 || ii < 0) { clear(box); box.appendChild(el('p', 'dash-empty', 'Use the Queries.csv (or Pages.csv) file from Search Console → Performance → Export.')); return; }
    var data = rows.slice(1).map(function (r) { return [r[iq], Number(r[ic]) || 0, Number(r[ii]) || 0, ip >= 0 ? Number(r[ip]) || 0 : 0]; })
      .sort(function (a, b) { return b[1] - a[1] || b[2] - a[2]; }).slice(0, 25);
    table(box, [rows[0][iq], 'Clicks', 'Impressions', 'Avg position'], data.map(function (r) { return [r[0], r[1], r[2], r[3] ? r[3].toFixed(1) : '-']; }));
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('dash-load').addEventListener('click', loadStats);
    $('dash-key').addEventListener('keydown', function (e) { if (e.key === 'Enter') loadStats(); });
    $('dash-forget').addEventListener('click', function () { store('ptv_dash_key', null); $('dash-results').hidden = true; msg('Key forgotten on this device.'); });
    $('dash-file').addEventListener('change', function (e) {
      var f = e.target.files && e.target.files[0]; if (!f) return;
      var r = new FileReader(); r.onload = function () { showGsc(String(r.result)); }; r.readAsText(f);
    });
    if (load('ptv_dash_key') && ENDPOINT) loadStats();
    else if (!ENDPOINT) msg('The lead sheet is not connected yet. Set lead_endpoint in site.config.json, rebuild and deploy (see docs/SETUP.md).', true);
  });
})();
