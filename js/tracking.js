// Patnitop Travels Hub — conversion tracking + lead submission helper.
//
// Tracking: every event goes to window.dataLayer, and to Google Analytics 4
// via gtag() ONLY if a GA4 measurement ID was set in site.config.json (build.py
// then loads gtag). With no ID, nothing leaves the browser.
//
// Events sent:
//   phone_click      tap on any tel: link          {link_location}
//   whatsapp_click   tap on any wa.me link         {link_location}
//   email_click      tap on any mailto: link       {link_location}
//   generate_lead    an enquiry was submitted      {lead_type, source}
//   quote_request    a fare/itinerary was asked for {lead_type, source}
//   product_enquiry  a product enquiry was made    {source}
//   photography_enquiry  a photography enquiry was made {source}
// "Confirmed booking" cannot be seen from the website — confirmation happens
// on a call or WhatsApp. Record it by setting the lead's Status to Confirmed
// in the lead sheet (see docs/SETUP.md).
//
// Click events (phone_click, whatsapp_click, email_click) are ALSO posted, with no
// personal data, to the same private Google Apps Script endpoint when one is set, so the
// lead dashboard can count them without needing a Google Analytics login. A tap on a Call
// button is a call ATTEMPT, never a confirmed booking.
//
// Attribution: the first page and traffic source of each visit are remembered for the
// browser session (sessionStorage) and attached to every enquiry and click event.
//
// Leads: ptvLead.submit(payload) posts one enquiry to the Google Apps Script
// web app set as lead_endpoint. With no endpoint it does nothing, and the
// WhatsApp / phone hand-off that every flow ends with still works.

