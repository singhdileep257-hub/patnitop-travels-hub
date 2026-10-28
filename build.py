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
import json
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------
# Site configuration — values live in site.config.json (committed),
# and can be overridden by environment variables of the same name in
# upper case (SITE_URL, GA4_MEASUREMENT_ID, LEAD_ENDPOINT).
#   site_url            canonical base URL. Keep it on the Netlify URL until
#                       www.patnitoptravelshub.com actually points at the site.
#   ga4_measurement_id  e.g. G-XXXXXXXXXX. Empty = no analytics script loaded.
#   lead_endpoint       Google Apps Script web-app URL (see docs/SETUP.md).
#                       Empty = enquiries go to WhatsApp only (no storage).
# ---------------------------------------------------------------
def _load_config():
    cfg = {}
    path = os.path.join(ROOT, "site.config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    cfg["site_url"] = os.environ.get("SITE_URL", cfg.get("site_url", "")).rstrip("/")
    cfg["ga4_measurement_id"] = os.environ.get("GA4_MEASUREMENT_ID", cfg.get("ga4_measurement_id", "")).strip()
    cfg["lead_endpoint"] = os.environ.get("LEAD_ENDPOINT", cfg.get("lead_endpoint", "")).strip()
    cfg["indexable_products_page"] = bool(cfg.get("indexable_products_page", False))
    for key in ("gbp_maps_url", "gbp_review_url"):
        cfg[key] = os.environ.get(key.upper(), cfg.get(key, "")).strip()
        if cfg[key] and not cfg[key].startswith("https://"):
            raise SystemExit(f"{key} must be an https:// link (copy it from your Google Business Profile)")
    if not re.match(r"^https?://[^/\s]+$", cfg["site_url"]):
        raise SystemExit("site_url in site.config.json must look like https://example.com (no trailing path)")
    if cfg["ga4_measurement_id"] and not re.match(r"^G-[A-Z0-9]{6,14}$", cfg["ga4_measurement_id"]):
        raise SystemExit("ga4_measurement_id must look like G-XXXXXXXXXX")
    if cfg["lead_endpoint"] and not cfg["lead_endpoint"].startswith("https://"):
        raise SystemExit("lead_endpoint must be an https:// URL")
    return cfg

CONFIG = _load_config()
SITE_URL = CONFIG["site_url"]
GA4_ID = CONFIG["ga4_measurement_id"]
LEAD_ENDPOINT = CONFIG["lead_endpoint"]
GBP_MAPS_URL = CONFIG["gbp_maps_url"]      # your real Google Maps / Business Profile link (empty until it exists)
GBP_REVIEW_URL = CONFIG["gbp_review_url"]  # your real "write a review" link (empty until it exists)
PHONE = "9103331334"
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

PHOTO_PATH = "couple-photoshoot-srinagar-patnitop.html"

NAV_ITEMS = [
    ("index.html", "Home"),
    ("taxi-services.html", "Taxi Services"),
    ("patnitop-sightseeing.html", "Sightseeing"),
    (PHOTO_PATH, "Photography"),
    ("hotel-booking.html", "Hotels"),
    ("tour-packages.html", "J&K Packages"),
    ("vehicles.html", "Vehicles"),
    ("faq.html", "FAQ"),
    ("contact.html", "Contact"),
]

# Couple photoshoots, reels & pre-wedding service (Srinagar and Patnitop). The WhatsApp text is a
# fill-in-the-blanks template, so the button works with no JavaScript and the customer can
# state every detail we need for a customised quotation. No prices, availability or package
# inclusions are written anywhere on the site.
PHOTO_WA_MSG = (
    "Hello Patnitop Travels Hub, I would like a quotation for a couple shoot / reels in Srinagar or Patnitop.\n"
    "Name:\n"
    "Shoot type (couple / pre-wedding / reels / other):\n"
    "Shoot date:\n"
    "Location (Srinagar / Patnitop / both):\n"
    "Duration preference (short / half day / full day):\n"
    "Photos, reels or both:\n"
    "Need a taxi as well (yes / no):"
)

def road_divider():
    return '''<svg class="road-divider" viewBox="0 0 1180 34" preserveAspectRatio="none" aria-hidden="true">
<path d="M0 20 Q 150 4, 300 20 T 600 20 T 900 20 T 1180 20"/>
</svg>'''

def mountain_art():
    # Original, decorative mountain silhouette (no photo, nothing copied).
    return '''<svg class="photo-art" viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true" focusable="false">
<path d="M0 120 L0 78 L130 38 L240 70 L380 20 L520 74 L660 34 L800 80 L940 28 L1070 66 L1200 40 L1200 120 Z" fill="rgba(247,245,239,0.10)"/>
<path d="M0 120 L0 96 L160 62 L300 92 L450 52 L600 94 L760 58 L900 96 L1050 64 L1200 90 L1200 120 Z" fill="#F7F5EF"/>
</svg>'''

def photo_band():
    # Homepage promo for the couple-shoot service. Real working WhatsApp link
    # built at build time; the other two buttons go to the dedicated page.
    return f'''<section class="photo-band" aria-labelledby="photo-band-title">
  <div class="container">
    <span class="eyebrow-plain">Srinagar · Patnitop · Kashmir</span>
    <h2 id="photo-band-title">Capture Your Love in Kashmir</h2>
    <p>Explore the beauty of Kashmir with professional couple photoshoots, cinematic Instagram Reels and pre-wedding photography in Srinagar and Patnitop. Choose beautiful locations, create memorable videos and combine your shoot with a convenient taxi or sightseeing package.</p>
    <div class="tag-list photo-tags"><span>Couple shoots in Srinagar</span><span>Pre-wedding in Srinagar &amp; Patnitop</span><span>Cinematic Reels</span><span>Taxi + sightseeing add-on</span></div>
    <div class="btn-row">
      <a href="{PHOTO_PATH}#enquiry" class="btn btn-primary">📸 Book a Couple Shoot</a>
      <a href="{wa_href(PHOTO_WA_MSG)}" class="btn btn-whatsapp" target="_blank" rel="noopener">💬 Get a Quote on WhatsApp</a>
      <a href="{PHOTO_PATH}#locations" class="btn btn-outline">Explore Shoot Locations</a>
    </div>
  </div>
  {mountain_art()}
</section>'''

def head(title, description, canonical_path, extra_schema="", extra_meta="", robots="index, follow"):
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
<meta name="robots" content="{robots}">
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
    "postalCode": "182142",
    "addressCountry": "IN"
  }},
  "geo": {{
    "@type": "GeoCoordinates",
    "latitude": 33.0903,
    "longitude": 75.3264
  }},
  "areaServed": ["Patnitop", "Kud", "Chenani", "Udhampur", "Katra", "Jammu", "Nathatop", "Sanasar", "Bhaderwah", "Srinagar", "Gulmarg", "Pahalgam", "Sonamarg"],
  "founder": {{ "@type": "Person", "name": "Dileep Singh" }},
  "sameAs": {json.dumps([GBP_MAPS_URL] if GBP_MAPS_URL else [])}{(',' + chr(10) + '  "hasMap": ' + json.dumps(GBP_MAPS_URL)) if GBP_MAPS_URL else ''}
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

def analytics_snippet():
    # Loaded only when a GA4 measurement ID is set in site.config.json.
    # With no ID, no third-party analytics script is requested at all;
    # js/tracking.js still queues events in window.dataLayer harmlessly.
    if not GA4_ID:
        return ""
    return (
        '<script async src="https://www.googletagmanager.com/gtag/js?id=' + GA4_ID + '"></script>\n'
        '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
        "gtag('js',new Date());gtag('config','" + GA4_ID + "');</script>\n"
    )

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
          <li><a href="{PHOTO_PATH}">Couple Photoshoots &amp; Reels</a></li>
          <li><a href="things-to-do-in-patnitop.html">Things to Do in Patnitop</a></li>
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
          <li><a href="udhampur-to-patnitop-taxi.html">Udhampur to Patnitop Taxi</a></li>
          <li><a href="chenani-to-patnitop-taxi.html">Chenani to Patnitop Taxi</a></li>
          <li><a href="kudh-to-patnitop-taxi.html">Kud to Patnitop Taxi</a></li>
          <li><a href="nathatop-sanasar-taxi.html">Nathatop &amp; Sanasar Taxi</a></li>
          <li><a href="srinagar-taxi.html">Srinagar Taxi</a></li>
          <li><a href="gulmarg-taxi.html">Gulmarg Taxi</a></li>
          <li><a href="pahalgam-taxi.html">Pahalgam Taxi</a></li>
          <li><a href="sonamarg-taxi.html">Sonamarg Taxi</a></li>
          <li><a href="doodhpathri-taxi.html">Doodhpathri Taxi</a></li>
          <li><a href="yusmarg-taxi.html">Yusmarg Taxi</a></li>
          <li><a href="bhaderwah-taxi.html">Bhaderwah Taxi</a></li>
          <li><a href="sudh-mahadev-taxi.html">Sudh Mahadev Taxi</a></li>
          <li><a href="mantalai-taxi.html">Mantalai Taxi</a></li>
          <li><a href="gauri-kund-taxi.html">Gauri Kund Taxi</a></li>
          <li><a href="airport-railway-transfer.html">Airport &amp; Railway Transfer</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact</h4>
        <ul>
          <li>Dileep Singh</li>
          <li><a href="tel:+91{PHONE}">{PHONE}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li>Patnitop, Jammu &amp; Kashmir, India</li>{(f'{chr(10)}          <li><a href="{GBP_MAPS_URL}" target="_blank" rel="noopener">📍 Find us on Google Maps</a></li>') if GBP_MAPS_URL else ''}
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> Patnitop Travels Hub. All rights reserved. · <a href="privacy.html">Privacy</a></span>
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
{analytics_snippet()}<script src="js/tracking.js"></script>
<script src="js/script.js"></script>
<script src="js/agent-data.js"></script>
<script src="js/agent.js"></script>
</body>
</html>'''

def page(title, description, path, active_nav, body_html, breadcrumb_items=None, extra_schema="", schema_list=None, extra_meta="", robots="index, follow"):
    schemas = extra_schema
    if schema_list:
        schemas = "\n".join(schema_list)
    html = head(title, description, path, schemas, extra_meta, robots)
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

def cta_buttons(context="general", wa_message=None):
    import html as _h
    wa_attr = f' data-wa-message="{_h.escape(wa_message, quote=True)}"' if wa_message else ""
    return f'''<div class="btn-row">
  <a href="tel:+91{PHONE}" class="btn btn-pine">📞 Call Now</a>
  <a href="{wa_href(wa_message)}" data-whatsapp{wa_attr} class="btn btn-whatsapp" target="_blank" rel="noopener">💬 WhatsApp Now</a>
  <a href="contact.html#booking-form" class="btn btn-primary">🚕 Book a Taxi</a>
