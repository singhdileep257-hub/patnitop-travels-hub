#!/usr/bin/env python3
"""Static guards for the lead-generation work: the eight added landing pages, the call-first
enquiry form on every route/location page, no duplicated copy between the airport pages,
the dashboard being private, and phone/privacy rules.   python3 tests/lead_system.test.py"""
import glob, html, json, os, re, sys, difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARY = "9103331334"
fails = []
def fail(m): fails.append(m)
def read(n): return open(os.path.join(ROOT, n), encoding="utf-8").read()
def visible(raw):
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)))
def body_text(n):
    raw = read(n); i = raw.find('<section class="page-hero">'); j = raw.find("<footer")
    return visible(raw[i:j])
def intro_paras(n):
    """The page's own copy: the first content section only (not shared template text)."""
    raw = read(n); i = raw.find('<section class="page-hero">'); j = raw.find('<section class="section-alt">')
    return [p for p in re.findall(r"<p>(.*?)</p>", raw[i:j], re.S) if len(p) > 120]

NEW = {
    "jammu-airport-taxi.html": "Jammu Airport", "katra-railway-station-taxi.html": "Katra Railway Station",
    "katra-to-jammu-taxi.html": "Katra", "tempo-traveller-booking.html": "Tempo Traveller",
    "urbania-booking.html": "Urbania", "glanza-taxi-service.html": "Glanza",
    "ramban-taxi-service.html": "Ramban", "banihal-taxi-service.html": "Banihal",
}
sitemap = read("sitemap.xml"); agent = read("js/agent-data.js")
for fn, key in NEW.items():
    if not os.path.exists(os.path.join(ROOT, fn)): fail(f"{fn}: page missing"); continue
    raw = read(fn); vis = body_text(fn)
    if f"/{fn}</loc>" not in sitemap: fail(f"{fn}: not in sitemap.xml")
    if f'rel="canonical" href="' not in raw or f'/{fn}"' not in raw: fail(f"{fn}: canonical missing/wrong")
    if key not in re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S).group(1): fail(f"{fn}: H1 must name {key}")
    if fn not in agent: fail(f"{fn}: missing from agent-data.js")
    if len(re.findall(r'<details class="faq-item">', raw)) < 5: fail(f"{fn}: needs at least 5 visible FAQs")
    if not re.search(r'<a href="tel:\+91' + PRIMARY + r'" class="btn btn-pine">', raw): fail(f"{fn}: main Call button missing")
    if "Kudh" in vis: fail(f"{fn}: use Kud, never Kudh")
    # honesty: no prices, figures, ratings or unverified promises
    if re.search(r"₹|\brs\b\.?|\brupees?\b|per\s?km|starting (from|at)|\bcheap|lowest|guarantee|discount|\bbest (price|rate)", vis, re.I): fail(f"{fn}: price/promise wording")
    if re.search(r"reviews?\b|rated|testimonial|award|trusted|experienced|\d+\s*(years|km|kms|hours|hrs|seats|seater)", vis, re.I): fail(f"{fn}: unverified claim wording")
    leftover = re.sub(r"NH 44", "", re.sub(PRIMARY, "", vis))
    if re.search(r"\d", leftover): fail(f"{fn}: contains numbers other than the phone number: {re.findall(r'.{12}\d+.{8}', leftover)[:2]}")
    if "subject to availability" not in vis and fn not in ("katra-to-jammu-taxi.html", "jammu-airport-taxi.html", "katra-railway-station-taxi.html"): fail(f"{fn}: must say subject to availability")
    for need in ("confirmed only when we confirm", "We do not publish fixed fares"):
        if need not in vis: fail(f"{fn}: missing honesty wording {need!r}")

# no duplicated copy between the three airport/railway pages
paras = intro_paras
pairs = [("jammu-airport-taxi.html", "airport-railway-transfer.html"), ("katra-railway-station-taxi.html", "airport-railway-transfer.html"), ("jammu-airport-taxi.html", "katra-railway-station-taxi.html"), ("tempo-traveller-booking.html", "urbania-booking.html"), ("ramban-taxi-service.html", "banihal-taxi-service.html")]
for a, b in pairs:
    for pa in paras(a):
        for pb in paras(b):
            if difflib.SequenceMatcher(None, pa, pb).ratio() > 0.8: fail(f"duplicate paragraph between {a} and {b}: {pa[:60]!r}")
