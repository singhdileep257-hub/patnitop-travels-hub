#!/usr/bin/env python3
"""
Static site generator for Patnitop Travels Hub.
Run: python3 build.py
Outputs finished .html files into the project root (next to css/, js/).
Keeping this script means you (or Claude, later) can regenerate every
page instantly after editing shared header/footer/schema in one place.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://www.patnitoptravelshub.com"  # placeholder — update once domain is live
PHONE = "9103331334"
PHONE2 = "8493988568"
PHONE_INTL = "+919103331334"
EMAIL = "singhdileep257@gmail.com"

# WhatsApp: number is fixed here and used to build a REAL, working href at
# build time (no dependence on JS to function). JS (js/script.js) may still
# swap in a page-specific message on top of this, but the button works even
# if JS never runs.
WA_NUMBER = "919103331334"
WA_DEFAULT_MSG = "Hello Patnitop Travels Hub, I would like to enquire about a taxi/hotel booking."

def wa_href(message=None):
    import urllib.parse
    msg = message or WA_DEFAULT_MSG
    return f"https://wa.me/{WA_NUMBER}?text={urllib.parse.quote(msg)}"

NAV_ITEMS = [
    ("index.html", "Home"),
    ("taxi-services.html", "Taxi Services"),
    ("patnitop-sightseeing.html", "Sightseeing"),
    ("hotel-booking.html", "Hotels"),
    ("tour-packages.html", "J&K Packages"),
    ("vehicles.html", "Vehicles"),
    ("faq.html", "FAQ"),
    ("contact.html", "Contact"),
]

def road_divider():
    return '''<svg class="road-divider" viewBox="0 0 1180 34" preserveAspectRatio="none" aria-hidden="true">
<path d="M0 20 Q 150 4, 300 20 T 600 20 T 900 20 T 1180 20"/>
</svg>'''

def head(title, description, canonical_path, extra_schema="", extra_meta=""):
    canonical = f"{SITE_URL}/{canonical_path}" if canonical_path != "index.html" else f"{SITE_URL}/"
    og_image = f"{SITE_URL}/images/patnitop-hero.jpg"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
{extra_meta}<meta name="geo.region" content="IN-JK">
<meta name="geo.placename" content="Patnitop, Jammu and Kashmir">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:locale" content="en_IN">
<meta property="og:site_name" content="Patnitop Travels Hub">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚕</text></svg>">
{extra_schema}
</head>
'''

def local_business_schema():
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "TravelAgency",
  "name": "Patnitop Travels Hub",
  "image": "{SITE_URL}/images/patnitop-hero.jpg",
  "url": "{SITE_URL}/",
  "telephone": "{PHONE_INTL}",
  "email": "{EMAIL}",
  "address": {{
    "@type": "PostalAddress",
    "streetAddress": "Patnitop",
    "addressLocality": "Patnitop",
    "addressRegion": "Jammu and Kashmir",
    "postalCode": "182121",
    "addressCountry": "IN"
  }},
  "geo": {{
    "@type": "GeoCoordinates",
    "latitude": 33.0994,
    "longitude": 75.3244
  }},
  "areaServed": ["Patnitop", "Katra", "Jammu", "Nathatop", "Sanasar", "Bhaderwah", "Srinagar", "Gulmarg", "Pahalgam", "Sonamarg"],
  "priceRange": "$$",
  "founder": {{ "@type": "Person", "name": "Dileep Singh" }},
  "sameAs": []
}}
</script>'''

def breadcrumb_schema(items):
    # items: list of (name, path)
    entries = []
    for i, (name, path) in enumerate(items, start=1):
        url = f"{SITE_URL}/" if path == "index.html" else f"{SITE_URL}/{path}"
        entries.append(f'{{"@type":"ListItem","position":{i},"name":"{name}","item":"{url}"}}')
    return '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[''' + ",".join(entries) + ''']}
</script>'''

def website_schema():
    # Single WebSite entity for the whole site — added on the homepage only
    # to avoid duplicating this once per page. Distinct @type from the
    # TravelAgency business entity, so this is not duplicate/overlapping
    # schema — it describes the website, not the business.
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Patnitop Travels Hub",
  "url": "{SITE_URL}/"
}}
</script>'''

def service_schema(name, description, area_served):
    # Used only on the 6 dedicated single-route/single-service landing
    # pages, where one page = one genuine service. Not added to the
    # taxi-services hub or homepage, which already cover the business
    # broadly via TravelAgency — adding Service there would duplicate it.
    areas = ",".join(f'"{a}"' for a in area_served)
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Service",
  "serviceType": "{name}",
  "name": "{name}",
  "description": "{description}",
  "provider": {{
    "@type": "TravelAgency",
    "name": "Patnitop Travels Hub",
    "telephone": "{PHONE_INTL}"
  }},
  "areaServed": [{areas}]
}}
</script>'''

def faq_schema(qas):
    entries = []
    for q, a in qas:
        entries.append(
            '{"@type":"Question","name":"' + q.replace('"', "'") + '","acceptedAnswer":{"@type":"Answer","text":"' + a.replace('"', "'") + '"}}'
        )
    return '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[''' + ",".join(entries) + ''']}
</script>'''

def topbar():
    return f'''<div class="topbar">
  <div class="container">
    <span>Dileep Singh · Patnitop Travels Hub — Taxi, Sightseeing &amp; Hotel Booking across J&amp;K</span>
    <span><a href="tel:+91{PHONE}">📞 {PHONE}</a> &nbsp;|&nbsp; <a href="mailto:{EMAIL}">{EMAIL}</a></span>
  </div>
</div>'''

def header(active_path):
    links = ""
    for path, label in NAV_ITEMS:
        cls = " class=\"active\"" if path == active_path else ""
        links += f'<a href="{path}"{cls}>{label}</a>\n      '
    return f'''{topbar()}
<header class="site-header">
  <div class="container">
    <a href="index.html" class="brand">
      <span class="mark">P</span>
      <span class="brand-text"><strong>Patnitop Travels Hub</strong><span>Taxi &amp; Travel Partner, J&amp;K</span></span>
    </a>
    <nav class="main-nav">
      {links}
    </nav>
    <div style="display:flex; align-items:center; gap:14px;">
      <a href="tel:+91{PHONE}" class="header-call"><span class="call-label">Call Now</span> 📞 {PHONE}</a>
      <button class="nav-toggle" aria-label="Open menu" aria-expanded="false">☰</button>
    </div>
  </div>
</header>'''

def breadcrumbs_html(items):
    # items: list of (name, path) excluding trailing separators
    parts = []
    for i, (name, path) in enumerate(items):
        if i == len(items) - 1:
            parts.append(f'<span>{name}</span>')
        else:
            parts.append(f'<a href="{path}">{name}</a>')
    return f'''<div class="breadcrumbs"><div class="container">{" &raquo; ".join(parts)}</div></div>'''

def mobile_bar():
    return f'''<div class="mobile-bar">
  <div class="row">
    <a class="call" href="tel:+91{PHONE}"><span class="icon">📞</span>Call</a>
    <a class="whatsapp" href="{wa_href()}" data-whatsapp target="_blank" rel="noopener"><span class="icon">💬</span>WhatsApp</a>
    <a class="book" href="contact.html#booking-form"><span class="icon">🚕</span>Book Now</a>
  </div>
</div>'''

def footer():
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>Patnitop Travels Hub</h4>
        <p>Taxi, sightseeing and hotel booking assistance for tourists visiting Patnitop and Jammu &amp; Kashmir. Run by Dileep Singh, based locally in Patnitop.</p>
      </div>
      <div>
        <h4>Explore</h4>
        <ul>
          <li><a href="taxi-services.html">Taxi Services</a></li>
          <li><a href="patnitop-sightseeing.html">Patnitop Sightseeing</a></li>
          <li><a href="hotel-booking.html">Hotel Booking</a></li>
          <li><a href="tour-packages.html">J&amp;K Tour Packages</a></li>
          <li><a href="vehicles.html">Vehicles</a></li>
        </ul>
      </div>
      <div>
        <h4>Popular Routes</h4>
        <ul>
          <li><a href="katra-to-patnitop-taxi.html">Katra to Patnitop Taxi</a></li>
          <li><a href="jammu-to-patnitop-taxi.html">Jammu to Patnitop Taxi</a></li>
          <li><a href="nathatop-sanasar-taxi.html">Nathatop &amp; Sanasar Taxi</a></li>
          <li><a href="srinagar-taxi.html">Srinagar Taxi</a></li>
          <li><a href="bhaderwah-taxi.html">Bhaderwah Taxi</a></li>
          <li><a href="airport-railway-transfer.html">Airport &amp; Railway Transfer</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact</h4>
        <ul>
          <li>Dileep Singh</li>
          <li><a href="tel:+91{PHONE}">{PHONE}</a></li>
          <li><a href="tel:+91{PHONE2}">{PHONE2}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li>Patnitop, Jammu &amp; Kashmir, India</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> Patnitop Travels Hub. All rights reserved.</span>
      <span>Wherever you want to travel in Jammu &amp; Kashmir, our team is ready to assist you.</span>
    </div>
  </div>
</footer>
{mobile_bar()}
<noscript>
  <!-- Fallback shown only if JavaScript is unavailable — the chat widget
       itself cannot render without JS, but a real WhatsApp link is still
       guaranteed here, consistent with the rest of the site. -->
  <a href="{wa_href()}" class="btn btn-whatsapp" style="position:fixed; right:16px; bottom:16px; z-index:70;">💬 Chat on WhatsApp</a>
</noscript>
<script src="js/script.js"></script>
<script src="js/agent-data.js"></script>
<script src="js/agent.js"></script>
</body>
</html>'''

def page(title, description, path, active_nav, body_html, breadcrumb_items=None, extra_schema="", schema_list=None, extra_meta=""):
    schemas = extra_schema
    if schema_list:
        schemas = "\n".join(schema_list)
    html = head(title, description, path, schemas, extra_meta)
    html += "<body>\n"
    html += header(active_nav)
    if breadcrumb_items:
        html += breadcrumbs_html(breadcrumb_items)
    html += body_html
    html += footer()
    return html

def write(path, content):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", path)

# ---------------------------------------------------------------
# Reusable content blocks
# ---------------------------------------------------------------

def cta_buttons(context="general"):
    return f'''<div class="btn-row">
  <a href="tel:+91{PHONE}" class="btn btn-pine">📞 Call Now</a>
  <a href="{wa_href()}" data-whatsapp class="btn btn-whatsapp" target="_blank" rel="noopener">💬 WhatsApp Now</a>
  <a href="contact.html#booking-form" class="btn btn-primary">🚕 Book a Taxi</a>
</div>'''

def faq_block(qas, heading="Frequently Asked Questions"):
    items = ""
    for q, a in qas:
        items += f'''<details class="faq-item">
  <summary>{q}</summary>
  <div class="faq-a">{a}</div>
</details>
'''
    return f'''<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Common questions</span>
      <h2>{heading}</h2>
    </div>
    {items}
  </div>
</section>'''

GLOBAL_FAQS = [
    ("How can I book a taxi in Patnitop?", "Call or WhatsApp Dileep Singh at 9103331334, or fill in the booking form on this website with your pickup, drop, date and vehicle preference. We will confirm your taxi booking directly."),
    ("Do you provide Katra to Patnitop taxi service?", "Yes, Patnitop Travels Hub provides Katra to Patnitop taxi service and Patnitop to Katra taxi service, including pickup from Katra Railway Station."),
    ("Do you provide Jammu Airport pickup?", "Yes, we offer Jammu Airport pickup and drop, as well as Jammu Railway Station pickup and drop, connecting onward to Patnitop and other destinations."),
    ("Can you arrange hotels in Patnitop?", "Yes, we assist tourists with hotel booking in Patnitop across budget, family and premium categories, and can arrange combined hotel plus taxi packages."),
    ("Do you provide Patnitop sightseeing?", "Yes, we provide local sightseeing taxi service covering Patnitop, Nathatop, Sanasar and nearby attractions."),
    ("Can I hire a taxi for Srinagar or Bhaderwah?", "Yes, our team can arrange taxi and travel assistance to Srinagar, Bhaderwah, Gulmarg, Pahalgam, Sonamarg and other destinations across Jammu &amp; Kashmir, subject to availability."),
    ("Do you provide Tempo Traveller?", "Yes, Tempo Traveller service is available for group and family travel. Call us to check current availability and fare."),
    ("How can I contact Dileep Singh?", "You can call or WhatsApp Dileep Singh at 9103331334 (alternate number 8493988568) or email singhdileep257@gmail.com."),
]

# ---------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------

def build_home():
    body = f'''
<section class="hero">
  <div class="container">
    <span class="eyebrow-plain">Patnitop · Katra · Jammu · Kashmir</span>
    <h1>Your Trusted Taxi &amp; Travel Partner in Jammu &amp; Kashmir</h1>
    <p class="lede">Patnitop Travels Hub arranges taxi service, local sightseeing, hotel booking and complete travel assistance for tourists visiting Patnitop, Katra, Jammu and across Jammu &amp; Kashmir.</p>
    <div class="hero-phone">Call <span class="num">{PHONE}</span> — Dileep Singh</div>
    <div class="btn-row">
      <a href="tel:+91{PHONE}" class="btn btn-primary">📞 Call Now</a>
      <a href="{wa_href()}" data-whatsapp class="btn btn-whatsapp" target="_blank" rel="noopener">💬 WhatsApp Now</a>
      <a href="contact.html#booking-form" class="btn btn-outline">🚕 Book a Taxi</a>
      <a href="hotel-booking.html" class="btn btn-outline">🏨 Book a Hotel</a>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">About us</span>
      <h2>Local travel help, from someone who knows these roads</h2>
    </div>
    <p>Patnitop Travels Hub is run by <strong>Dileep Singh</strong> and based locally in Patnitop, Jammu &amp; Kashmir. We help tourists with taxi service, sightseeing trips, hotel booking and travel planning — from the moment you land in Jammu or arrive at Katra, through Patnitop, and onward anywhere else in the Kashmir valley you want to go.</p>
    <p>Whether you need a one-way drop, a full round trip, an airport pickup, or a multi-day Jammu &amp; Kashmir itinerary, our team can arrange a taxi, tempo traveller or hotel that fits your plan.</p>
    <div class="trust-strip">
      <div class="item"><strong>Local to Patnitop</strong><span>Based on the ground, not a call centre elsewhere</span></div>
      <div class="item"><strong>Taxi + Hotel</strong><span>One point of contact for transport and stay</span></div>
      <div class="item"><strong>All of J&amp;K</strong><span>Katra, Jammu, Srinagar, Gulmarg, Pahalgam &amp; more</span></div>
      <div class="item"><strong>Book by phone or WhatsApp</strong><span>No app, no account needed</span></div>
    </div>
  </div>
</section>

{road_divider()}

<section class="section-alt">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Taxi services</span>
      <h2>Taxi service for every leg of your Jammu &amp; Kashmir trip</h2>
    </div>
    <div class="grid grid-3">
      <div class="card service-card"><h3>Katra ⇄ Patnitop Taxi</h3><p>Pickup from Katra or Katra Railway Station, straight to your Patnitop hotel, and back.</p><a class="card-link" href="katra-to-patnitop-taxi.html">Katra to Patnitop details →</a></div>
      <div class="card service-card"><h3>Jammu ⇄ Patnitop Taxi</h3><p>Airport and railway station transfers from Jammu to Patnitop and return.</p><a class="card-link" href="jammu-to-patnitop-taxi.html">Jammu to Patnitop details →</a></div>
      <div class="card service-card"><h3>Airport &amp; Railway Transfers</h3><p>Jammu Airport, Jammu Railway Station and Katra Railway Station pickup &amp; drop.</p><a class="card-link" href="airport-railway-transfer.html">Transfer details →</a></div>
      <div class="card service-card"><h3>Local Sightseeing Taxi</h3><p>Half-day and full-day sightseeing taxi around Patnitop, Nathatop and Sanasar.</p><a class="card-link" href="patnitop-sightseeing.html">Sightseeing details →</a></div>
      <div class="card service-card"><h3>Outstation Taxi</h3><p>One-way and round-trip outstation taxi anywhere in Jammu &amp; Kashmir.</p><a class="card-link" href="tour-packages.html">See destinations →</a></div>
      <div class="card service-card"><h3>Tempo Traveller</h3><p>For families and groups travelling together, with more luggage space.</p><a class="card-link" href="vehicles.html">View vehicles →</a></div>
    </div>
    <div class="btn-row"><a href="taxi-services.html" class="btn btn-pine">View All Taxi Services</a></div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Patnitop sightseeing</span>
      <h2>Places worth visiting around Patnitop</h2>
    </div>
    <div class="grid grid-4">
      <div class="card place-card"><h3>Nathatop</h3><p>Panoramic viewpoint above Patnitop, a short taxi ride away.</p></div>
      <div class="card place-card"><h3>Sanasar</h3><p>Meadow valley known for its bowl-shaped landscape.</p></div>
      <div class="card place-card"><h3>Patnitop Meadows</h3><p>Open grassland at the heart of Patnitop town.</p></div>
      <div class="card place-card"><h3>Naag Temple</h3><p>Local temple site, easily combined with a sightseeing trip.</p></div>
    </div>
    <div class="btn-row"><a href="patnitop-sightseeing.html" class="btn btn-pine">See Full Sightseeing Guide</a></div>
  </div>
</section>

{road_divider()}

<section class="section-pine">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Hotel booking</span>
      <h2>Hotel booking assistance in Patnitop</h2>
    </div>
    <p>Tell us your budget and travel dates and we will help you find a suitable hotel in Patnitop — budget, family or premium — and can combine it with your taxi booking so pickup, stay and sightseeing are arranged together.</p>
    <div class="btn-row">
      <a href="hotel-booking.html" class="btn btn-primary">Hotel Booking Details</a>
      <a href="{wa_href()}" data-whatsapp class="btn btn-outline" target="_blank" rel="noopener">💬 Ask on WhatsApp</a>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Jammu &amp; Kashmir tour packages</span>
      <h2>Wherever you want to travel in Jammu &amp; Kashmir, our team is ready to assist you</h2>
    </div>
    <p>Beyond Patnitop, we provide taxi and travel assistance across Jammu &amp; Kashmir, including Bhaderwah, Srinagar, Gulmarg, Pahalgam, Sonamarg, Doodhpathri and Yusmarg. Exact itinerary and fare depend on your travel dates, chosen vehicle, group size and destination — call or WhatsApp us to plan yours.</p>
    <div class="tag-list">
      <span>Patnitop</span><span>Katra</span><span>Jammu</span><span>Bhaderwah</span><span>Srinagar</span>
      <span>Gulmarg</span><span>Pahalgam</span><span>Sonamarg</span><span>Doodhpathri</span><span>Yusmarg</span>
    </div>
    <div class="btn-row"><a href="tour-packages.html" class="btn btn-pine">Explore Tour Packages</a></div>
  </div>
</section>

<section class="section-alt">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Vehicles</span>
      <h2>Choose a vehicle that fits your group</h2>
    </div>
    <div class="grid grid-4">
      <div class="card vehicle-card"><h3>Dzire</h3><p>Compact sedan for small families, 4 passengers.</p><div class="fare-note">Call / WhatsApp for Current Fare</div></div>
      <div class="card vehicle-card"><h3>Ertiga</h3><p>MPV for 6 passengers with luggage.</p><div class="fare-note">Call / WhatsApp for Current Fare</div></div>
      <div class="card vehicle-card"><h3>Innova / Toyota Crysta</h3><p>Comfortable SUV for mountain routes, 6-7 passengers.</p><div class="fare-note">Call / WhatsApp for Current Fare</div></div>
      <div class="card vehicle-card"><h3>Tempo Traveller</h3><p>For larger groups travelling together.</p><div class="fare-note">Call / WhatsApp for Current Fare</div></div>
    </div>
    <div class="btn-row"><a href="vehicles.html" class="btn btn-pine">Get Best Quote</a></div>
  </div>
</section>

{road_divider()}

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Why choose us</span>
      <h2>What you get when you book with us</h2>
    </div>
    <div class="grid grid-3">
      <div class="card"><h3>Local Patnitop knowledge</h3><p>Based in Patnitop, familiar with routes, weather and road conditions.</p></div>
      <div class="card"><h3>Taxi + sightseeing + hotel</h3><p>One contact for transport, local sightseeing and stay arrangements.</p></div>
      <div class="card"><h3>Airport &amp; railway transfers</h3><p>Pickup from Jammu Airport, Jammu Railway Station and Katra Railway Station.</p></div>
      <div class="card"><h3>Jammu &amp; Kashmir coverage</h3><p>Travel assistance beyond Patnitop, across the wider Kashmir region.</p></div>
      <div class="card"><h3>Personalised trip planning</h3><p>Itinerary shaped around your dates, group size and interests.</p></div>
      <div class="card"><h3>Easy booking</h3><p>Book directly by phone call or WhatsApp message — no app required.</p></div>
    </div>
  </div>
</section>

<section class="section-alt">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Customer reviews</span>
      <h2>What travellers say</h2>
    </div>
    <div class="review-placeholder">
      Genuine customer reviews will appear here once collected from Google Business Profile. If you have travelled with us, we would welcome your review.
    </div>
  </div>
</section>

{faq_block(GLOBAL_FAQS)}

<section class="section-pine">
  <div class="container text-center">
    <h2>Plan your Patnitop trip today</h2>
    <p>Dileep Singh — Patnitop Travels Hub. Call: {PHONE}</p>
    {cta_buttons()}
  </div>
</section>
'''
    schemas = [local_business_schema(), website_schema(), faq_schema(GLOBAL_FAQS)]
    return page(
        "Patnitop Taxi Service &amp; Travel Agency | Patnitop Travels Hub",
        "Patnitop Travels Hub offers taxi service, sightseeing and hotel booking in Patnitop, Jammu & Kashmir. Katra, Jammu, Nathatop, Sanasar & more. Call 9103331334.",
        "index.html", "index.html", body, schema_list=schemas,
        extra_meta='<meta name="google-site-verification" content="LULNs-XkSlabxgey8_J3qHXofnjcPeqAF8OBtkCHO5I" />\n'
    )

write("index.html", build_home())
print("home built")

# ---------------------------------------------------------------
# TAXI SERVICES (hub page)
# ---------------------------------------------------------------

TAXI_SERVICES = [
    ("Katra to Patnitop Taxi", "Pickup from Katra town or Katra Railway Station, direct to Patnitop.", "katra-to-patnitop-taxi.html"),
    ("Jammu to Patnitop Taxi", "Jammu Airport or Jammu Railway Station to Patnitop, one-way or round trip.", "jammu-to-patnitop-taxi.html"),
    ("Airport &amp; Railway Station Transfers", "Jammu Airport, Jammu Railway Station, Katra Railway Station pickup &amp; drop.", "airport-railway-transfer.html"),
    ("Patnitop Sightseeing Taxi", "Local taxi for Nathatop, Sanasar and nearby attractions.", "patnitop-sightseeing.html"),
    ("Nathatop &amp; Sanasar Taxi", "Dedicated taxi service for the Nathatop and Sanasar viewpoints.", "nathatop-sanasar-taxi.html"),
    ("Srinagar Taxi", "Taxi service from Patnitop or Jammu towards Srinagar.", "srinagar-taxi.html"),
    ("Bhaderwah Taxi", "Taxi service to Bhaderwah from Patnitop and Jammu.", "bhaderwah-taxi.html"),
    ("Hotel Pickup &amp; Drop", "Pickup and drop from your Patnitop hotel for onward travel.", "hotel-booking.html"),
]

def build_taxi_services():
    services = TAXI_SERVICES
    cards = ""
    for name, desc, link in services:
        cards += f'<div class="card service-card"><h3>{name}</h3><p>{desc}</p><a class="card-link" href="{link}">Learn more →</a></div>\n'

    taxi_faqs = [qa for qa in GLOBAL_FAQS if "taxi" in qa[0].lower() or "airport" in qa[0].lower() or "tempo" in qa[0].lower()]

    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Patnitop Taxi Service</h1>
    <p>Complete taxi service for tourists in Patnitop and across Jammu &amp; Kashmir — airport transfers, railway station pickup, local sightseeing and outstation trips.</p>
  </div>
</section>
<section>
  <div class="container">
    <div class="section-head">
      <h2>All taxi services offered by Patnitop Travels Hub</h2>
      <p>Every trip is arranged directly with Dileep Singh — call or WhatsApp {PHONE} to check vehicle availability and current fare for your dates.</p>
    </div>
    <div class="grid grid-3">{cards}</div>
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>One-way &amp; round-trip taxi service</h2></div>
    <p>We offer both one-way taxi drop and full round-trip taxi service for Patnitop, Katra, Jammu and onward destinations across Jammu &amp; Kashmir. Family and group transportation, including Tempo Traveller, can be arranged for larger parties.</p>
    {cta_buttons()}
  </div>
</section>
{faq_block(taxi_faqs, "Taxi Service FAQs")}
'''
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("Taxi Services", "taxi-services.html")]), faq_schema(taxi_faqs)]
    return page(
        "Patnitop Taxi Service | Airport, Railway &amp; Sightseeing Taxi",
        "Book taxi service in Patnitop — airport pickup, railway station transfer, local sightseeing and outstation taxi across Jammu & Kashmir. Call 9103331334.",
        "taxi-services.html", "taxi-services.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Taxi Services", "taxi-services.html")],
        schema_list=schemas
    )

write("taxi-services.html", build_taxi_services())

# ---------------------------------------------------------------
# ROUTE / KEYWORD LANDING PAGES (shared template)
# ---------------------------------------------------------------

def build_route_page(path, title, meta_desc, h1, intro_paragraphs, points, faqs, active="taxi-services.html", crumb_name=None, related=None, area_served=None):
    points_html = "".join(f'<li>{p}</li>' for p in points)
    paras = "".join(f'<p>{p}</p>' for p in intro_paragraphs)
    related = related or [("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")]
    related_links = "".join(f' <a href="{p}">{n}</a> ·' for n, p in related).rstrip(" ·")
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>{h1}</h1>
    <p>Call or WhatsApp Dileep Singh at {PHONE} to book.</p>
  </div>
</section>
<section>
  <div class="container">
    {paras}
    <ul>{points_html}</ul>
    {cta_buttons()}
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>Vehicles available</h2></div>
    <p>Dzire, Ertiga, Innova / Toyota Crysta and Tempo Traveller are commonly available for this route, depending on your group size. <a href="vehicles.html">See all vehicles</a> or call/WhatsApp for the current fare.</p>
  </div>
</section>
<section>
  <div class="container">
    <p class="small">You may also want:{related_links}</p>
  </div>
</section>
{faq_block(faqs, "Frequently Asked Questions")}
'''
    crumb = crumb_name or h1
    area_served = area_served or ["Patnitop"]
    schemas = [
        local_business_schema(),
        breadcrumb_schema([("Home", "index.html"), (crumb, path)]),
        faq_schema(faqs),
        service_schema(h1, meta_desc, area_served),
    ]
    return page(
        title, meta_desc, path, active, body,
        breadcrumb_items=[("Home", "index.html"), (crumb, path)],
        schema_list=schemas
    )

ROUTES = [
    dict(
        id="katra",
        path="katra-to-patnitop-taxi.html",
        title="Katra to Patnitop Taxi | Patnitop Travels Hub",
        meta_desc="Book a Katra to Patnitop taxi or Patnitop to Katra taxi with pickup from Katra town or Katra Railway Station. Call 9103331334 for fare and availability.",
        h1="Katra to Patnitop Taxi",
        intro=[
            "Patnitop Travels Hub arranges taxi service between Katra and Patnitop, including pickup from Katra Railway Station and drop directly at your Patnitop hotel.",
            "This route is popular with pilgrims travelling onward from Vaishno Devi towards Patnitop, Nathatop and other hill destinations in Jammu &amp; Kashmir."
        ],
        points=[
            "Katra to Patnitop taxi and Patnitop to Katra taxi, both directions",
            "Pickup available from Katra Railway Station",
            "One-way drop or round-trip taxi service",
            "Hotel pickup and drop in Patnitop included",
            "Family and group transportation, including Tempo Traveller for larger groups",
        ],
        faqs=[
            ("How far is Patnitop from Katra?", "The exact travel time depends on road and weather conditions on the day — call us and we can advise based on current conditions."),
            ("Can you pick us up from Katra Railway Station?", "Yes, we provide Katra Railway Station pickup and drop as part of this route."),
            ("Is a round trip available, or only one-way drop?", "Both one-way taxi drop and full round-trip taxi service are available for Katra to Patnitop."),
        ],
        related=[("Airport & Railway Transfer", "airport-railway-transfer.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Katra", "Patnitop"],
        active="taxi-services.html", crumb_name=None,
        agent_label="Katra to Patnitop",
        agent_default_pickup="Katra town or Katra Railway Station",
        agent_default_drop="Patnitop (your hotel)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="jammu",
        path="jammu-to-patnitop-taxi.html",
        title="Jammu to Patnitop Taxi | Patnitop Travels Hub",
        meta_desc="Book a Jammu to Patnitop taxi or Patnitop to Jammu taxi with Jammu Airport and Railway Station pickup. Call 9103331334 for fare and availability.",
        h1="Jammu to Patnitop Taxi",
        intro=[
            "Patnitop Travels Hub provides taxi service between Jammu and Patnitop, including pickup from Jammu Airport and Jammu Railway Station.",
            "Whether you are arriving by flight or by train, we can arrange your taxi to Patnitop and the return trip to Jammu when your visit ends."
        ],
        points=[
            "Jammu to Patnitop taxi and Patnitop to Jammu taxi, both directions",
            "Jammu Airport pickup and drop",
            "Jammu Railway Station pickup and drop",
            "One-way and round-trip taxi service",
            "Family and group transportation, including Tempo Traveller",
        ],
        faqs=[
            ("Do you provide Jammu Airport pickup for Patnitop?", "Yes, we offer Jammu Airport pickup and drop with onward taxi service to Patnitop."),
            ("Do you provide Jammu Railway Station pickup?", "Yes, Jammu Railway Station pickup and drop is available as part of this route."),
            ("Can I book a one-way taxi from Jammu to Patnitop?", "Yes, one-way taxi drop is available, along with full round-trip service if you need a return journey."),
        ],
        related=[("Airport & Railway Transfer", "airport-railway-transfer.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Jammu", "Patnitop"],
        active="taxi-services.html", crumb_name=None,
        agent_label="Jammu to Patnitop",
        agent_default_pickup="Jammu (Airport / Railway Station / city)",
        agent_default_drop="Patnitop (your hotel)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="airport-railway",
        path="airport-railway-transfer.html",
        title="Jammu Airport to Patnitop Taxi | Railway Station Transfer | Patnitop Travels Hub",
        meta_desc="Jammu Airport to Patnitop taxi and Jammu Railway Station to Patnitop taxi, plus Katra Railway Station pickup. Call 9103331334.",
        h1="Airport &amp; Railway Station Pickup and Drop",
        intro=[
            "Patnitop Travels Hub provides taxi pickup and drop at Jammu Airport, Jammu Railway Station and Katra Railway Station, with onward transfer to Patnitop, Katra or other Jammu &amp; Kashmir destinations.",
            "Share your flight or train details when booking so your taxi can be arranged around your arrival or departure time."
        ],
        points=[
            "Jammu Airport pickup and drop",
            "Jammu Railway Station pickup and drop",
            "Katra Railway Station pickup and drop",
            "Onward transfer to Patnitop, Katra, or other J&amp;K destinations",
            "Hotel pickup and drop also available",
        ],
        faqs=[
            ("Which airport and railway stations do you cover?", "We cover Jammu Airport, Jammu Railway Station and Katra Railway Station, with onward taxi transfer to Patnitop and nearby destinations."),
            ("Should I share my flight or train number?", "Yes, sharing your flight or train details and expected arrival time helps us plan your pickup accurately."),
        ],
        crumb_name="Airport &amp; Railway Transfer",
        related=[("Katra to Patnitop Taxi", "katra-to-patnitop-taxi.html"), ("Jammu to Patnitop Taxi", "jammu-to-patnitop-taxi.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Jammu", "Katra", "Patnitop"],
        active="taxi-services.html",
        agent_label="Airport / Railway Station Transfer",
        agent_default_pickup="Jammu Airport / Jammu Railway Station / Katra Railway Station",
        agent_default_drop="Patnitop or your onward destination",
        agent_ask_sightseeing=False, agent_ask_hotel=True,
    ),
    dict(
        id="nathatop-sanasar",
        path="nathatop-sanasar-taxi.html",
        title="Nathatop &amp; Sanasar Taxi Service | Patnitop Travels Hub",
        meta_desc="Book a taxi from Patnitop to Nathatop and Sanasar for sightseeing. Call or WhatsApp 9103331334 for current fare and availability.",
        h1="Nathatop &amp; Sanasar Taxi",
        intro=[
            "Nathatop and Sanasar are two of the most visited viewpoints near Patnitop, and Patnitop Travels Hub arranges local taxi service to both.",
            "These trips can be booked as a half-day or full-day sightseeing taxi, and combined with other nearby attractions on request."
        ],
        points=[
            "Taxi service to Nathatop viewpoint",
            "Taxi service to Sanasar meadow",
            "Half-day and full-day sightseeing options",
            "Can be combined with other local Patnitop attractions",
        ],
        faqs=[
            ("Can Nathatop and Sanasar be covered in one day?", "Depending on your schedule and road conditions on the day, both can often be combined — call us and we will help plan the timing."),
            ("Do you provide a driver-guide for sightseeing?", "Our drivers are familiar with these local routes; for detailed historical or cultural guiding, let us know in advance so we can advise what is available."),
        ],
        active="patnitop-sightseeing.html",
        crumb_name="Nathatop &amp; Sanasar Taxi",
        related=[("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Katra to Patnitop Taxi", "katra-to-patnitop-taxi.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Nathatop", "Sanasar", "Patnitop"],
        agent_label="Nathatop & Sanasar Sightseeing",
        agent_default_pickup="Your Patnitop hotel",
        agent_default_drop="Nathatop & Sanasar (return to Patnitop)",
        agent_ask_sightseeing=False, agent_ask_hotel=False,
    ),
    dict(
        id="srinagar",
        path="srinagar-taxi.html",
        title="Srinagar Taxi Service from Patnitop &amp; Jammu | Patnitop Travels Hub",
        meta_desc="Book a taxi to Srinagar from Patnitop or Jammu. Outstation taxi across Jammu & Kashmir. Call 9103331334 for fare and availability.",
        h1="Srinagar Taxi Service",
        intro=[
            "Patnitop Travels Hub can arrange outstation taxi service to Srinagar from Patnitop or Jammu, as part of a wider Jammu &amp; Kashmir trip.",
            "Availability and route timing depend on season and road conditions, so please call ahead to plan your Srinagar leg."
        ],
        points=[
            "Taxi from Patnitop to Srinagar",
            "Taxi from Jammu to Srinagar",
            "Can be combined with Gulmarg, Pahalgam and Sonamarg on a wider itinerary",
            "One-way and round-trip options",
        ],
        faqs=[
            ("Do you provide taxi service all the way to Srinagar?", "Yes, subject to availability, we can arrange taxi service to Srinagar from Patnitop or Jammu."),
            ("Can this be combined with Gulmarg or Pahalgam?", "Yes, this can be arranged as part of a wider Jammu &amp; Kashmir tour — see our tour packages page for more."),
        ],
        crumb_name="Srinagar Taxi",
        related=[("J&K Tour Packages", "tour-packages.html"), ("Bhaderwah Taxi", "bhaderwah-taxi.html"), ("Vehicles", "vehicles.html")],
        area_served=["Srinagar", "Patnitop", "Jammu"],
        active="taxi-services.html",
        agent_label="Srinagar Taxi",
        agent_default_pickup="Patnitop or Jammu",
        agent_default_drop="Srinagar",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="bhaderwah",
        path="bhaderwah-taxi.html",
        title="Bhaderwah Taxi Service | Patnitop Travels Hub",
        meta_desc="Book a taxi to Bhaderwah from Patnitop or Jammu with Patnitop Travels Hub. Call 9103331334 for fare and availability.",
        h1="Bhaderwah Taxi Service",
        intro=[
            "Patnitop Travels Hub arranges taxi service to Bhaderwah, known as \"Mini Kashmir\", from Patnitop and Jammu.",
            "This can be booked as a standalone trip or combined with your wider Jammu &amp; Kashmir travel plans."
        ],
        points=[
            "Taxi from Patnitop to Bhaderwah",
            "Taxi from Jammu to Bhaderwah",
            "One-way and round-trip taxi service",
            "Family and group transportation available",
        ],
        faqs=[
            ("How do I book a Bhaderwah taxi?", "Call or WhatsApp 9103331334, or use the booking form on this website with your travel dates."),
            ("Can I combine Bhaderwah with a Patnitop trip?", "Yes, this route is often combined with a Patnitop or wider Jammu &amp; Kashmir itinerary — call us to plan it."),
        ],
        crumb_name="Bhaderwah Taxi",
        related=[("J&K Tour Packages", "tour-packages.html"), ("Srinagar Taxi", "srinagar-taxi.html"), ("Vehicles", "vehicles.html")],
        area_served=["Bhaderwah", "Patnitop", "Jammu"],
        active="taxi-services.html",
        agent_label="Bhaderwah Taxi",
        agent_default_pickup="Patnitop or Jammu",
        agent_default_drop="Bhaderwah",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
]

for r in ROUTES:
    write(r["path"], build_route_page(
        r["path"], r["title"], r["meta_desc"], r["h1"],
        r["intro"], r["points"], r["faqs"],
        active=r["active"], crumb_name=r["crumb_name"],
        related=r["related"], area_served=r["area_served"],
    ))

print("route pages built")

# ---------------------------------------------------------------
# SIGHTSEEING
# ---------------------------------------------------------------

SIGHTSEEING_PLACES = [
    ("Nathatop", "A panoramic viewpoint above Patnitop, popular for mountain views."),
    ("Sanasar", "A bowl-shaped meadow valley, a short taxi ride from Patnitop."),
    ("Patnitop Meadows", "The open grassland at the centre of Patnitop town."),
    ("Naag Temple", "A local temple site near Patnitop."),
    ("Padora Park", "A local park area in the Patnitop region."),
    ("Children Park", "A family-friendly park in Patnitop."),
    ("Shiv Temple", "A local temple, easily combined with other nearby stops."),
]

def build_sightseeing():
    places = SIGHTSEEING_PLACES
    cards = "".join(f'<div class="card place-card"><h3>{n}</h3><p>{d}</p></div>' for n, d in places)
    sightseeing_faqs = [GLOBAL_FAQS[4], GLOBAL_FAQS[5]]
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Patnitop Sightseeing Taxi</h1>
    <p>Local sightseeing taxi covering Patnitop, Nathatop, Sanasar and nearby attractions.</p>
  </div>
</section>
<section>
  <div class="container">
    <p>Patnitop Travels Hub arranges a local sightseeing taxi so you can visit the main attractions around Patnitop without arranging separate transport for each stop. Exact stops, timing and route can be adjusted to your interests and the time you have available.</p>
    <div class="grid grid-4">{cards}</div>
    <p class="small">Note: opening hours, entry fees and exact attraction availability can change — please confirm current details with us or on-site when you visit.</p>
    {cta_buttons()}
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>Combine sightseeing with your taxi route</h2></div>
    <p>Sightseeing can be added on to a <a href="katra-to-patnitop-taxi.html">Katra to Patnitop taxi</a>, <a href="jammu-to-patnitop-taxi.html">Jammu to Patnitop taxi</a>, or arranged as a standalone half-day or full-day local taxi hire. <a href="nathatop-sanasar-taxi.html">See Nathatop &amp; Sanasar taxi details</a>.</p>
  </div>
</section>
{faq_block(sightseeing_faqs, "Sightseeing FAQs")}
'''
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("Sightseeing", "patnitop-sightseeing.html")]), faq_schema(sightseeing_faqs)]
    return page(
        "Patnitop Sightseeing Taxi | Nathatop, Sanasar &amp; Local Attractions",
        "Book a Patnitop sightseeing taxi covering Nathatop, Sanasar, Patnitop Meadows and nearby attractions. Call 9103331334 to book.",
        "patnitop-sightseeing.html", "patnitop-sightseeing.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Sightseeing", "patnitop-sightseeing.html")],
        schema_list=schemas
    )

write("patnitop-sightseeing.html", build_sightseeing())

# ---------------------------------------------------------------
# HOTEL BOOKING
# ---------------------------------------------------------------

HOTEL_CATEGORIES = [
    ("Budget Hotels", "Simple, comfortable stays for cost-conscious travellers."),
    ("Family Hotels", "Rooms and layouts suited to families travelling together."),
    ("Premium Hotels", "Higher-comfort stays for a more relaxed trip."),
]

def build_hotel_booking():
    hotel_cards = "\n      ".join(f'<div class="card"><h3>{n}</h3><p>{d}</p></div>' for n, d in HOTEL_CATEGORIES)
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Patnitop Hotel Booking</h1>
    <p>Hotel booking assistance in Patnitop across budget, family and premium categories.</p>
  </div>
</section>
<section>
  <div class="container">
    <p>Patnitop Travels Hub helps tourists book hotels in Patnitop according to their budget and requirements. Tell us your travel dates, group size and budget range, and we will help you find a suitable option.</p>
    <div class="grid grid-3">
      {hotel_cards}
    </div>
    <p style="margin-top:20px;">Couple-friendly accommodation can be arranged where legally and practically applicable — please mention this when enquiring so we can check current availability.</p>
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>Hotel + Taxi Packages</h2></div>
    <p>We can combine your hotel booking with taxi pickup, drop and local sightseeing, so transport and stay are arranged through a single point of contact.</p>
    {cta_buttons()}
  </div>
</section>
<section>
  <div class="container">
    <div class="booking-panel">
      <h2 class="mt-0">Hotel Booking Enquiry</h2>
      <p class="small">Prefer to fill a form? Use the full booking form on our <a href="contact.html#booking-form">Contact page</a> — mention "Hotel Required: Yes" and your budget in the message field.</p>
      {cta_buttons()}
    </div>
  </div>
</section>
{faq_block([GLOBAL_FAQS[3]], "Hotel Booking FAQ")}
'''
    hotel_faqs = [GLOBAL_FAQS[3]]
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("Hotel Booking", "hotel-booking.html")]), faq_schema(hotel_faqs)]
    return page(
        "Patnitop Hotel Booking | Budget, Family &amp; Premium Hotels",
        "Hotel booking assistance in Patnitop — budget, family and premium hotels, with optional hotel + taxi packages. Call 9103331334.",
        "hotel-booking.html", "hotel-booking.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Hotel Booking", "hotel-booking.html")],
        schema_list=schemas
    )

write("hotel-booking.html", build_hotel_booking())

# ---------------------------------------------------------------
# TOUR PACKAGES
# ---------------------------------------------------------------

PACKAGE_DESTINATIONS = [
    ("Patnitop", None),
    ("Katra", "katra-to-patnitop-taxi.html"),
    ("Jammu", "jammu-to-patnitop-taxi.html"),
    ("Bhaderwah", "bhaderwah-taxi.html"),
    ("Srinagar", "srinagar-taxi.html"),
    ("Gulmarg", None),
    ("Pahalgam", None),
    ("Sonamarg", None),
    ("Doodhpathri", None),
    ("Yusmarg", None),
]

def build_packages():
    # dest -> (label, linked page or None if no dedicated page exists)
    dests = PACKAGE_DESTINATIONS
    tags = "".join(
        f'<span><a href="{link}">{d}</a></span>' if link else f'<span>{d}</span>'
        for d, link in dests
    )
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Jammu &amp; Kashmir Tour Packages</h1>
    <p>Wherever you want to travel in Jammu &amp; Kashmir, our team is ready to assist you.</p>
  </div>
</section>
<section>
  <div class="container">
    <p>Patnitop Travels Hub arranges travel across Jammu &amp; Kashmir, covering the destinations below and other tourist spots on request. The exact itinerary, number of days and pricing depend on your travel dates, choice of vehicle, group size and destination — call or WhatsApp us to plan a route that fits your trip.</p>
    <div class="tag-list">{tags}</div>
    {cta_buttons()}
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>How a package is planned</h2></div>
    <p>Share your number of travel days, preferred destinations, group size and rough budget with us on call or WhatsApp. We will suggest a route and vehicle, and confirm current availability and fare before you travel.</p>
  </div>
</section>
'''
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("J&K Tour Packages", "tour-packages.html")])]
    return page(
        "Jammu &amp; Kashmir Taxi &amp; Tour Packages | Patnitop Travels Hub",
        "Taxi and tour services across Jammu & Kashmir — Patnitop, Katra, Jammu, Bhaderwah, Srinagar, Gulmarg, Pahalgam, Sonamarg and more. Call 9103331334.",
        "tour-packages.html", "tour-packages.html", body,
        breadcrumb_items=[("Home", "index.html"), ("J&K Tour Packages", "tour-packages.html")],
        schema_list=schemas
    )

write("tour-packages.html", build_packages())

# ---------------------------------------------------------------
# VEHICLES
# ---------------------------------------------------------------

VEHICLES = [
    ("Dzire", "Compact sedan, suited to small families of up to 4 passengers with regular luggage."),
    ("Ertiga", "MPV with more space, suited to 6 passengers with luggage."),
    ("Innova / Toyota Crysta", "Comfortable SUV, a common choice for mountain routes, 6-7 passengers."),
    ("Tempo Traveller", "Larger vehicle for groups and bigger families travelling together."),
]

def build_vehicles():
    vehicles = VEHICLES
    cards = "".join(f'<div class="card vehicle-card"><h3>{n}</h3><p>{d}</p><div class="fare-note">Get Best Quote — Call / WhatsApp for Current Fare</div></div>' for n, d in vehicles)
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Vehicles Available</h1>
    <p>Choose a vehicle based on your group size and route — call or WhatsApp for the current fare.</p>
  </div>
</section>
<section>
  <div class="container">
    <div class="section-head"><h2>Choose your vehicle</h2></div>
    <div class="grid grid-4">{cards}</div>
    <p class="small" style="margin-top:20px;">Fares depend on route, distance, season and vehicle availability, so we do not publish fixed prices online. Call or WhatsApp {PHONE} and we will confirm the current fare for your exact trip.</p>
    {cta_buttons()}
  </div>
</section>
'''
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("Vehicles", "vehicles.html")])]
    return page(
        "Vehicles for Taxi Hire in Patnitop | Dzire, Ertiga, Innova, Tempo Traveller",
        "Choose from Dzire, Ertiga, Innova/Toyota Crysta or Tempo Traveller for your Patnitop taxi. Call or WhatsApp 9103331334 for current fare.",
        "vehicles.html", "vehicles.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Vehicles", "vehicles.html")],
        schema_list=schemas
    )

write("vehicles.html", build_vehicles())

# ---------------------------------------------------------------
# FAQ PAGE
# ---------------------------------------------------------------

def build_faq():
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Frequently Asked Questions</h1>
    <p>Answers to common questions about taxi booking, hotels and sightseeing with Patnitop Travels Hub.</p>
  </div>
</section>
{faq_block(GLOBAL_FAQS, "All Questions")}
<section class="section-alt">
  <div class="container text-center">
    <h2>Still have a question?</h2>
    {cta_buttons()}
  </div>
</section>
'''
    schemas = [local_business_schema(), faq_schema(GLOBAL_FAQS), breadcrumb_schema([("Home", "index.html"), ("FAQ", "faq.html")])]
    return page(
        "FAQ — Patnitop Taxi, Hotel &amp; Sightseeing Questions",
        "Frequently asked questions about Patnitop taxi booking, Katra & Jammu transfers, hotel booking and sightseeing with Patnitop Travels Hub.",
        "faq.html", "faq.html", body,
        breadcrumb_items=[("Home", "index.html"), ("FAQ", "faq.html")],
        schema_list=schemas
    )

write("faq.html", build_faq())

# ---------------------------------------------------------------
# CONTACT + BOOKING FORM
# ---------------------------------------------------------------

def build_contact():
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Contact &amp; Book</h1>
    <p>Dileep Singh — Patnitop Travels Hub. Call: {PHONE}</p>
  </div>
</section>
<section>
  <div class="container">
    <div class="grid grid-2" style="align-items:start;">
      <div>
        <h2 class="mt-0">Get in touch</h2>
        <p><strong>Patnitop Travels Hub</strong><br>Dileep Singh<br>Patnitop, Jammu &amp; Kashmir, India</p>
        <p>
          📞 <a href="tel:+91{PHONE}">{PHONE}</a><br>
          📞 <a href="tel:+91{PHONE2}">{PHONE2}</a><br>
          ✉️ <a href="mailto:{EMAIL}">{EMAIL}</a><br>
          ✉️ <a href="mailto:patnitoptravelshub@gmail.com">patnitoptravelshub@gmail.com</a>
        </p>
        {cta_buttons()}
        <div style="margin-top:28px; border:1px solid var(--line); aspect-ratio:4/3; overflow:hidden;">
          <iframe title="Patnitop location map" src="https://www.google.com/maps?q=Patnitop,Jammu+and+Kashmir&output=embed" width="100%" height="100%" style="border:0;" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
      </div>
      <div class="booking-panel" id="booking-form">
        <h2 class="mt-0">Booking / Enquiry Form</h2>
        <form id="enquiry-form">
          <div class="form-grid">
            <div><label for="name">Name</label><input id="name" name="name" required></div>
            <div><label for="mobile">Mobile Number</label><input id="mobile" name="mobile" type="tel" required></div>
            <div><label for="pickup">Pickup Location</label><input id="pickup" name="pickup" required></div>
            <div><label for="drop">Drop Location</label><input id="drop" name="drop" required></div>
            <div><label for="travel_date">Travel Date</label><input id="travel_date" name="travel_date" type="date" required></div>
            <div><label for="return_date">Return Date (optional)</label><input id="return_date" name="return_date" type="date"></div>
            <div><label for="passengers">Number of Passengers</label><input id="passengers" name="passengers" type="number" min="1" required></div>
            <div>
              <label for="vehicle">Vehicle Required</label>
              <select id="vehicle" name="vehicle">
                <option>Dzire</option><option>Ertiga</option><option>Innova / Toyota Crysta</option><option>Tempo Traveller</option><option>Not sure — please suggest</option>
              </select>
            </div>
            <div class="full">
              <label>Hotel Required?</label>
              <div class="radio-row">
                <label><input type="radio" name="hotel_required" value="Yes" checked> Yes</label>
                <label><input type="radio" name="hotel_required" value="No"> No</label>
              </div>
            </div>
            <div class="full">
              <label>Sightseeing Required?</label>
              <div class="radio-row">
                <label><input type="radio" name="sightseeing_required" value="Yes" checked> Yes</label>
                <label><input type="radio" name="sightseeing_required" value="No"> No</label>
              </div>
            </div>
            <div class="full"><label for="message">Message</label><textarea id="message" name="message" rows="3"></textarea></div>
          </div>
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:20px;">Submit Enquiry</button>
          <p class="form-note">Submitting prepares a WhatsApp message with your details — you send it to us with one tap, or call {PHONE} directly.</p>
        </form>
        <div class="form-success" id="form-success"></div>
      </div>
    </div>
  </div>
</section>
'''
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("Contact", "contact.html")])]
    return page(
        "Contact Patnitop Travels Hub | Book a Taxi or Hotel",
        "Contact Dileep Singh at Patnitop Travels Hub — call 9103331334 or 8493988568, WhatsApp, or fill the booking form for taxi and hotel enquiries.",
        "contact.html", "contact.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Contact", "contact.html")],
        schema_list=schemas
    )

write("contact.html", build_contact())

# ---------------------------------------------------------------
# AI AGENT KNOWLEDGE SOURCE
# Generated entirely from the constants above (GLOBAL_FAQS, ROUTES,
# TAXI_SERVICES, SIGHTSEEING_PLACES, HOTEL_CATEGORIES, VEHICLES,
# PACKAGE_DESTINATIONS) — nothing here is hand-typed business content;
# it is the same data already used to build the HTML pages, so the
# widget and the pages can never drift out of sync.
# ---------------------------------------------------------------

def build_agent_data():
    import json as _json

    routes_out = []
    for r in ROUTES:
        routes_out.append({
            "id": r["id"],
            "label": r["agent_label"],
            "path": r["path"],
            "summary": re.sub("<[^>]+>", "", r["intro"][0]).replace("&amp;", "&"),
            "defaultPickup": r["agent_default_pickup"],
            "defaultDrop": r["agent_default_drop"],
            "askSightseeing": r["agent_ask_sightseeing"],
            "askHotel": r["agent_ask_hotel"],
            "faqs": [{"q": q, "a": re.sub("<[^>]+>", "", a).replace("&amp;", "&")} for q, a in r["faqs"]],
        })

    data = {
        "whatsappNumber": WA_NUMBER,
        "phone": PHONE,
        "phone2": PHONE2,
        "businessName": "Patnitop Travels Hub",
        "routes": routes_out,
        "taxiServices": [{"name": re.sub("<[^>]+>", "", n).replace("&amp;", "&"), "desc": d} for n, d, _ in TAXI_SERVICES],
        "sightseeing": [{"name": n, "desc": d} for n, d in SIGHTSEEING_PLACES],
        "hotelCategories": [{"name": n, "desc": d} for n, d in HOTEL_CATEGORIES],
        "vehicles": [{"name": n, "desc": d} for n, d in VEHICLES],
        "packageDestinations": [d for d, _ in PACKAGE_DESTINATIONS],
        "faqs": [{"q": q, "a": re.sub("<[^>]+>", "", a).replace("&amp;", "&")} for q, a in GLOBAL_FAQS],
    }

    js = "// AUTO-GENERATED by build.py from GLOBAL_FAQS / ROUTES / TAXI_SERVICES /\n"
    js += "// SIGHTSEEING_PLACES / HOTEL_CATEGORIES / VEHICLES / PACKAGE_DESTINATIONS.\n"
    js += "// Do not hand-edit — edit the source lists in build.py and re-run it.\n"
    js += "var AGENT_DATA = " + _json.dumps(data, indent=2) + ";\n"

    with open(os.path.join(ROOT, "js", "agent-data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print("wrote js/agent-data.js")

build_agent_data()

print("ALL PAGES BUILT")