</div>'''

def google_links_html():
    # Shown only once the real Business Profile links are set in site.config.json.
    parts = []
    if GBP_MAPS_URL:
        parts.append(f'<a href="{GBP_MAPS_URL}" class="btn btn-outline" target="_blank" rel="noopener">📍 View on Google Maps</a>')
    if GBP_REVIEW_URL:
        parts.append(f'<a href="{GBP_REVIEW_URL}" class="btn btn-outline" target="_blank" rel="noopener">⭐ Review us on Google</a>')
    return ('<div class="btn-row">' + "".join(parts) + '</div>') if parts else ""

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
    ("How can I contact Dileep Singh?", "You can call or WhatsApp Dileep Singh at 9103331334 or email singhdileep257@gmail.com."),
]

# ---------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------

def build_home():
    body = f'''
<section class="hero">
  <div class="container">
    <span class="eyebrow-plain">Patnitop · Katra · Jammu · Kashmir</span>
    <h1>Patnitop Taxi Service &amp; Travel Partner in Jammu &amp; Kashmir</h1>
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
    <p class="small">Popular pickup points for Patnitop: <a href="katra-to-patnitop-taxi.html">Katra</a> · <a href="jammu-to-patnitop-taxi.html">Jammu</a> · <a href="udhampur-to-patnitop-taxi.html">Udhampur</a> · <a href="chenani-to-patnitop-taxi.html">Chenani</a> · <a href="kudh-to-patnitop-taxi.html">Kud</a></p>
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
    <div class="btn-row"><a href="patnitop-sightseeing.html" class="btn btn-pine">See Full Sightseeing Guide</a> <a href="things-to-do-in-patnitop.html" class="btn btn-outline">Things to Do in Patnitop</a></div>
  </div>
</section>

{photo_band()}

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
      <span><a href="gulmarg-taxi.html">Gulmarg</a></span><span><a href="pahalgam-taxi.html">Pahalgam</a></span><span><a href="sonamarg-taxi.html">Sonamarg</a></span><span><a href="doodhpathri-taxi.html">Doodhpathri</a></span><span><a href="yusmarg-taxi.html">Yusmarg</a></span>
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
        "Taxi service in Patnitop, Kud, Chenani, Udhampur, Katra and Jammu, plus sightseeing and hotel booking help. Call or WhatsApp Patnitop Travels Hub on 9103331334.",
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
    ("Udhampur to Patnitop Taxi", "Taxi between Udhampur and Patnitop, one-way or round trip.", "udhampur-to-patnitop-taxi.html"),
    ("Chenani to Patnitop Taxi", "Taxi between Chenani and Patnitop, in both directions.", "chenani-to-patnitop-taxi.html"),
    ("Kud to Patnitop Taxi", "Short-hop taxi between Kud and Patnitop.", "kudh-to-patnitop-taxi.html"),
    ("Airport &amp; Railway Station Transfers", "Jammu Airport, Jammu Railway Station, Katra Railway Station pickup &amp; drop.", "airport-railway-transfer.html"),
    ("Patnitop Sightseeing Taxi", "Local taxi for Nathatop, Sanasar and nearby attractions.", "patnitop-sightseeing.html"),
    ("Nathatop &amp; Sanasar Taxi", "Dedicated taxi service for the Nathatop and Sanasar viewpoints.", "nathatop-sanasar-taxi.html"),
    ("Srinagar Taxi", "Taxi service from Patnitop or Jammu towards Srinagar.", "srinagar-taxi.html"),
    ("Gulmarg Taxi", "Taxi enquiries to Gulmarg from Jammu, Katra and Udhampur, subject to availability.", "gulmarg-taxi.html"),
    ("Pahalgam Taxi", "Taxi enquiries to Pahalgam from Jammu, Katra and Udhampur, subject to availability.", "pahalgam-taxi.html"),
    ("Sonamarg Taxi", "Taxi enquiries to Sonamarg from Jammu, Katra and Udhampur, subject to availability.", "sonamarg-taxi.html"),
    ("Doodhpathri Taxi Enquiry", "Ask about a taxi to Doodhpathri from Jammu, Katra and Udhampur; availability is confirmed first.", "doodhpathri-taxi.html"),
    ("Yusmarg Taxi Enquiry", "Ask about a taxi to Yusmarg from Jammu, Katra and Udhampur; availability is confirmed first.", "yusmarg-taxi.html"),
    ("Bhaderwah Taxi", "Taxi service to Bhaderwah from Patnitop and Jammu.", "bhaderwah-taxi.html"),
    ("Sudh Mahadev Taxi", "Taxi to the ancient Sudh Mahadev temple from Patnitop, Jammu and Katra.", "sudh-mahadev-taxi.html"),
    ("Mantalai Taxi", "Taxi to Mantalai, the place linked in local belief to the Shiv-Parvati wedding.", "mantalai-taxi.html"),
    ("Gauri Kund Taxi", "Taxi to the sacred Gauri Kund near Sudh Mahadev, from Patnitop and Jammu.", "gauri-kund-taxi.html"),
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
    <p>Planning a couple trip or pre-wedding shoot? Your taxi can be combined with a <a href="{PHOTO_PATH}">couple photoshoot in Srinagar or Patnitop</a> arranged through us, where available.</p>
    {cta_buttons()}
  </div>