# titles/h1 must all be distinct (a cannibalisation guard)
titles = {}
for f in glob.glob(os.path.join(ROOT, "*.html")):
    m = re.search(r"<title>(.*?)</title>", open(f, encoding="utf-8").read(), re.S)
    if m: titles.setdefault(m.group(1).strip(), []).append(os.path.basename(f))
for t, ns in titles.items():
    if len(ns) > 1: fail(f"duplicate title {t!r}: {ns}")
# combined page must link to both dedicated pages
comb = read("airport-railway-transfer.html")
for need in ("jammu-airport-taxi.html", "katra-railway-station-taxi.html"):
    if f'href="{need}"' not in comb: fail(f"airport-railway-transfer.html must link to {need}")

# every route / location landing page has the call-first enquiry form with the required fields
ROUTE_PAGES = [f for f in map(os.path.basename, glob.glob(os.path.join(ROOT, "*-taxi.html")) + glob.glob(os.path.join(ROOT, "*-taxi-service.html")) + glob.glob(os.path.join(ROOT, "*-booking.html")))
               if f not in ("hotel-booking.html",)] + ["airport-railway-transfer.html"]
for fn in sorted(set(ROUTE_PAGES)):
    raw = read(fn)
    if 'id="route-enquiry-form"' not in raw: fail(f"{fn}: enquiry form missing"); continue
    for field in ("name", "mobile", "pickup", "drop", "travel_date", "passengers", "vehicle", "website"):
        if f'name="{field}"' not in raw: fail(f"{fn}: form field {field} missing")
    for v in ("Dzire", "Ertiga", "Glanza", "Innova / Toyota Crysta", "Tempo Traveller", "Urbania"):
        if f"<option>{v}</option>" not in raw: fail(f"{fn}: vehicle option {v} missing")
    if 'id="enquiry"' not in raw or 'href="#enquiry"' not in raw: fail(f"{fn}: Book button must jump to the form (#enquiry)")
    if raw.find('href="tel:+91' + PRIMARY + '" class="btn btn-pine"') > raw.find('class="btn btn-whatsapp"'): fail(f"{fn}: Call button must come before WhatsApp")
    if "Fastest way to book: call" not in raw: fail(f"{fn}: form must lead with the call")
    if "js/tracking.js" not in raw or "js/script.js" not in raw: fail(f"{fn}: tracking/form scripts missing")
# the contact page and homepage still carry the original form / buttons
if 'id="enquiry-form"' not in read("contact.html"): fail("contact.html: original booking form removed")

# dashboard: private
d = read("dashboard.html")
if "noindex" not in d: fail("dashboard.html must be noindex")
if "dashboard.html" in sitemap: fail("dashboard.html must not be in the sitemap")
for f in glob.glob(os.path.join(ROOT, "*.html")):
    if os.path.basename(f) != "dashboard.html" and "dashboard.html" in open(f, encoding="utf-8").read(): fail(f"{os.path.basename(f)} links to the private dashboard")
if re.search(r"key\s*=\s*['\"][a-z0-9]{12,}", d + read("js/dashboard.js")): fail("a dashboard key appears to be hard-coded")
if "Confirmed bookings" not in d + read("js/dashboard.js"): fail("dashboard must show confirmed bookings separately")

# only the primary number anywhere
for f in glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "js", "*.js")):
    r = open(f, encoding="utf-8").read()
    if "8493988568" in r: fail(f"{os.path.basename(f)}: removed alternate number present")
    if f.endswith(".html"):
        for n in re.findall(r"tel:\+?(\d+)", r):
            if n != "91" + PRIMARY: fail(f"{os.path.basename(f)}: unexpected tel number {n}")
    else:
        for n in re.findall(r"(?<!\d)(?:\+?91)?([6-9]\d{9})(?!\d)", r):
            if n != PRIMARY: fail(f"{os.path.basename(f)}: unexpected phone-like number {n}")

if fails:
    print("FAILED:"); [print(" -", x) for x in fails]; sys.exit(1)
print(f"lead system checks passed: {len(NEW)} new pages, {len(set(ROUTE_PAGES))} route pages with forms, private dashboard")