(function () {
  'use strict';


  // ---------------------------------------------------------------
  // Visit attribution (first touch in this browser session)
  // ---------------------------------------------------------------
  function classifySource(utm, refHost) {
    if (utm.campaign && /^(gbp|gmb|google[-_ ]?business)/i.test(utm.campaign)) return 'google_business_profile';
    if (utm.source) return utm.medium ? utm.source + ' / ' + utm.medium : utm.source;
    if (!refHost) return 'direct';
    if (/(^|\.)google\./i.test(refHost)) return 'google_organic';
    if (/(^|\.)(bing|duckduckgo|yahoo|ecosia|yandex)\./i.test(refHost)) return 'other_search';
    if (/(facebook|instagram|t\.co|twitter|x\.com|youtube|whatsapp|linkedin)/i.test(refHost)) return 'social';
    return 'referral: ' + refHost;
  }

  function readAttribution() {
    var attr = null;
    try { attr = JSON.parse(sessionStorage.getItem('ptv_attr') || 'null'); } catch (e) { attr = null; }
    if (attr && attr.landing_page) return attr;
    var q = {};
    try { new URLSearchParams(location.search).forEach(function (v, k) { q[k] = v; }); } catch (e) { /* old browser */ }
    var refHost = '';
    try { if (document.referrer) { var u = new URL(document.referrer); if (u.host !== location.host) refHost = u.host; } } catch (e) { refHost = ''; }
    var utm = { source: (q.utm_source || '').slice(0, 60), medium: (q.utm_medium || '').slice(0, 60), campaign: (q.utm_campaign || '').slice(0, 60) };
    attr = {
      landing_page: location.pathname,
      traffic_source: classifySource(utm, refHost),
      referrer: refHost,
      utm_campaign: utm.campaign
    };
    try { sessionStorage.setItem('ptv_attr', JSON.stringify(attr)); } catch (e) { /* storage blocked: still works for this page */ }
    return attr;
  }
  window.ptvAttribution = readAttribution;
  try { readAttribution(); } catch (e) { /* capture the first touch as soon as the page loads */ }

  var EVENT_NAMES = { phone_click: 1, whatsapp_click: 1, email_click: 1 };
  function sendEvent(name, params) {
    try {
      if (!EVENT_NAMES[name]) return;
      var url = (typeof AGENT_DATA !== 'undefined' && AGENT_DATA.leadEndpoint) ? AGENT_DATA.leadEndpoint : '';
      if (!url) return;
      var a = readAttribution();
      var body = JSON.stringify({
        type: 'event', event: name, page: location.pathname, link_location: (params && params.link_location) || '',
        traffic_source: a.traffic_source, landing_page: a.landing_page, referrer: a.referrer
      });
      fetch(url, { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: body, keepalive: true }).catch(function () {});
    } catch (e) { /* tracking must never break the page */ }
  }

  function track(name, params) {
    params = params || {};
    params.page_path = location.pathname;
    sendEvent(name, params);
    try {
      window.dataLayer = window.dataLayer || [];
      if (typeof window.gtag === 'function') {
        window.gtag('event', name, params);
      } else {
        var evt = { event: name };
        for (var k in params) { if (Object.prototype.hasOwnProperty.call(params, k)) evt[k] = params[k]; }
        window.dataLayer.push(evt);
      }
    } catch (e) { /* tracking must never break the page */ }
  }
  window.ptvTrack = track;

  function placement(a) {
    if (a.closest('#ptv-agent-root')) return 'agent';
    if (a.closest('.mobile-bar')) return 'mobile_bar';
    if (a.closest('.site-header')) return 'header';
    if (a.closest('.topbar')) return 'topbar';
    if (a.closest('.site-footer')) return 'footer';
    if (a.closest('.hero, .page-hero')) return 'hero';
    return 'content';
  }

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('tel:') === 0) track('phone_click', { link_location: placement(a) });
    else if (href.indexOf('wa.me/') !== -1) track('whatsapp_click', { link_location: placement(a) });
    else if (href.indexOf('mailto:') === 0) track('email_click', { link_location: placement(a) });
  }, true);

  // ---------------------------------------------------------------
  // Lead helper
  // ---------------------------------------------------------------
  function newLeadId() {
    return 'L' + Date.now().toString(36).toUpperCase() + Math.random().toString(36).slice(2, 6).toUpperCase();
  }

  // Returns the cleaned number (digits, optional leading +) or '' if invalid.
  function cleanMobile(v) {
    var s = String(v || '').replace(/[\s\-().]/g, '');
    return /^\+?\d{10,15}$/.test(s) ? s : '';
  }

  function endpoint() {
    return (typeof AGENT_DATA !== 'undefined' && AGENT_DATA.leadEndpoint) ? AGENT_DATA.leadEndpoint : '';
  }

  window.ptvLead = {
    cleanMobile: cleanMobile,
    newId: newLeadId,
    enabled: function () { return !!endpoint(); },
    // Resolves {sent:true} when the request was handed to the network and the
    // browser reported no error; {sent:false, reason} when offline, timed out
    // or failed. A cross-origin "no-cors" POST cannot read the server's reply,
    // so {sent:true} means "delivered to the endpoint", not "row confirmed".
    submit: function (payload) {
      var url = endpoint();
      if (!url) return Promise.resolve({ sent: false, reason: 'no-endpoint' });
      if (typeof navigator !== 'undefined' && navigator.onLine === false) return Promise.resolve({ sent: false, reason: 'offline' });
      payload = payload || {};
      if (!payload.lead_id) payload.lead_id = newLeadId();
      payload.submitted_at = new Date().toISOString();
      payload.page = location.pathname;
      var attr = readAttribution();
      payload.traffic_source = attr.traffic_source;
      payload.landing_page = attr.landing_page;
      payload.referrer = attr.referrer;
      var ctrl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 10000) : null;
      try {
        return fetch(url, {
          method: 'POST',
          mode: 'no-cors',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          body: JSON.stringify(payload),
          keepalive: true,
          signal: ctrl ? ctrl.signal : undefined
        }).then(function () { if (timer) clearTimeout(timer); return { sent: true, lead_id: payload.lead_id }; })
          .catch(function (e) { if (timer) clearTimeout(timer); return { sent: false, reason: (e && e.name === 'AbortError') ? 'timeout' : 'network' }; });
      } catch (e) {
        if (timer) clearTimeout(timer);
        return Promise.resolve({ sent: false, reason: 'error' });
      }
    }
  };
})();