</section>
{faq_block(taxi_faqs, "Taxi Service FAQs")}
'''
    schemas = [local_business_schema(), breadcrumb_schema([("Home", "index.html"), ("Taxi Services", "taxi-services.html")]), faq_schema(taxi_faqs)]
    return page(
        "Patnitop Taxi Service | Airport, Railway &amp; Sightseeing Taxi",
        "Taxi in Patnitop from Kud, Chenani, Udhampur, Katra and Jammu: airport and railway transfers, sightseeing and outstation trips. Call 9103331334.",
        "taxi-services.html", "taxi-services.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Taxi Services", "taxi-services.html")],
        schema_list=schemas
    )

write("taxi-services.html", build_taxi_services())

# ---------------------------------------------------------------
# ROUTE / KEYWORD LANDING PAGES (shared template)
# ---------------------------------------------------------------

def build_route_page(path, title, meta_desc, h1, intro_paragraphs, points, faqs, active="taxi-services.html", crumb_name=None, related=None, area_served=None, wa_message=None, vehicles_html=None):
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
    {cta_buttons(wa_message=wa_message)}
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>Vehicles available</h2></div>
    {vehicles_html or '<p>Dzire, Ertiga, Innova / Toyota Crysta and Tempo Traveller are commonly available for this route, depending on your group size. <a href="vehicles.html">See all vehicles</a> or call/WhatsApp for the current fare.</p>'}
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
        related=[("Airport & Railway Transfer", "airport-railway-transfer.html"), ("Udhampur to Patnitop Taxi", "udhampur-to-patnitop-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")],
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
        related=[("Airport & Railway Transfer", "airport-railway-transfer.html"), ("Udhampur to Patnitop Taxi", "udhampur-to-patnitop-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Jammu", "Patnitop"],
        active="taxi-services.html", crumb_name=None,
        agent_label="Jammu to Patnitop",
        agent_default_pickup="Jammu (Airport / Railway Station / city)",
        agent_default_drop="Patnitop (your hotel)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="udhampur",
        path="udhampur-to-patnitop-taxi.html",
        title="Udhampur to Patnitop Taxi | Patnitop Travels Hub",
        meta_desc="Book an Udhampur to Patnitop taxi or Patnitop to Udhampur taxi, one-way or round trip. Call or WhatsApp 9103331334 for fare and availability.",
        h1="Udhampur to Patnitop Taxi",
        intro=[
            "Patnitop Travels Hub arranges taxi service between Udhampur and Patnitop, in both directions. Patnitop is in Udhampur district on the Jammu&ndash;Srinagar highway (NH 44), so Udhampur is a common starting or ending point for Patnitop trips.",
            "Tell us your exact pickup point in Udhampur and your travel date, and we will confirm whether we can arrange it and at what fare."
        ],
        points=[
            "Udhampur to Patnitop taxi and Patnitop to Udhampur taxi, both directions",
            "One-way drop or round-trip taxi service, subject to availability",
            "Can be extended onward to Katra, Jammu, Bhaderwah or Srinagar",
            "Family and group transportation, including Tempo Traveller for larger groups",
        ],
        faqs=[
            ("Do you provide Udhampur to Patnitop taxi service?", "Yes, Patnitop Travels Hub arranges taxi service between Udhampur and Patnitop. Call or WhatsApp 9103331334 with your pickup point and date to confirm availability and fare."),
            ("Can I book a one-way taxi from Udhampur to Patnitop?", "Yes, one-way drop is available, along with round-trip service if you need a return journey."),
        ],
        related=[("Jammu to Patnitop Taxi", "jammu-to-patnitop-taxi.html"), ("Chenani to Patnitop Taxi", "chenani-to-patnitop-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html")],
        area_served=["Udhampur", "Patnitop"],
        active="taxi-services.html", crumb_name=None,
        agent_label="Udhampur to Patnitop",
        agent_default_pickup="Udhampur (your pickup point)",
        agent_default_drop="Patnitop (your hotel)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="chenani",
        path="chenani-to-patnitop-taxi.html",
        title="Chenani to Patnitop Taxi | Patnitop Travels Hub",
        meta_desc="Book a Chenani to Patnitop taxi or Patnitop to Chenani taxi with Patnitop Travels Hub. Call or WhatsApp 9103331334 for fare and availability.",
        h1="Chenani to Patnitop Taxi",
        intro=[
            "Patnitop Travels Hub arranges taxi service between Chenani and Patnitop in both directions. Chenani lies on the highway south of Patnitop, towards Udhampur and Jammu.",
            "Share your pickup point in Chenani and your travel date, and we will confirm availability and the current fare for your trip."
        ],
        points=[
            "Chenani to Patnitop taxi and Patnitop to Chenani taxi, both directions",
            "One-way drop or round-trip taxi service, subject to availability",
            "Can be combined with Nathatop and Sanasar sightseeing",
            "Family and group transportation, including Tempo Traveller for larger groups",
        ],
        faqs=[
            ("Do you provide taxi service from Chenani to Patnitop?", "Yes, Patnitop Travels Hub arranges taxi service between Chenani and Patnitop. Call or WhatsApp 9103331334 to confirm availability and fare for your date."),
            ("Can I add sightseeing to a Chenani to Patnitop trip?", "Yes, local sightseeing around Patnitop, Nathatop and Sanasar can be added. Let us know when you enquire."),
        ],
        related=[("Udhampur to Patnitop Taxi", "udhampur-to-patnitop-taxi.html"), ("Kud to Patnitop Taxi", "kudh-to-patnitop-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html")],
        area_served=["Chenani", "Patnitop"],
        active="taxi-services.html", crumb_name=None,
        agent_label="Chenani to Patnitop",
        agent_default_pickup="Chenani (your pickup point)",
        agent_default_drop="Patnitop (your hotel)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="kudh",
        path="kudh-to-patnitop-taxi.html",
        title="Kud to Patnitop Taxi | Patnitop Travels Hub",
        meta_desc="Taxi from Kud to Patnitop and back, one-way or round trip, with Patnitop Travels Hub. Call or WhatsApp 9103331334 for fare and availability.",
        h1="Kud to Patnitop Taxi",
        intro=[
            "Patnitop Travels Hub arranges taxi service between Kud and Patnitop. Kud is a town on the Jammu&ndash;Srinagar highway (NH 44), roughly 10 km before Patnitop when travelling from Udhampur.",
            "Tell us your pickup point in Kud and your travel date, and we will confirm availability and the current fare."
        ],
        points=[
            "Kud to Patnitop taxi and Patnitop to Kud taxi, both directions",
            "One-way drop or round-trip taxi service, subject to availability",
            "Can be combined with Nathatop and Sanasar sightseeing",
            "Onward travel to Katra, Jammu, Bhaderwah or Srinagar can be arranged",
        ],
        faqs=[
            ("Do you provide taxi service from Kud to Patnitop?", "Yes, Patnitop Travels Hub arranges taxi service between Kud and Patnitop. Call or WhatsApp 9103331334 to confirm availability and fare."),
            ("Is Kud written in other ways?", "Yes, the town name is sometimes spelled differently on signs and maps. Whichever spelling you use, call or WhatsApp 9103331334 and we will understand your pickup point."),
        ],
        related=[("Chenani to Patnitop Taxi", "chenani-to-patnitop-taxi.html"), ("Udhampur to Patnitop Taxi", "udhampur-to-patnitop-taxi.html"), ("Nathatop &amp; Sanasar Taxi", "nathatop-sanasar-taxi.html")],
        area_served=["Kud", "Patnitop"],
        active="taxi-services.html", crumb_name=None,
        agent_label="Kud to Patnitop",
        agent_default_pickup="Kud (your pickup point)",
        agent_default_drop="Patnitop (your hotel)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="airport-railway",
        path="airport-railway-transfer.html",
        title="Jammu Airport &amp; Railway Taxi to Patnitop | Patnitop Travels Hub",
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
        related=[("J&K Tour Packages", "tour-packages.html"), ("Couple Photoshoots in Srinagar", PHOTO_PATH), ("Gulmarg Taxi", "gulmarg-taxi.html"), ("Pahalgam Taxi", "pahalgam-taxi.html"), ("Sonamarg Taxi", "sonamarg-taxi.html"), ("Bhaderwah Taxi", "bhaderwah-taxi.html"), ("Vehicles", "vehicles.html")],
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
    dict(
        id="sudh-mahadev",
        path="sudh-mahadev-taxi.html",
        title="Sudh Mahadev Taxi from Patnitop &amp; Jammu | Patnitop Travels Hub",
        meta_desc="Book a Sudh Mahadev taxi from Patnitop, Jammu or Katra for a temple visit or yatra. Call or WhatsApp 9103331334 for fare and availability.",
        h1="Sudh Mahadev Taxi",
        intro=[
            "Sudh Mahadev is an ancient Shiva temple in the hills of the Udhampur region of Jammu &amp; Kashmir, and a well-known pilgrimage stop for devotees travelling through Patnitop. Patnitop Travels Hub arranges taxi service to Sudh Mahadev from Patnitop, Jammu and Katra.",
            "You can book it as a one-way drop, a round trip, or a full-day temple visit. An annual yatra is held in the month of Shravan; dates and arrangements are announced locally each year, so please check with us before planning a yatra-season trip."
        ],
        points=[
            "Taxi from Patnitop to Sudh Mahadev and back",
            "Pickup from Jammu, Jammu Airport, Jammu Railway Station or Katra",
            "One-way drop, round trip or full-day temple visit",
            "Can be combined with <a href=\"gauri-kund-taxi.html\">Gauri Kund</a> and <a href=\"mantalai-taxi.html\">Mantalai</a> on the same trip",
            "Family and group transportation, including Tempo Traveller",
        ],
        faqs=[
            ("How do I book a taxi to Sudh Mahadev?", "Call or WhatsApp Dileep Singh at 9103331334 with your pickup place, travel date and number of people. We will confirm vehicle availability and the current fare."),
            ("Can I visit Sudh Mahadev from Patnitop in one day?", "Yes, a day trip from Patnitop is commonly arranged. Exact timing depends on road and weather conditions, so call us and we will help plan an early start."),
            ("Is a taxi available during the Sudh Mahadev yatra?", "Taxi service is available subject to demand and local traffic arrangements during the yatra season. Please book early and ask us about the current situation before you travel."),
            ("Can I combine Sudh Mahadev with Gauri Kund and Mantalai?", "Yes, these places are close to each other and are often visited together. Tell us what you want to see and we will plan the route and timing with you."),
        ],
        crumb_name="Sudh Mahadev Taxi",
        related=[("Gauri Kund Taxi", "gauri-kund-taxi.html"), ("Mantalai Taxi", "mantalai-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Sudh Mahadev", "Patnitop", "Jammu", "Katra"],
        active="patnitop-sightseeing.html",
        agent_label="Sudh Mahadev Taxi",
        agent_default_pickup="Patnitop, Jammu or Katra",
        agent_default_drop="Sudh Mahadev (return if needed)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="mantalai",
        path="mantalai-taxi.html",
        title="Mantalai Taxi from Patnitop &amp; Jammu | Patnitop Travels Hub",
        meta_desc="Book a Mantalai taxi from Patnitop, Jammu or Katra, alone or with Sudh Mahadev and Gauri Kund. Call or WhatsApp 9103331334 for fare and availability.",
        h1="Mantalai Taxi",
        intro=[
            "Mantalai is a quiet hill village in the Udhampur region, which local belief associates with the wedding of Lord Shiva and Goddess Parvati. It is visited by pilgrims and by travellers who want to see a less crowded side of Jammu &amp; Kashmir. Patnitop Travels Hub arranges taxi service to Mantalai from Patnitop, Jammu and Katra.",
            "Mantalai is usually visited together with Sudh Mahadev and Gauri Kund. Road conditions on the hill routes can change with the season and weather, so we recommend calling us before you travel."
        ],
        points=[
            "Taxi from Patnitop to Mantalai and back",
            "Pickup from Jammu, Jammu Airport, Jammu Railway Station or Katra",
            "Combine with <a href=\"sudh-mahadev-taxi.html\">Sudh Mahadev</a> and <a href=\"gauri-kund-taxi.html\">Gauri Kund</a> in a single day trip",
            "One-way drop, round trip or full-day hire",
            "Family and group transportation, including Tempo Traveller",
        ],
        faqs=[
            ("How do I book a Mantalai taxi?", "Call or WhatsApp 9103331334, or use the booking form on this website with your pickup place, date and group size."),
            ("Is Mantalai connected to Sudh Mahadev?", "Mantalai lies in the same region and is commonly visited along with Sudh Mahadev. We can plan both, and Gauri Kund, as one trip."),
            ("What is the road like to Mantalai?", "Hill roads can be narrow and affected by rain or snow. Call us before you travel and we will advise based on current conditions and the vehicle that suits your group."),
        ],
        crumb_name="Mantalai Taxi",
        related=[("Sudh Mahadev Taxi", "sudh-mahadev-taxi.html"), ("Gauri Kund Taxi", "gauri-kund-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Vehicles", "vehicles.html")],
        area_served=["Mantalai", "Sudh Mahadev", "Patnitop", "Jammu"],
        active="patnitop-sightseeing.html",
        agent_label="Mantalai Taxi",
        agent_default_pickup="Patnitop, Jammu or Katra",
        agent_default_drop="Mantalai (return if needed)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
    dict(
        id="gauri-kund",
        path="gauri-kund-taxi.html",
        title="Gauri Kund Taxi from Patnitop &amp; Jammu | Patnitop Travels Hub",
        meta_desc="Book a Gauri Kund taxi near Sudh Mahadev from Patnitop, Jammu or Katra, with optional Mantalai stop. Call or WhatsApp 9103331334.",
        h1="Gauri Kund Taxi",
        intro=[
            "Gauri Kund is a sacred spring-fed pool near Sudh Mahadev, which local belief associates with Goddess Parvati. Pilgrims visiting Sudh Mahadev often stop here too. Patnitop Travels Hub arranges taxi service to Gauri Kund from Patnitop, Jammu and Katra.",
            "Part of the way to some sacred sites in this area may need to be covered on foot, depending on the season and local arrangements. Tell us your group's needs, such as elderly or young travellers, so we can advise before you set out."
        ],
        points=[
            "Taxi from Patnitop to Gauri Kund and back",
            "Pickup from Jammu, Jammu Airport, Jammu Railway Station or Katra",
            "Easily combined with <a href=\"sudh-mahadev-taxi.html\">Sudh Mahadev</a> and <a href=\"mantalai-taxi.html\">Mantalai</a>",
            "One-way drop, round trip or full-day hire",
            "Family and group transportation, including Tempo Traveller",
        ],
        faqs=[
            ("How do I book a taxi to Gauri Kund?", "Call or WhatsApp Dileep Singh at 9103331334 with your pickup place, date and group size. We will confirm availability and the current fare."),
            ("Is Gauri Kund near Sudh Mahadev?", "Yes, Gauri Kund is in the Sudh Mahadev area and is commonly visited on the same trip. We can arrange both in one taxi booking."),
            ("Is the walk to Gauri Kund difficult for elders or children?", "This depends on the season and local arrangements. Please tell us who is travelling when you call, so we can advise on timing and what to expect."),
        ],
        crumb_name="Gauri Kund Taxi",
        related=[("Sudh Mahadev Taxi", "sudh-mahadev-taxi.html"), ("Mantalai Taxi", "mantalai-taxi.html"), ("Patnitop Sightseeing", "patnitop-sightseeing.html"), ("Hotel Booking", "hotel-booking.html")],
        area_served=["Gauri Kund", "Sudh Mahadev", "Patnitop", "Jammu"],
        active="patnitop-sightseeing.html",
        agent_label="Gauri Kund Taxi",
        agent_default_pickup="Patnitop, Jammu or Katra",
        agent_default_drop="Gauri Kund (return if needed)",
        agent_ask_sightseeing=True, agent_ask_hotel=True,
    ),
]

# ---------------------------------------------------------------
# KASHMIR TAXI PAGES: Gulmarg, Pahalgam, Sonamarg, Doodhpathri, Yusmarg
# Written to be honest by design:
#   - pickup ENQUIRIES from Jammu, Katra and Udhampur only
#   - no fares anywhere: the rate is given on call/WhatsApp (9103331334)
#   - trips are "arranged using our vehicles and partner drivers", never
#     "all vehicles are ours"
#   - no claims about permits, local sightseeing, entry rules or opening
#     seasons: those are "confirmed when you enquire"
#   - Doodhpathri and Yusmarg are ENQUIRY-ONLY pages: we say we confirm
#     whether we can arrange the trip, and the Service schema does not list
#     them as an area served
#   - no distances, drive times or "how to reach" route claims
# tests/check_site.py enforces these rules on all five pages.
# ---------------------------------------------------------------
KASHMIR_PICKUPS = "Jammu, Katra and Udhampur"

# (id, slug, display name, about-the-place sentence, enquiry_only)
KASHMIR_DESTINATIONS = [
    ("gulmarg", "gulmarg-taxi.html", "Gulmarg",
     "Gulmarg is a high meadow resort in the Pir Panjal range of Kashmir, known for its open meadows in summer, snow in winter and its gondola cable car.",
     False),
    ("pahalgam", "pahalgam-taxi.html", "Pahalgam",
     "Pahalgam is a valley town on the Lidder river in south Kashmir, known for its pine forests, meadows and nearby valleys such as Aru and Betaab.",
     False),
    ("sonamarg", "sonamarg-taxi.html", "Sonamarg",
     "Sonamarg is a mountain valley on the Sind river in Kashmir, known for its alpine meadows and the Thajiwas Glacier.",
     False),
    ("doodhpathri", "doodhpathri-taxi.html", "Doodhpathri",
     "Doodhpathri is a quiet meadow destination in Kashmir's Budgam district, known for its green meadows, pine forests and streams.",
     True),
    ("yusmarg", "yusmarg-taxi.html", "Yusmarg",
     "Yusmarg is a meadow destination in Kashmir's Budgam district, known for its pine forests and open green meadows.",
     True),
]

def _kashmir_route(idx):
    rid, path, name, about, enquiry_only = KASHMIR_DESTINATIONS[idx]
    peers = [KASHMIR_DESTINATIONS[(idx + k) % len(KASHMIR_DESTINATIONS)] for k in (1, 2)]
    if enquiry_only:
        intro_1 = (f"Interested in {name}? Send us your plan and Patnitop Travels Hub will confirm whether we can arrange a taxi to {name} "
                   f"for your dates, pickup point and group size. Where we can, the trip is arranged using our vehicles and partner drivers, "
                   f"and nothing is booked until we confirm it with you.")
        title = f"{name} Taxi Enquiry | Jammu, Katra &amp; Udhampur | Patnitop Travels Hub"
        meta = (f"Taxi enquiries for {name} from Jammu, Katra and Udhampur. Call or WhatsApp 9103331334 and we confirm availability "
                f"and the current rate before booking.")
        h1 = f"{name} Taxi Enquiry"
        point_1 = f"Taxi enquiries for {name}, with availability confirmed before booking"
        faq_1 = (f"Can I get a taxi to {name} from Jammu, Katra or Udhampur?",
                 f"You can enquire from all three. Tell us your pickup point, dates and group size on 9103331334 and we will confirm "
                 f"whether we can arrange the trip, and how, before anything is booked.")
        areas = ["Jammu", "Katra", "Udhampur"]
        vehicles_html = ('<p>Which vehicle suits your trip depends on your group size and on availability, and we confirm it when you enquire. '
                         '<a href="vehicles.html">See all vehicles</a> or call/WhatsApp for the current rate.</p>')
    else:
        vehicles_html = None
        intro_1 = (f"Patnitop Travels Hub can arrange a taxi to {name} for travellers setting off from Jammu, Katra or Udhampur, subject to availability. "
                   f"Trips are arranged using our vehicles and partner drivers, and the vehicle, driver and rate are confirmed with you before anything is booked.")
        title = f"{name} Taxi from Jammu, Katra &amp; Udhampur | Patnitop Travels Hub"
        meta = (f"Taxi to {name} from Jammu, Katra and Udhampur with Patnitop Travels Hub, subject to availability. "
                f"Call or WhatsApp 9103331334 for the current rate.")
        h1 = f"{name} Taxi Service"
        point_1 = f"Taxi to {name}, subject to availability"
        faq_1 = (f"Can I get a taxi to {name} from Jammu, Katra or Udhampur?",
                 f"You can enquire from all three. Tell us your pickup point, dates and group size on 9103331334 and we will confirm "
                 f"availability and the plan with you.")
        areas = [name, "Jammu", "Katra", "Udhampur"]
    intro_2 = about
    intro_3 = (f"We do not publish fares for {name}, because the rate depends on your pickup point, dates, number of days, vehicle and group size. "
               f"Call or WhatsApp 9103331334 for the current rate.")
    points = [
        point_1,
        f"Jammu to {name} taxi enquiries",
        f"Katra to {name} taxi enquiries",
        f"Udhampur to {name} taxi enquiries",
        "Vehicle chosen by group size, subject to availability",
        "Route, timing and number of days planned with you before booking",
        "Current rate on call or WhatsApp at 9103331334 (no fixed fares are published)",
    ]
    faqs = [
        faq_1,
        (f"How much does a taxi to {name} cost?",
         f"We do not publish fixed fares. The rate depends on your pickup point, dates, number of days, vehicle and group size. Call or WhatsApp 9103331334 for the current rate."),
        ("Are the vehicles owned by Patnitop Travels Hub?",
         "Trips are arranged using our vehicles and partner drivers, depending on availability. We confirm the vehicle and driver for your trip when you book."),
        (f"What is included in a trip to {name}?",
         "We agree what is included when you enquire, and nothing is assumed. Please ask about tolls, parking, entry fees, waiting time and any sightseeing stop before you book."),
        (f"Do local entry or taxi rules apply at {name}?",
         f"Entry rules and local taxi arrangements can differ by place, vehicle and season. Ask us when you enquire and we will confirm what applies to your trip before booking."),
        ("How do weather and roads affect the trip?",
         "Weather, snow and road conditions change with the season and can affect timing, so we plan the route with you and advise based on current conditions."),
        (f"Can {name} be combined with Srinagar or other places?",
         "A wider itinerary can be discussed. See our Srinagar taxi and J&amp;K tour packages pages, or call or WhatsApp 9103331334."),
    ]
    wa_message = (f"Hello Patnitop Travels Hub, I would like to enquire about a taxi to {name}.\n"
                  f"Pickup (Jammu / Katra / Udhampur):\n"
                  f"Travel dates:\n"
                  f"Number of people:\n"
                  f"One-way or round trip:")
    related = [("Srinagar Taxi", "srinagar-taxi.html"), ("J&K Tour Packages", "tour-packages.html")]
    related += [(f"{p[2]} Taxi", p[1]) for p in peers]
    related += [("Jammu to Patnitop Taxi", "jammu-to-patnitop-taxi.html"),
                ("Katra to Patnitop Taxi", "katra-to-patnitop-taxi.html"),
                ("Udhampur to Patnitop Taxi", "udhampur-to-patnitop-taxi.html")]
    return dict(
        id=rid, path=path, title=title, meta_desc=meta, h1=h1,
        intro=[intro_1, intro_2, intro_3], points=points, faqs=faqs,
        related=related, area_served=areas,
        active="taxi-services.html", crumb_name=f"{name} Taxi",
        wa_message=wa_message, vehicles_html=vehicles_html,
        agent_label=f"{name} Taxi" if not enquiry_only else f"{name} Taxi Enquiry",
        agent_default_pickup="Jammu, Katra or Udhampur",
        agent_default_drop=name,
        agent_ask_sightseeing=False, agent_ask_hotel=False,
    )

ROUTES += [_kashmir_route(i) for i in range(len(KASHMIR_DESTINATIONS))]

for r in ROUTES:
    write(r["path"], build_route_page(
        r["path"], r["title"], r["meta_desc"], r["h1"],
        r["intro"], r["points"], r["faqs"],
        active=r["active"], crumb_name=r["crumb_name"],
        related=r["related"], area_served=r["area_served"],
        wa_message=r.get("wa_message"), vehicles_html=r.get("vehicles_html"),
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
    <p class="small">Note: opening hours, entry fees and exact attraction availability can change — please confirm current details with us or on-site when you visit. Looking for activities such as the gondola ride, zip line, horse riding or trekking? See our guide to <a href="things-to-do-in-patnitop.html">things to do in Patnitop</a>.</p>
    {cta_buttons()}
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>Combine sightseeing with your taxi route</h2></div>
    <p>Sightseeing can be added on to a <a href="katra-to-patnitop-taxi.html">Katra to Patnitop taxi</a>, <a href="jammu-to-patnitop-taxi.html">Jammu to Patnitop taxi</a>, or arranged as a standalone half-day or full-day local taxi hire. <a href="nathatop-sanasar-taxi.html">See Nathatop &amp; Sanasar taxi details</a>. Want photos or a reel of your trip? Ask about a <a href="{PHOTO_PATH}">couple photographer in Patnitop or Srinagar</a> alongside your sightseeing.</p>
  </div>
</section>
<section>
  <div class="container">
    <div class="section-head">
      <h2>Sudh Mahadev, Mantalai &amp; Gauri Kund</h2>
      <p>Three sacred places in the hills near Patnitop, popular with pilgrims and often visited together in one day trip.</p>
    </div>
    <div class="grid grid-3">
      <div class="card service-card"><h3>Sudh Mahadev</h3><p>An ancient Shiva temple and well-known pilgrimage stop.</p><a class="card-link" href="sudh-mahadev-taxi.html">Sudh Mahadev taxi →</a></div>
      <div class="card service-card"><h3>Mantalai</h3><p>A quiet hill village linked in local belief to the Shiv-Parvati wedding.</p><a class="card-link" href="mantalai-taxi.html">Mantalai taxi →</a></div>
      <div class="card service-card"><h3>Gauri Kund</h3><p>A sacred pool near Sudh Mahadev, associated with Goddess Parvati.</p><a class="card-link" href="gauri-kund-taxi.html">Gauri Kund taxi →</a></div>
    </div>
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
# THINGS TO DO IN PATNITOP (activities and experiences guide)
# Honest guide: we are a taxi / travel-assistance business. We do not
# run or sell these activities, quote no prices, and say availability
# must be confirmed on site.
# ---------------------------------------------------------------

ACTIVITY_IDEAS = [
    ("Viewpoints and meadow walks", "Nathatop, Sanasar and the open meadows of Patnitop are the usual starting points for easy walks and mountain views.", "nathatop-sanasar-taxi.html", "Nathatop &amp; Sanasar taxi"),
    ("Gondola ride", "A gondola ride is one of the activities available in Patnitop. Please confirm availability, timings and charges before you go.", None, None),
    ("Zip line", "A zip line is one of the activities available in Patnitop. Please confirm availability, timings and charges before you go.", None, None),
    ("Horse riding", "Horse riding is one of the activities available in Patnitop. Please confirm availability, timings and charges before you go.", None, None),
    ("Shikara boating", "Shikara boating is one of the activities available in Patnitop. Please confirm availability, timings and charges before you go.", None, None),
    ("Trekking and nature walks", "The forested hills around Patnitop are popular for short walks and day treks. Ask us to drop you at a starting point and arrange the pickup time.", None, None),
    ("Snow in winter", "Patnitop sometimes receives snowfall in winter, but snow is not guaranteed and varies from year to year. Road and weather conditions can change quickly, so please check with us before you travel.", None, None),
    ("Temples and pilgrimage stops", "Naag Temple near Patnitop, and Sudh Mahadev, Mantalai and Gauri Kund in the hills nearby, are often combined into one day trip.", "sudh-mahadev-taxi.html", "Sudh Mahadev taxi"),
    ("Family time at the parks", "Children Park, Padora Park and the meadows suit families who want a relaxed day rather than a long trek.", "patnitop-sightseeing.html", "Patnitop sightseeing taxi"),
]

THINGS_TO_DO_FAQS = [
    ("What are the best things to do in Patnitop?", "Popular choices include the Nathatop viewpoint, Sanasar meadow, walks around Patnitop Meadows, nearby temples such as Naag Temple and Sudh Mahadev, and, depending on season and availability, activities such as the gondola ride, zip line, trekking, horse riding, shikara boating and snow visits. Call or WhatsApp 9103331334 and we will help you plan a taxi route around your interests."),
    ("Can you take me to the gondola ride, zip line, horse riding or shikara boating?", "Patnitop Travels Hub provides taxi service and travel assistance, so we can plan your taxi and your return pickup. Please confirm availability, timings and charges of the activities themselves before you go."),
    ("How many days are enough for Patnitop?", "Many visitors spend one to two days, covering Nathatop, Sanasar and the meadows. If you want to add Sudh Mahadev, Mantalai and Gauri Kund, a second day helps. Tell us your plan and we can suggest a sensible route."),
    ("Can you arrange a taxi for a full-day local trip?", "Yes. We arrange half-day and full-day local taxi hire around Patnitop. Call or WhatsApp 9103331334 to check the vehicle and current fare."),
]

def build_things_to_do():
    cards = ""
    for title, desc, link, link_text in ACTIVITY_IDEAS:
        extra = f'<a class="card-link" href="{link}">{link_text} →</a>' if link else ""
        cards += f'<div class="card service-card"><h3>{title}</h3><p>{desc}</p>{extra}</div>'
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Things to Do in Patnitop</h1>
    <p>Places, activities and day-trip ideas around Patnitop, with taxi help from Patnitop Travels Hub.</p>
  </div>
</section>
<section>
  <div class="container">
    <p>Patnitop is a hill station in Jammu &amp; Kashmir, popular for cool weather, meadows and mountain views. Here are common ideas for a visit. Patnitop Travels Hub is a local taxi and travel-assistance service: we can take you there, arrange your pickup, and plan a route that fits your time.</p>
    <div class="grid grid-3">{cards}</div>
    <p class="small">Note: activity availability, timings, entry fees and road or weather conditions change through the year. Please confirm current details before you travel.</p>
    {cta_buttons()}
  </div>
</section>
<section class="section-alt">
  <div class="container">
    <div class="section-head"><h2>Plan your trip with a local taxi</h2></div>
    <p>Reaching Patnitop: we run taxi service from <a href="katra-to-patnitop-taxi.html">Katra</a>, <a href="jammu-to-patnitop-taxi.html">Jammu</a>, <a href="udhampur-to-patnitop-taxi.html">Udhampur</a>, <a href="chenani-to-patnitop-taxi.html">Chenani</a> and <a href="kudh-to-patnitop-taxi.html">Kud</a>. Once you are here, see our <a href="patnitop-sightseeing.html">Patnitop sightseeing taxi</a>, or ask about <a href="hotel-booking.html">hotel booking help</a> and <a href="vehicles.html">vehicles</a>. Travelling as a couple? You can also ask about a <a href="{PHOTO_PATH}">couple photoshoot in Patnitop or Srinagar, with cinematic reels</a>.</p>
  </div>
</section>
{faq_block(THINGS_TO_DO_FAQS, "Things to Do in Patnitop: FAQs")}
'''
    crumbs = [("Home", "index.html"), ("Things to Do in Patnitop", "things-to-do-in-patnitop.html")]
    schemas = [local_business_schema(), breadcrumb_schema(crumbs), faq_schema(THINGS_TO_DO_FAQS)]
    return page(
        "Things to Do in Patnitop | Activities &amp; Day Trips",
        "Things to do in Patnitop: gondola ride, zip line, horse riding, shikara boating, trekking and sightseeing, with local taxi help. Call 9103331334.",
        "things-to-do-in-patnitop.html", "patnitop-sightseeing.html", body,
        breadcrumb_items=crumbs, schema_list=schemas
    )

