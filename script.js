// Patnitop Travels Hub — shared site behaviour

document.addEventListener('DOMContentLoaded', function () {

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

  // WhatsApp buttons: the href built into the HTML at build time (see
  // build.py / wa_href()) already works with JS off, so this only
  // ENHANCES buttons that carry a page-specific data-wa-message —
  // it never creates the link from scratch and never overwrites a
  // working href with nothing.
  var WA_NUMBER = '919103331334'; // country code + 9103331334
  document.querySelectorAll('[data-whatsapp][data-wa-message]').forEach(function (btn) {
    var msg = btn.getAttribute('data-wa-message');
    if (msg) {
      btn.href = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(msg);
    }
  });

  // Booking form: build a WhatsApp message from the filled fields and
  // show an on-page confirmation (no backend required to get started).
  var form = document.getElementById('enquiry-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var get = function (k) { return (data.get(k) || '').toString().trim(); };

      var lines = [
        'New booking enquiry — Patnitop Travels Hub',
        'Name: ' + get('name'),
        'Mobile: ' + get('mobile'),
        'Pickup: ' + get('pickup'),
        'Drop: ' + get('drop'),
        'Travel date: ' + get('travel_date'),
        'Return date: ' + (get('return_date') || 'N/A'),
        'Passengers: ' + get('passengers'),
        'Vehicle: ' + get('vehicle'),
        'Hotel required: ' + get('hotel_required'),
        'Sightseeing required: ' + get('sightseeing_required'),
        'Message: ' + (get('message') || 'N/A')
      ];
      var waMsg = encodeURIComponent(lines.join('\n'));
      var waLink = 'https://wa.me/919103331334?text=' + waMsg;

      var success = document.getElementById('form-success');
      if (success) {
        success.classList.add('show');
        success.innerHTML = 'Thank you, ' + (get('name') || 'traveller') +
          '! Your enquiry is ready to send. Tap the button below to send it to us on WhatsApp, or call ' +
          '<a href="tel:+919103331334">9103331334</a> directly.' +
          '<div style="margin-top:12px;"><a class="btn btn-whatsapp" href="' + waLink + '" target="_blank" rel="noopener">💬 Send Enquiry on WhatsApp</a></div>';
        success.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      form.reset();
    });
  }

  // Simple year stamp in footer
  var yearEl = document.getElementById('year');
  if (yearEl) { yearEl.textContent = new Date().getFullYear(); }

});
