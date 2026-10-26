// Patnitop Travels Hub — shared site behaviour

document.addEventListener('DOMContentLoaded', function () {

  var WA_NUMBER = '919103331334'; // country code + 9103331334
  var PHONE_DISPLAY = '9103331334';

  // Mobile nav toggle
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
      var expanded = nav.classList.contains('open');
      toggle.setAttribute('aria-expanded', expanded);
    });
    // close menu after a link is tapped
    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { nav.classList.remove('open'); });
    });
  }

  // WhatsApp buttons: build a pre-filled message from data attributes,
  // or fall back to a generic enquiry message.
  document.querySelectorAll('[data-whatsapp]').forEach(function (btn) {
    var customMsg = btn.getAttribute('data-wa-message');
    var msg = customMsg || "Hello Patnitop Travels Hub, I would like to enquire about a taxi/hotel booking.";
    btn.href = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(msg);
  });

  // Date inputs: no travel dates in the past.
  function todayISO() {
    var d = new Date();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
  }
  document.querySelectorAll('input[type="date"]').forEach(function (i) { i.min = todayISO(); });
  var travelDate = document.getElementById('travel_date');
  var returnDate = document.getElementById('return_date');
  if (travelDate && returnDate) {
    travelDate.addEventListener('change', function () {
      returnDate.min = travelDate.value || todayISO();
    });
  }

  // ---------------------------------------------------------------
  // Shared handling for the taxi enquiry form and the product enquiry form.
  // Each submit: validate -> record lead (if a lead endpoint is configured)
  // -> track -> show a WhatsApp hand-off with the details pre-filled.
  // A submission is an ENQUIRY, never a confirmed booking.
  // ---------------------------------------------------------------
  function showHandoff(box, name, waLink, intro) {
    if (!box) return;
    box.textContent = '';
    box.classList.add('show');
    var p = document.createElement('div');
    p.textContent = 'Thank you, ' + (name || 'traveller') + '! ' + intro + ' Or call ';
    var tel = document.createElement('a');
    tel.href = 'tel:+91' + PHONE_DISPLAY;
    tel.textContent = PHONE_DISPLAY;
    p.appendChild(tel);
    p.appendChild(document.createTextNode(' directly. This is an enquiry, not a confirmed booking.'));
    box.appendChild(p);
    var wrap = document.createElement('div');
    wrap.style.marginTop = '12px';
    var a = document.createElement('a');
    a.className = 'btn btn-whatsapp';
    a.href = waLink;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = '💬 Send Enquiry on WhatsApp';
    wrap.appendChild(a);
    box.appendChild(wrap);
    box.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function validMobile(form) {
    var input = form.querySelector('input[name="mobile"]');
    var cleaned = window.ptvLead ? window.ptvLead.cleanMobile(input.value) : input.value.trim();
    input.setCustomValidity(cleaned ? '' : 'Please enter a valid mobile number (10 to 15 digits).');
    if (!cleaned) { input.reportValidity(); return ''; }
    return cleaned;
  }

  // Taxi / hotel / sightseeing enquiry form
  var form = document.getElementById('enquiry-form');
  if (form) {
    form.addEventListener('input', function (e) {
      if (e.target && e.target.setCustomValidity) e.target.setCustomValidity('');
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var get = function (k) { return (data.get(k) || '').toString().trim(); };

      if (get('website')) { form.reset(); return; } // honeypot: a bot filled the hidden field

      var mobile = validMobile(form);
      if (!mobile) return;
      var rd = document.getElementById('return_date');
      if (get('return_date') && get('travel_date') && get('return_date') < get('travel_date')) {
        rd.setCustomValidity('Return date cannot be before the travel date.');
        rd.reportValidity();
        return;
      }

      var consent = get('consent_followup') === 'Yes' ? 'Yes' : 'No';
      var leadId = window.ptvLead ? window.ptvLead.newId() : '';
      var payload = {
        lead_id: leadId, type: 'taxi', source: 'contact-form', service: 'Taxi / travel enquiry',
        name: get('name'), mobile: mobile, pickup: get('pickup'), drop: get('drop'),
        travel_date: get('travel_date'), return_date: get('return_date'), passengers: get('passengers'),
        vehicle: get('vehicle'), hotel_required: get('hotel_required'), sightseeing_required: get('sightseeing_required'),
        notes: get('message'), consent_followup: consent
      };
      if (window.ptvLead) window.ptvLead.submit(payload);
      if (window.ptvTrack) {
        window.ptvTrack('generate_lead', { lead_type: 'taxi', source: 'contact_form' });
        window.ptvTrack('quote_request', { lead_type: 'taxi', source: 'contact_form' });
      }

      var lines = [
        'New booking enquiry — Patnitop Travels Hub',
        'Name: ' + payload.name,
        'Mobile: ' + mobile,
        'Pickup: ' + payload.pickup,
        'Drop: ' + payload.drop,
        'Travel date: ' + payload.travel_date,
        'Return date: ' + (payload.return_date || 'N/A'),
        'Passengers: ' + payload.passengers,
        'Vehicle: ' + payload.vehicle,
        'Hotel required: ' + payload.hotel_required,
        'Sightseeing required: ' + payload.sightseeing_required,
        'Message: ' + (payload.notes || 'N/A'),
        'OK to follow up: ' + consent,
        'Ref: ' + leadId
      ];
      var waLink = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(lines.join('\n'));
      showHandoff(document.getElementById('form-success'), payload.name, waLink,
        'Your enquiry is ready to send. Tap the button below to send it to us on WhatsApp.');
      form.reset();
    });
  }

  // Local products enquiry form (separate from taxi bookings)
  var pform = document.getElementById('product-enquiry-form');
  if (pform) {
    pform.addEventListener('input', function (e) {
      if (e.target && e.target.setCustomValidity) e.target.setCustomValidity('');
    });
    pform.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(pform);
      var get = function (k) { return (data.get(k) || '').toString().trim(); };
      if (get('website')) { pform.reset(); return; }

      var mobile = validMobile(pform);
      if (!mobile) return;
      var products = data.getAll('products').map(function (v) { return String(v); });
      if (!products.length) {
        var first = pform.querySelector('input[name="products"]');
        first.setCustomValidity('Please tick at least one product.');
        first.reportValidity();
        return;
      }

      var consent = get('consent_followup') === 'Yes' ? 'Yes' : 'No';
      var leadId = window.ptvLead ? window.ptvLead.newId() : '';
      var payload = {
        lead_id: leadId, type: 'product', source: 'products-form', service: 'Local products enquiry',
        name: get('name'), mobile: mobile, products: products.join(', '), quantity: get('quantity'),
        delivery_place: get('delivery_place'), notes: get('message'), consent_followup: consent
      };
      if (window.ptvLead) window.ptvLead.submit(payload);
      if (window.ptvTrack) {
        window.ptvTrack('product_enquiry', { source: 'products_form' });
        window.ptvTrack('generate_lead', { lead_type: 'product', source: 'products_form' });
      }

      var lines = [
        'PRODUCT ENQUIRY (not a taxi booking) — Patnitop Travels Hub',
        'Name: ' + payload.name,
        'Mobile: ' + mobile,
        'Interested in: ' + payload.products,
        'Quantity: ' + (payload.quantity || 'N/A'),
        'Delivery place: ' + (payload.delivery_place || 'N/A'),
        'Message: ' + (payload.notes || 'N/A'),
        'OK to follow up: ' + consent,
        'Ref: ' + leadId
      ];
      var waLink = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(lines.join('\n'));
      showHandoff(document.getElementById('product-form-success'), payload.name, waLink,
        'Your product enquiry is ready to send. Tap the button below to send it to us on WhatsApp.');
      pform.reset();
    });
  }

  // Photography / reels enquiry form (separate from taxi bookings).
  // Stored with type 'other' so the existing lead sheet accepts it without
  // any change to the Apps Script; the shoot details are kept in Notes.
  var phform = document.getElementById('photo-enquiry-form');
  if (phform) {
    phform.addEventListener('input', function (e) {
      if (e.target && e.target.setCustomValidity) e.target.setCustomValidity('');
    });
    phform.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(phform);
      var get = function (k) { return (data.get(k) || '').toString().trim(); };
      if (get('website')) { phform.reset(); return; }

      var mobile = validMobile(phform);
      if (!mobile) return;

      var consent = get('consent_followup') === 'Yes' ? 'Yes' : 'No';
      var leadId = window.ptvLead ? window.ptvLead.newId() : '';
      var details = 'Shoot type: ' + get('shoot_type') + ' | Wants: ' + get('deliverable') +
        ' | Taxi needed: ' + get('taxi') + (get('message') ? ' | Message: ' + get('message') : '');
      var payload = {
        lead_id: leadId, type: 'other', source: 'photography-form', service: 'Photography / reels enquiry',
        name: get('name'), mobile: mobile, pickup: get('location'),
        travel_date: get('preferred_date'), passengers: get('people'),
        notes: details, consent_followup: consent
      };
      if (window.ptvLead) window.ptvLead.submit(payload);
      if (window.ptvTrack) {
        window.ptvTrack('photography_enquiry', { source: 'photography_form' });
        window.ptvTrack('generate_lead', { lead_type: 'photography', source: 'photography_form' });
        window.ptvTrack('quote_request', { lead_type: 'photography', source: 'photography_form' });
      }

      var lines = [
        'PHOTOGRAPHY ENQUIRY (not a taxi booking) — Patnitop Travels Hub',
        'Name: ' + payload.name,
        'Mobile: ' + mobile,
        'Shoot type: ' + get('shoot_type'),
        'Preferred date: ' + (payload.travel_date || 'Flexible / not decided'),
        'Number of people: ' + payload.passengers,
        'Preferred location: ' + get('location'),
        'Photos, reels or both: ' + get('deliverable'),
        'Taxi needed: ' + get('taxi'),
        'Message: ' + (get('message') || 'N/A'),
        'OK to follow up: ' + consent,
        'Ref: ' + leadId
      ];
      var waLink = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(lines.join('\n'));
      showHandoff(document.getElementById('photo-form-success'), payload.name, waLink,
        'Your photography enquiry is ready to send. Tap the button below to send it to us on WhatsApp.');
      phform.reset();
    });
  }

  // Simple year stamp in footer
  var yearEl = document.getElementById('year');
  if (yearEl) { yearEl.textContent = new Date().getFullYear(); }

});