write("things-to-do-in-patnitop.html", build_things_to_do())

# ---------------------------------------------------------------
# COUPLE PHOTOSHOOTS, REELS & PRE-WEDDING (Srinagar and Patnitop)
# Honest by design: no prices, no fixed package inclusions, no delivery
# times, no availability promises, no reviews, past clients or awards,
# and no photos we do not have the right to use. Everything is "tell us
# your plan, we send a customised quotation". The enquiry ends in a
# WhatsApp hand-off like every other form on the site.
#
# Photos: a location card shows a photo only if the file exists at
# images/photography/<slug>.jpg (slugs are the first item of each
# location below). Add only photos you own or have written permission
# to use. With no file, the card simply shows text.
# ---------------------------------------------------------------

PHOTO_SERVICES = [
    ("Romantic couple photoshoots in Srinagar", "Natural, relaxed couple portraits around Srinagar's lakes, gardens and viewpoints, planned around the light and the season."),
    ("Cinematic Instagram Reels &amp; couple travel videos", "Short vertical reels and cinematic travel clips of your trip, framed for Instagram. Videos can be edited to music, subject to music licensing and availability."),
    ("Pre-wedding photoshoots in Srinagar and Patnitop", "Pre-wedding and engagement shoots in Kashmir's lakes and gardens or in Patnitop's meadows and pine forests."),
    ("Scenic photography around Srinagar", "Dal Lake, houseboats and permitted lakeside locations, Mughal Gardens, other gardens and mountain viewpoints."),
    ("Patnitop forests, meadows and viewpoints", "Couple photoshoots among Patnitop's pine forests, open meadows and scenic viewpoints."),
    ("Photography + taxi + sightseeing", "Custom packages that add a taxi and a sightseeing route to your shoot, where available, so pickup, locations and timings are planned together."),
]

SRINAGAR_LOCATIONS = [
    ("srinagar-dal-lake", "Dal Lake and houseboats", "Shikaras, houseboats and mountain reflections make Dal Lake one of Kashmir's best-known backdrops. We confirm which lakeside spots and houseboats can be used for a shoot."),
    ("srinagar-mughal-gardens", "Mughal Gardens", "Historic terraced gardens beside Dal Lake, such as Nishat Bagh and Shalimar Bagh, known for chinar trees, flowers and fountains in season. Entry rules and photography permissions vary, so we check first."),
    ("srinagar-gardens-viewpoints", "Gardens and mountain viewpoints", "Other gardens and hillside viewpoints around the city, including the tulip garden when it is open in spring. What is possible depends on the time of year."),
    ("srinagar-other", "Other Srinagar locations", "Have a place in mind? Tell us and we will say whether it can work for a couple shoot or reel."),
]

PATNITOP_LOCATIONS = [
    ("patnitop-pine-forests", "Pine forests", "Tall pine-lined paths and quiet forest light, away from the main road."),
    ("patnitop-meadows", "Meadows", "Open grassland at the heart of Patnitop, with wide mountain views."),
    ("patnitop-viewpoints", "Nathatop and Sanasar viewpoints", "Nathatop is a panoramic viewpoint above Patnitop, and Sanasar is a bowl-shaped meadow valley a short drive away."),
]

PHOTO_PACKAGE_IDEAS = [
    ("Photoshoot + taxi", "One plan for your pickup, your shoot locations and your drop, where available. Taxi from Srinagar, Katra, Jammu, Udhampur, Chenani or Kud can be included in the same quotation.", "taxi-services.html", "See taxi services"),
    ("Srinagar shoot + sightseeing", "Combine your Srinagar couple shoot with a sightseeing route and a taxi, with one driver and one schedule.", "srinagar-taxi.html", "See Srinagar taxi"),
    ("Patnitop shoot + sightseeing", "Shoot at Nathatop, Sanasar and the Patnitop meadows while you see the sights.", "patnitop-sightseeing.html", "See Patnitop sightseeing"),
    ("A shoot in both Srinagar and Patnitop", "Ask about planning a trip that covers both places, with transport and stay discussed in the same conversation.", "tour-packages.html", "See J&amp;K tour packages"),
]

PHOTO_STEPS = [
    ("Tell us your plan", "Send the form below, or the ready-made WhatsApp message, with your shoot type, date, location and how long you would like to shoot."),
    ("We confirm the details", "We check photographer availability and confirm what is included, the price and when you will receive your photos or reel, before anything is booked."),
    ("Plan the day", "We settle locations, timing and, if you want one, your taxi and sightseeing route."),
    ("Enjoy the shoot", "Arrive, relax and enjoy Kashmir. Your finished photos or reel follow as agreed with you."),
]

PHOTO_FAQS = [
    ("Do you offer a couple photographer in Srinagar?", "Patnitop Travels Hub can arrange a professional photographer for couple photoshoots in Srinagar, around places such as Dal Lake, houseboats, Mughal Gardens and mountain viewpoints. Send your date and shoot type on WhatsApp at 9103331334 and we will confirm availability."),
    ("Do you arrange a couple photoshoot in Patnitop?", "Yes, we can arrange couple photoshoots in Patnitop's pine forests, meadows and viewpoints such as Nathatop and Sanasar. Share your date and preferred spot and we will confirm what can be arranged."),
    ("Can you arrange a pre-wedding photographer in Kashmir?", "Yes. Pre-wedding and engagement shoots can be arranged in Srinagar and in Patnitop. Tell us your date, location and the look you want, and we will confirm what is possible."),
    ("Do you make cinematic reels in Srinagar?", "You can ask for cinematic Instagram reels and couple travel videos in Srinagar and Patnitop, as photos, reels or both. Tell us what you want and we will include it in your quotation."),
    ("How much does a couple photoshoot cost?", "There is no fixed price list. The cost depends on the shoot type, location, date, duration and whether you want photos, reels or both, so we send a customised quotation once you share your plan. Call or WhatsApp 9103331334."),
    ("Can my reel be edited to music?", "We can edit short videos to music, subject to music licensing and availability. If you plan to post the video publicly, ask us which music can be used, because some popular songs are not licensed for every use."),
    ("Which locations can we shoot at?", "In Srinagar, common choices are Dal Lake, houseboats and lakeside spots, Mughal Gardens, other gardens and mountain viewpoints. In Patnitop, they are the pine forests, meadows, Nathatop and Sanasar. Permissions, entry rules, timing and weather vary by place and season, so we confirm what is possible before the shoot."),
    ("Can I add a taxi and sightseeing to my photoshoot?", "Yes, where available. Photography can be combined with a taxi and a sightseeing route in Srinagar or Patnitop, including pickup from Katra, Jammu, Udhampur, Chenani or Kud. Tell us you need a taxi and we will include it in the same quotation."),
    ("Is an enquiry a confirmed booking?", "No. An enquiry is only a request. A shoot is confirmed only after we agree the date, inclusions and price with you directly."),
]

PHOTO_SHOOT_TYPES = [
    "Couple photoshoot", "Pre-wedding shoot", "Engagement shoot",
    "Cinematic reels / couple travel video", "Travel memories / honeymoon", "Something else / not sure yet",
]
PHOTO_LOCATION_CHOICES = [
    "Srinagar: Dal Lake / houseboats", "Srinagar: gardens / viewpoints", "Patnitop (forests, meadows, viewpoints)",
    "Both Srinagar and Patnitop", "Not sure, please suggest",
]
PHOTO_DURATIONS = ["A short session", "Half day", "Full day", "Not sure, please advise"]

def _loc_cards(items, city):
    out = ""
    for slug, name, desc in items:
        img = ""
        if os.path.exists(os.path.join(ROOT, "images", "photography", f"{slug}.jpg")):
            img = f'<img src="images/photography/{slug}.jpg" alt="Couple photoshoot location: {name}, {city}" loading="lazy" decoding="async">'
        out += f'<div class="card place-card">{img}<h3>{name}</h3><p>{desc}</p></div>'
    return out

def build_photography():
    service_cards = "".join(f'<div class="card service-card"><h3>{n}</h3><p>{d}</p></div>' for n, d in PHOTO_SERVICES)
    srinagar_cards = _loc_cards(SRINAGAR_LOCATIONS, "Srinagar")
    patnitop_cards = _loc_cards(PATNITOP_LOCATIONS, "Patnitop")
    package_cards = "".join(
        f'<div class="card service-card"><h3>{n}</h3><p>{d}</p><a class="card-link" href="{link}">{text} →</a></div>'
        for n, d, link, text in PHOTO_PACKAGE_IDEAS
    )
    step_items = "".join(
        f'<li class="photo-step"><span class="photo-step-num" aria-hidden="true">{i}</span><div><h3>{t}</h3><p>{d}</p></div></li>'
        for i, (t, d) in enumerate(PHOTO_STEPS, start=1)
    )
    shoot_options = "".join(f"<option>{s}</option>" for s in PHOTO_SHOOT_TYPES)
    location_options = "".join(f"<option>{s}</option>" for s in PHOTO_LOCATION_CHOICES)
    duration_options = "".join(f"<option>{s}</option>" for s in PHOTO_DURATIONS)
    wa_quote = wa_href(PHOTO_WA_MSG)

    body = f'''
<section class="photo-hero">
  <div class="container">
    <span class="eyebrow-plain">Srinagar · Patnitop · Kashmir</span>
    <h1>Couple Photographer in Srinagar &amp; Patnitop</h1>
    <p class="lede">Explore the beauty of Kashmir with professional couple photoshoots, cinematic Instagram Reels and pre-wedding photography in Srinagar and Patnitop, with an optional taxi and sightseeing plan from Patnitop Travels Hub.</p>
    <div class="btn-row">
      <a href="#enquiry" class="btn btn-primary">📸 Book a Couple Shoot</a>
      <a href="{wa_quote}" class="btn btn-whatsapp" target="_blank" rel="noopener">💬 Get a Quote on WhatsApp</a>
      <a href="#locations" class="btn btn-outline">Explore Shoot Locations</a>
    </div>
  </div>
  {mountain_art()}
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">What we can arrange</span>
      <h2>Couple photoshoots, reels and pre-wedding shoots in Kashmir</h2>
      <p>Patnitop Travels Hub can arrange a professional photographer and videographer for your trip, so your time in Srinagar and Patnitop comes home as photos and videos you will want to keep.</p>
    </div>
    <div class="grid grid-3">{service_cards}</div>
  </div>
</section>

<section class="section-alt" id="locations">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Srinagar</span>
      <h2>Couple Photoshoot in Srinagar</h2>
      <p>Looking for a couple photographer in Srinagar? We can arrange romantic couple shoots and cinematic reels in Srinagar around Dal Lake, houseboats, the Mughal Gardens and mountain viewpoints. Permissions, entry rules and conditions vary by place and season, so we confirm what is possible before your shoot.</p>
    </div>
    <div class="grid grid-4">{srinagar_cards}</div>
    <p class="small" style="margin-top:18px;">Travelling to Srinagar? See our <a href="srinagar-taxi.html">Srinagar taxi service</a> and <a href="tour-packages.html">J&amp;K tour packages</a>.</p>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Cinematic reels</span>
      <h2>Cinematic Reels in Srinagar and Patnitop</h2>
      <p>Ask for short vertical reels and couple travel videos of your trip, as reels on their own or together with photographs. Videos can be edited to music, subject to music licensing and availability, so tell us if you plan to post publicly.</p>
    </div>
  </div>
</section>

<section class="section-alt">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Pre-wedding</span>
      <h2>Pre-Wedding Photographer in Kashmir</h2>
      <p>Pre-wedding and engagement shoots can be arranged in Srinagar, among the lakes and gardens, and in Patnitop, among meadows and pine forests. Share your date and the look you have in mind and we will confirm what can be arranged.</p>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Patnitop</span>
      <h2>Couple Photoshoot and Pre-Wedding Shoot in Patnitop</h2>
      <p>A hill station in Jammu &amp; Kashmir, Patnitop offers pine forests, open meadows and wide mountain viewpoints for a couple photoshoot or a pre-wedding shoot in Patnitop. Our team is based locally in Patnitop.</p>
    </div>
    <div class="grid grid-3">{patnitop_cards}</div>
    <p class="small" style="margin-top:18px;">Planning the rest of your Patnitop trip? See <a href="things-to-do-in-patnitop.html">things to do in Patnitop</a>, the <a href="patnitop-sightseeing.html">Patnitop sightseeing taxi</a> and the <a href="nathatop-sanasar-taxi.html">Nathatop and Sanasar taxi</a>.</p>
  </div>
</section>

<section class="section-alt" id="packages">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Custom photography packages</span>
      <h2>Build your own shoot package</h2>
      <p>Every shoot is planned around you, so we do not list fixed prices or package inclusions here. Tell us what you want and we will send a customised quotation. Taxi and sightseeing can be added where available.</p>
    </div>
    <div class="grid grid-2">{package_cards}</div>
    <div class="btn-row">
      <a href="#enquiry" class="btn btn-primary">📸 Request a Customised Quote</a>
      <a href="{wa_quote}" class="btn btn-whatsapp" target="_blank" rel="noopener">💬 Get a Quote on WhatsApp</a>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">How it works</span>
      <h2>From enquiry to shoot day</h2>
    </div>
    <ol class="photo-steps">{step_items}</ol>
  </div>
</section>

<section class="section-alt" id="enquiry">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Couple shoot enquiry</span>
      <h2>Book a couple shoot or ask for a quote</h2>
      <p>Tell us a little about your shoot. You can also call <a href="tel:+91{PHONE}">{PHONE}</a>, email <a href="mailto:patnitoptravelshub@gmail.com">patnitoptravelshub@gmail.com</a> or <a href="{wa_quote}" target="_blank" rel="noopener">send the details on WhatsApp</a>.</p>
    </div>
    <div class="booking-panel">
      <form id="photo-enquiry-form">
        <div class="form-grid">
          <div><label for="ph-name">Name</label><input id="ph-name" name="name" autocomplete="name" required></div>
          <div><label for="ph-mobile">Mobile Number</label><input id="ph-mobile" name="mobile" type="tel" inputmode="tel" autocomplete="tel" required></div>
          <div><label for="ph-type">Shoot type</label><select id="ph-type" name="shoot_type">{shoot_options}</select></div>
          <div><label for="ph-location">Location</label><select id="ph-location" name="location">{location_options}</select></div>
          <div><label for="ph-date">Shoot date (optional)</label><input id="ph-date" name="preferred_date" type="date"></div>
          <div><label for="ph-duration">Duration preference</label><select id="ph-duration" name="duration">{duration_options}</select></div>
          <div><label for="ph-people">Number of people (optional)</label><input id="ph-people" name="people" type="number" min="1"></div>
          <div>
            <label>What would you like?</label>
            <div class="radio-row">
              <label><input type="radio" name="deliverable" value="Photos"> Photos</label>
              <label><input type="radio" name="deliverable" value="Reels"> Reels</label>
              <label><input type="radio" name="deliverable" value="Photos and reels" checked> Both</label>
            </div>
          </div>
          <div class="full">
            <label>Do you also need a taxi?</label>
            <div class="radio-row">
              <label><input type="radio" name="taxi" value="Yes"> Yes</label>
              <label><input type="radio" name="taxi" value="No"> No</label>
              <label><input type="radio" name="taxi" value="Not sure yet" checked> Not sure yet</label>
            </div>
          </div>
          <div class="full"><label for="ph-message">Message (ideas, occasion, flexible dates)</label><textarea id="ph-message" name="message" rows="3"></textarea></div>
          <div class="full consent-row"><label><input type="checkbox" name="consent_followup" value="Yes"> You may follow up with me by call or WhatsApp about this enquiry if needed (optional).</label></div>
          <div class="hp" aria-hidden="true"><label>Leave this field empty<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        </div>
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:20px;">Send Couple Shoot Enquiry</button>
        <p class="form-note">Submitting prepares a WhatsApp message with your details, which you send with one tap. This is an enquiry, not a confirmed booking: availability, price and what is included are confirmed with you directly. We use your details only to respond. See our <a href="privacy.html">Privacy page</a>.</p>
      </form>
      <div class="form-success" id="photo-form-success"></div>
    </div>
  </div>
</section>

<section class="section-pine photo-cross">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow-plain">Make it a complete trip</span>
      <h2>Photography, taxi and stay from one place</h2>
    </div>
    <p>Arrange your <a href="srinagar-taxi.html">Srinagar taxi</a> or your pickup from <a href="katra-to-patnitop-taxi.html">Katra</a>, <a href="jammu-to-patnitop-taxi.html">Jammu</a>, <a href="udhampur-to-patnitop-taxi.html">Udhampur</a>, <a href="chenani-to-patnitop-taxi.html">Chenani</a> or <a href="kudh-to-patnitop-taxi.html">Kud</a>, add a <a href="patnitop-sightseeing.html">sightseeing route</a>, and ask about <a href="hotel-booking.html">hotel booking help</a> in the same conversation.</p>
    <div class="btn-row">
      <a href="taxi-services.html" class="btn btn-outline">View Taxi Services</a>
      <a href="tel:+91{PHONE}" class="btn btn-primary">📞 Call {PHONE}</a>
    </div>
  </div>
</section>

{faq_block(PHOTO_FAQS, "Couple Photoshoot FAQs")}
'''
    crumbs = [("Home", "index.html"), ("Couple Photoshoots", PHOTO_PATH)]
    schemas = [
        local_business_schema(),
        breadcrumb_schema(crumbs),
        service_schema(
            "Couple photoshoot, reels and pre-wedding photography",
            "Arranged couple photography, cinematic reels and pre-wedding shoots in Srinagar and Patnitop, quoted individually and optionally combined with taxi and sightseeing.",
            ["Srinagar", "Patnitop", "Nathatop", "Sanasar"],
        ),
        faq_schema(PHOTO_FAQS),
    ]
    return page(
        "Couple Photographer in Srinagar &amp; Patnitop | Pre-Wedding &amp; Reels",
        "Couple photoshoots, pre-wedding shoots and cinematic reels in Srinagar and Patnitop, with optional taxi and sightseeing. Enquire on WhatsApp 9103331334.",
        PHOTO_PATH, PHOTO_PATH, body,
        breadcrumb_items=crumbs, schema_list=schemas
    )

write(PHOTO_PATH, build_photography())

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
    ("Udhampur", "udhampur-to-patnitop-taxi.html"),
    ("Chenani", "chenani-to-patnitop-taxi.html"),
    ("Kud", "kudh-to-patnitop-taxi.html"),
    ("Bhaderwah", "bhaderwah-taxi.html"),
    ("Srinagar", "srinagar-taxi.html"),
    ("Gulmarg", "gulmarg-taxi.html"),
    ("Pahalgam", "pahalgam-taxi.html"),
    ("Sonamarg", "sonamarg-taxi.html"),
    ("Doodhpathri", "doodhpathri-taxi.html"),
    ("Yusmarg", "yusmarg-taxi.html"),
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
          ✉️ <a href="mailto:{EMAIL}">{EMAIL}</a><br>
          ✉️ <a href="mailto:patnitoptravelshub@gmail.com">patnitoptravelshub@gmail.com</a>
        </p>
        {cta_buttons()}
        {google_links_html()}
        <div style="margin-top:28px; border:1px solid var(--line); aspect-ratio:4/3; overflow:hidden;">
          <iframe title="Patnitop location map" src="https://www.google.com/maps?q=Patnitop,Jammu+and+Kashmir&output=embed" width="100%" height="100%" style="border:0;" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
      </div>
      <div class="booking-panel" id="booking-form">
        <h2 class="mt-0">Booking / Enquiry Form</h2>
        <form id="enquiry-form">
          <div class="form-grid">
            <div><label for="name">Name</label><input id="name" name="name" required></div>
            <div><label for="mobile">Mobile Number</label><input id="mobile" name="mobile" type="tel" inputmode="tel" autocomplete="tel" required></div>
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
            <div class="full consent-row"><label><input type="checkbox" name="consent_followup" value="Yes"> You may follow up with me by call or WhatsApp about this enquiry if needed (optional).</label></div>
            <div class="hp" aria-hidden="true"><label>Leave this field empty<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
          </div>
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:20px;">Submit Enquiry</button>
          <p class="form-note">Submitting prepares a WhatsApp message with your details — you send it to us with one tap, or call {PHONE} directly. We use your details only to respond to your enquiry — see our <a href="privacy.html">Privacy page</a>.</p>
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
        "Contact Dileep Singh at Patnitop Travels Hub — call or WhatsApp 9103331334, or fill the booking form for taxi and hotel enquiries.",
        "contact.html", "contact.html", body,
        breadcrumb_items=[("Home", "index.html"), ("Contact", "contact.html")],
        schema_list=schemas
    )

write("contact.html", build_contact())

# ---------------------------------------------------------------
# PRIVACY NOTICE
# Plain-language notice shown wherever contact details are collected.
# ---------------------------------------------------------------

PRIVACY_UPDATED = "20 October 2026"

def build_privacy():
    storage_line = (
        "Enquiries you submit through the chat assistant or the forms may also be recorded in a private spreadsheet that only Patnitop Travels Hub can access, so that we can track and answer them."
        if LEAD_ENDPOINT else
        "At present, enquiries reach us through WhatsApp, phone or email only."
    )
    analytics_line = (
        "This website uses Google Analytics to count visits and button clicks (for example, Call and WhatsApp buttons). These counts are used only to understand which pages help travellers reach us."
        if GA4_ID else
        "This website does not currently run analytics or advertising trackers."
    )
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Privacy Notice</h1>
    <p>Last updated: {PRIVACY_UPDATED}</p>
  </div>
</section>
<section>
  <div class="container">
    <h2>Who we are</h2>
    <p>Patnitop Travels Hub, run by Dileep Singh, Patnitop, Jammu &amp; Kashmir, India. Contact: <a href="tel:+91{PHONE}">{PHONE}</a> or <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    <h2>What we collect</h2>
    <p>Only what you choose to give us when you make an enquiry: your name, mobile number, trip details (pickup, drop, dates, passengers, vehicle) or photoshoot details (shoot type, location, date, duration preference, number of people), any message you write, and whether you tick the optional box allowing us to follow up.</p>
    <h2>How we use it</h2>
    <p>To reply to your enquiry, prepare a fare or itinerary, and, only if you ticked the follow-up box, to contact you again about that enquiry by call or WhatsApp. An enquiry is not a confirmed booking until we confirm it with you directly.</p>
    <h2>Where it goes</h2>
    <p>When you tap a WhatsApp button, your message is sent through WhatsApp and is subject to WhatsApp&rsquo;s own terms. {storage_line}</p>
    <h2>Analytics</h2>
    <p>{analytics_line}</p>
    <h2>Your choices</h2>
    <p>You can ask us to correct or delete the details from your enquiry by calling or emailing us at the contact details above.</p>
  </div>
</section>
'''
    return page(
        "Privacy Notice | Patnitop Travels Hub",
        "How Patnitop Travels Hub uses the details you share when you make a taxi, hotel, couple shoot or product enquiry.",
        "privacy.html", "", body,
        breadcrumb_items=[("Home", "index.html"), ("Privacy", "privacy.html")],
        schema_list=[breadcrumb_schema([("Home", "index.html"), ("Privacy", "privacy.html")])]
    )

write("privacy.html", build_privacy())

# ---------------------------------------------------------------
# LOCAL PRODUCTS ENQUIRY (separate from taxi bookings)
# Enquiry form only. No catalogue, prices, stock or cart — those do not
# exist yet and must be verified before anything is advertised for sale.
# The page is noindex and is not in the nav, footer or sitemap unless
# "indexable_products_page" is switched on in site.config.json.
# ---------------------------------------------------------------

PRODUCT_INTERESTS = ["Honey", "Dry fruits", "Rajma", "Handicrafts", "Gift hampers", "Something else"]

def build_products_enquiry():
    checks = "".join(
        f'<label><input type="checkbox" name="products" value="{p}"> {p}</label>' for p in PRODUCT_INTERESTS
    )
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Local Products Enquiry</h1>
    <p>Honey, dry fruits, rajma, handicrafts and gift hampers from the Patnitop region &mdash; enquiry only.</p>
  </div>
</section>
<section>
  <div class="container">
    <div class="booking-panel" id="product-form">
      <h2 class="mt-0">Tell us what you are looking for</h2>
      <p class="small"><strong>This is an enquiry form, not a shop.</strong> No prices, stock or online ordering are listed here. Send your enquiry and we will get back to you about what we can arrange. This is separate from taxi bookings.</p>
      <form id="product-enquiry-form" data-lead-type="product">
        <div class="form-grid">
          <div><label for="p-name">Name</label><input id="p-name" name="name" required></div>
          <div><label for="p-mobile">Mobile Number</label><input id="p-mobile" name="mobile" type="tel" inputmode="tel" autocomplete="tel" required></div>
          <div class="full">
            <label>Products you are interested in</label>
            <div class="check-row">{checks}</div>
          </div>
          <div><label for="p-qty">Approximate quantity (optional)</label><input id="p-qty" name="quantity" placeholder="e.g. 2 kg, 10 gift boxes"></div>
          <div><label for="p-city">Delivery city / state (optional)</label><input id="p-city" name="delivery_place"></div>
          <div class="full"><label for="p-message">Message</label><textarea id="p-message" name="message" rows="3"></textarea></div>
          <div class="full consent-row"><label><input type="checkbox" name="consent_followup" value="Yes"> You may follow up with me by call or WhatsApp about this enquiry if needed (optional).</label></div>
          <div class="hp" aria-hidden="true"><label>Leave this field empty<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        </div>
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:20px;">Submit Product Enquiry</button>
        <p class="form-note">Submitting prepares a WhatsApp message marked as a product enquiry &mdash; you send it with one tap. We use your details only to respond &mdash; see our <a href="privacy.html">Privacy page</a>.</p>
      </form>
      <div class="form-success" id="product-form-success"></div>
    </div>
  </div>
</section>
'''
    robots = "index, follow" if CONFIG["indexable_products_page"] else "noindex, nofollow"
    return page(
        "Local Products Enquiry | Patnitop Travels Hub",
        "Enquire about local products from the Patnitop region. Enquiry only: no prices or online ordering.",
        "local-products-enquiry.html", "", body,
        breadcrumb_items=[("Home", "index.html"), ("Local Products Enquiry", "local-products-enquiry.html")],
        schema_list=[], robots=robots
    )

write("local-products-enquiry.html", build_products_enquiry())

# ---------------------------------------------------------------
# 404 PAGE (Netlify serves /404.html automatically for unknown URLs)
# ---------------------------------------------------------------

def build_404():
    body = f'''
<section class="page-hero">
  <div class="container">
    <h1>Page not found</h1>
    <p>That page does not exist, but we can still help with your trip.</p>
  </div>
</section>
<section>
  <div class="container">
    {cta_buttons()}
    <p class="small" style="margin-top:20px;"><a href="index.html">Home</a> · <a href="taxi-services.html">Taxi Services</a> · <a href="contact.html">Contact</a></p>
  </div>
</section>
'''
    html = page(
        "Page not found | Patnitop Travels Hub",
        "Page not found. Call or WhatsApp Patnitop Travels Hub on 9103331334 for taxi service in Patnitop.",
        "404.html", "", body, schema_list=[], robots="noindex, follow"
    )
    # Netlify serves this file at whatever URL was requested (e.g. /a/b/c),
    # so relative css/js/links would break. Make them root-absolute.
    return re.sub(r'(href|src)="(?!https?://|tel:|mailto:|#|data:|/)', r'\1="/', html)

write("404.html", build_404())

# ---------------------------------------------------------------
# SITEMAP + ROBOTS (generated, so they can never drift from the pages)
# Lists every indexable page built above. Excludes: 404, the Google
# verification file, and the products page unless made indexable.
# ---------------------------------------------------------------

def build_sitemap_and_robots():
    paths = ["index.html", "taxi-services.html"] + [r["path"] for r in ROUTES] + [
        "patnitop-sightseeing.html", "things-to-do-in-patnitop.html", PHOTO_PATH, "hotel-booking.html", "tour-packages.html",
        "vehicles.html", "faq.html", "contact.html", "privacy.html",
    ]
    if CONFIG["indexable_products_page"]:
        paths.append("local-products-enquiry.html")
    entries = []
    for p in paths:
        loc = f"{SITE_URL}/" if p == "index.html" else f"{SITE_URL}/{p}"
        entries.append(f"  <url>\n    <loc>{loc}</loc>\n  </url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(entries) + "\n</urlset>\n"
    write("sitemap.xml", sitemap)
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")

build_sitemap_and_robots()

# ---------------------------------------------------------------
# AI AGENT KNOWLEDGE SOURCE
# Generated entirely from the constants above (GLOBAL_FAQS, ROUTES,
# TAXI_SERVICES, SIGHTSEEING_PLACES, HOTEL_CATEGORIES, VEHICLES,
# PACKAGE_DESTINATIONS) — nothing here is hand-typed business content;
# it is the same data already used to build the HTML pages, so the
# widget and the pages can never drift out of sync.
# ---------------------------------------------------------------

import html as _html

def _plain(s):
    """Strip tags and decode HTML entities (&amp;, &ndash; ...) for plain-text JS data."""
    return _html.unescape(re.sub("<[^>]+>", "", s))

RATE_TRIP_TYPES = ("one-way", "round-trip", "local-sightseeing")

# A fare may only ever be shown for a trip whose two ends match one of these
# routes. Each route lists two keyword groups; the customer's pickup and drop
# must hit one group each (either way round). Every other trip is "manual
# confirmation by Dileep" - the assistant never stretches a fare to fit.
QUOTE_ENDPOINTS = {
    "katra":    [["katra"], ["patnitop"]],
    "jammu":    [["jammu"], ["patnitop"]],
    "udhampur": [["udhampur"], ["patnitop"]],
    "chenani":  [["chenani"], ["patnitop"]],
    "kudh":     [["kudh", "kud"], ["patnitop"]],
}

# Seats per vehicle as already stated on vehicles.html (None = larger/varies).
VEHICLE_CAPACITY = {"Dzire": 4, "Ertiga": 6, "Innova / Toyota Crysta": 7, "Tempo Traveller": None}

def load_verified_rates():
    """Read data/rates.json and validate it strictly.

    Rates are the ONLY source of prices the assistant may ever quote, and only
    entries that carry a verification date and the person who verified them.
    The file ships empty: no price is invented. Invalid entries stop the build
    rather than being silently published.
    """
    path = os.path.join(ROOT, "data", "rates.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    route_ids = set(QUOTE_ENDPOINTS)
    vehicle_names = {n for n, _ in VEHICLES}
    out = []
    for i, e in enumerate(raw.get("rates", [])):
        where = f"data/rates.json entry #{i + 1}"
        if e.get("route_id") not in route_ids:
            raise SystemExit(f"{where}: route_id must be one of {sorted(route_ids)}")
        if e.get("vehicle") not in vehicle_names:
            raise SystemExit(f"{where}: vehicle must be one of {sorted(vehicle_names)}")
        if e.get("trip_type") not in RATE_TRIP_TYPES:
            raise SystemExit(f"{where}: trip_type must be one of {RATE_TRIP_TYPES}")
        if not isinstance(e.get("amount_inr"), int) or e["amount_inr"] <= 0:
            raise SystemExit(f"{where}: amount_inr must be a positive whole number of rupees")
        if not str(e.get("includes", "")).strip():
            raise SystemExit(f"{where}: includes must say what the fare covers (tolls, waiting, etc.)")
        if not str(e.get("verified_by", "")).strip():
            raise SystemExit(f"{where}: verified_by is required")
        try:
            datetime.date.fromisoformat(e.get("verified_on", ""))
        except ValueError:
            raise SystemExit(f"{where}: verified_on must be a date like 2026-10-20")
        out.append({k: e[k] for k in ("route_id", "vehicle", "trip_type", "amount_inr", "includes", "verified_on", "verified_by")})
    return out

def build_agent_data():
    routes_out = []
    for r in ROUTES:
        routes_out.append({
            "id": r["id"],
            "label": r["agent_label"],
            "path": r["path"],
            "summary": _plain(r["intro"][0]),
            "defaultPickup": r["agent_default_pickup"],
            "defaultDrop": r["agent_default_drop"],
            "askSightseeing": r["agent_ask_sightseeing"],
            "askHotel": r["agent_ask_hotel"],
            "quoteEndpoints": QUOTE_ENDPOINTS.get(r["id"]),
            "faqs": [{"q": q, "a": _plain(a)} for q, a in r["faqs"]],
        })

    data = {
        "whatsappNumber": WA_NUMBER,
        "phone": PHONE,
        "businessName": "Patnitop Travels Hub",
        "leadEndpoint": LEAD_ENDPOINT,
        "privacyPath": "privacy.html",
        "routes": routes_out,
        "taxiServices": [{"name": _plain(n), "desc": d} for n, d, _ in TAXI_SERVICES],
        "sightseeing": [{"name": n, "desc": d} for n, d in SIGHTSEEING_PLACES],
        "hotelCategories": [{"name": n, "desc": d} for n, d in HOTEL_CATEGORIES],
        "vehicles": [{"name": n, "desc": d, "capacity": VEHICLE_CAPACITY.get(n)} for n, d in VEHICLES],
        "packageDestinations": [d for d, _ in PACKAGE_DESTINATIONS],
        "productInterests": PRODUCT_INTERESTS,
        "faqs": [{"q": q, "a": _plain(a)} for q, a in GLOBAL_FAQS],
        "rates": load_verified_rates(),
    }

    js = "// AUTO-GENERATED by build.py from site.config.json, data/rates.json and the\n"
    js += "// content lists in build.py (GLOBAL_FAQS / ROUTES / VEHICLES / ...).\n"
    js += "// Do not hand-edit: change the sources and re-run  python3 build.py\n"
    js += "var AGENT_DATA = " + json.dumps(data, indent=2) + ";\n"

    with open(os.path.join(ROOT, "js", "agent-data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print("wrote js/agent-data.js")

build_agent_data()

print("ALL PAGES BUILT")

