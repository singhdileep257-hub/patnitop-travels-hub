#!/usr/bin/env python3
"""Validates structured data and the phone number on EVERY URL in sitemap.xml.   python3 tests/seo_phone_schema.test.py
This is a local validator (Google's Rich Results Test cannot be run from here). It checks the parts we control:
valid JSON-LD, one consistent business entity, the one phone number everywhere, no old numbers, no fake ratings/reviews,
FAQ schema equal to the visible FAQ, breadcrumbs that match the page, and the local-SEO service-area block."""
import glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P, INTL = "9103331334", "+919103331334"
SITE = json.load(open(os.path.join(ROOT, "site.config.json")))["site_url"].rstrip("/")
BID = SITE + "/#business"
fails = []
def fail(m): fails.append(m)
def read(n): return open(os.path.join(ROOT, n), encoding="utf-8").read()
def strip(raw): return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S))))

urls = re.findall(r"<loc>([^<]+)</loc>", read("sitemap.xml"))
if len(urls) != 36: fail(f"expected 36 sitemap URLs, found {len(urls)}")

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

def types(n):
    t = n.get("@type"); return t if isinstance(t, list) else [t]

ROUTE_TAXI = 0
for u in urls:
    fn = (u[len(SITE) + 1:] or "index.html")
    if not os.path.exists(os.path.join(ROOT, fn)): fail(f"{u}: no file"); continue
    raw = read(fn); vis = strip(raw)
    # ---- phone everywhere ----
    desc = re.search(r'<meta name="description" content="(.*?)"', raw, re.S).group(1)
    if P not in desc: fail(f"{fn}: meta description lacks {P}")
    if f'content="{INTL}"' not in raw or "business:contact_data:phone_number" not in raw: fail(f"{fn}: phone metadata tag missing")
    hdr = raw[raw.find("<header"):raw.find("</header>")]; ftr = raw[raw.find("<footer"):]; top = raw[raw.find('<div class="topbar">'):raw.find("<header")]
    if f"tel:+91{P}" not in hdr: fail(f"{fn}: header Call button missing")
    if f"tel:+91{P}" not in ftr or P not in strip(ftr): fail(f"{fn}: footer phone missing")
    if f"tel:+91{P}" not in top or P not in strip(top): fail(f"{fn}: top bar phone missing")
    if 'class="mobile-bar"' not in raw or f'<a class="call" href="tel:+91{P}"' not in raw[raw.find('class="mobile-bar"'):]: fail(f"{fn}: sticky mobile Call bar missing")
    if vis.count(P) < 3: fail(f"{fn}: number visible fewer than 3 times")
    for n in set(re.findall(r"tel:\+?(\d+)", raw)):
        if n != "91" + P: fail(f"{fn}: unexpected tel: {n}")
    for n in set(re.findall(r"wa\.me/(\d+)", raw)):
        if n != "91" + P: fail(f"{fn}: unexpected wa.me {n}")
    if "8493988568" in raw: fail(f"{fn}: old number present")
    if "Kud, Patnitop" not in ftr: fail(f"{fn}: footer address must read 'Kud, Patnitop' (matches structured data)")
    # ---- structured data ----
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    nodes = []
    for b in blocks:
        try: nodes.append(json.loads(b))
        except Exception as e: fail(f"{fn}: invalid JSON-LD ({e})")
    allnodes = [n for d in nodes for n in walk(d)]
    biz = [d for d in nodes if "TravelAgency" in types(d) and d.get("@id") == BID]
    if len(biz) != 1: fail(f"{fn}: needs exactly one top-level business node with @id {BID}, found {len(biz)}")
    else:
        b = biz[0]
        if b.get("telephone") != INTL: fail(f"{fn}: business telephone != {INTL}")
        if b.get("name") != "Patnitop Travels Hub": fail(f"{fn}: business name wrong")
        if b.get("url") != SITE + "/": fail(f"{fn}: business url wrong")
        a = b.get("address", {})
        for k, v in (("addressLocality", "Patnitop"), ("addressRegion", "Jammu and Kashmir"), ("addressCountry", "IN")):
            if a.get(k) != v: fail(f"{fn}: address {k} should be {v}")
        if "Kud" not in a.get("streetAddress", ""): fail(f"{fn}: streetAddress should include Kud")
        cps = b.get("contactPoint", [])
        if not cps or any(c.get("telephone") != INTL or c.get("contactType") != "reservations" for c in cps): fail(f"{fn}: contactPoint must be the reservations number")
        if not b.get("openingHoursSpecification"): fail(f"{fn}: opening hours missing")
        names = {x.get("name") for x in b.get("areaServed", [])}
        for need in ("Jammu", "Katra", "Udhampur", "Patnitop", "Kud", "Ramban", "Banihal"):
            if need not in names: fail(f"{fn}: areaServed missing {need}")
        for s in b.get("sameAs", []):
            if not re.match(r"^https://", s): fail(f"{fn}: sameAs must be https URLs")
    # honesty: never invent ratings, reviews or prices in schema
    for n in allnodes:
        for bad in ("aggregateRating", "review", "priceRange", "offers"):
            if bad in n: fail(f"{fn}: schema contains {bad} (no invented ratings, reviews or prices)")
    for n in allnodes:
        if n.get("telephone") not in (None, INTL): fail(f"{fn}: schema telephone {n.get('telephone')} is not {INTL}")
        if "servicePhone" in n and n["servicePhone"].get("telephone") != INTL: fail(f"{fn}: servicePhone wrong")
    for d in nodes:
        if "TaxiService" in types(d):
            ROUTE_TAXI += 1
            if d.get("provider", {}).get("@id") != BID: fail(f"{fn}: TaxiService provider must reference {BID}")
            if d.get("availableChannel", {}).get("servicePhone", {}).get("telephone") != INTL: fail(f"{fn}: TaxiService must carry the reservations phone channel")
            if not d.get("areaServed"): fail(f"{fn}: TaxiService has no areaServed")
    # FAQ schema must equal the visible FAQ
    faq = [d for d in nodes if d.get("@type") == "FAQPage"]
    vis_q = [html.unescape(re.sub(r"<[^>]+>", "", q)).strip() for q in re.findall(r'<summary[^>]*>(.*?)</summary>', raw, re.S)]
    for d in faq:
        sq = [q["name"].strip() for q in d["mainEntity"]]
        if [x.replace("'", '"') for x in sq] != [x.replace("'", '"').replace("’", "'") for x in vis_q] and sorted(sq) != sorted(vis_q):
            fail(f"{fn}: FAQ structured data does not match the visible FAQ ({len(sq)} vs {len(vis_q)})")
    # breadcrumb: last item is this page; every item is an absolute URL on this site
    for d in nodes:
        if d.get("@type") == "BreadcrumbList":
            items = d["itemListElement"]
            if [i["position"] for i in items] != list(range(1, len(items) + 1)): fail(f"{fn}: breadcrumb positions not sequential")
            for i in items:
                if not i["item"].startswith(SITE + "/"): fail(f"{fn}: breadcrumb item off-site {i['item']}")
            if fn != "index.html" and items[-1]["item"] != u: fail(f"{fn}: last breadcrumb is not this page")

# dedicated service pages must each carry TaxiService
for fn in ("jammu-to-patnitop-taxi.html", "katra-to-patnitop-taxi.html", "udhampur-to-patnitop-taxi.html", "jammu-airport-taxi.html", "katra-railway-station-taxi.html",
           "tempo-traveller-booking.html", "urbania-booking.html", "glanza-taxi-service.html", "ramban-taxi-service.html", "banihal-taxi-service.html", "katra-to-jammu-taxi.html", "index.html", "taxi-services.html"):
    if '"@type": "TaxiService"' not in read(fn): fail(f"{fn}: TaxiService structured data missing")

# local SEO: service-area hub on home + taxi-services, all links real, a Call button per area
for fn in ("index.html", "taxi-services.html"):
    raw = read(fn)
    m = re.search(r'<section id="service-areas">(.*?)</section>', raw, re.S)
    if not m: fail(f"{fn}: service-areas block missing"); continue
    blk = m.group(1)
    if len(re.findall(r'tel:\+91' + P, blk)) < 5: fail(f"{fn}: service-areas needs a Call link in each of 4 areas + intro")
    for city in ("Jammu", "Katra", "Udhampur", "Patnitop"):
        if f"Taxi from {city}" not in blk and f"Taxi in {city}" not in blk: fail(f"{fn}: service-areas missing {city}")
    for href in re.findall(r'href="([^"#?]+\.html)"', blk):
        if not os.path.exists(os.path.join(ROOT, href)): fail(f"{fn}: service-areas links to missing {href}")
    if re.search(r"₹|\d+\s*(km|kms|hours|hrs)\b", strip(blk), re.I): fail(f"{fn}: service-areas must not state fares, distances or times")

# one number in every data file too
for f in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True):
    if not os.path.isfile(f) or any(x in f for x in (".git/", "node_modules", "/tests/", "googleb3")) or not f.endswith((".html", ".js", ".json", ".xml", ".txt", ".gs", ".md")): continue
    t = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.findall(r"(?<!\d)(?:\+?91[\s-]?)?0?([6-9]\d{4}[\s-]?\d{5})(?!\d)", t):
        d = re.sub(r"\D", "", m)
        if d != P: fail(f"{os.path.relpath(f, ROOT)}: other phone-like number {m}")

if fails:
    print("FAILED:"); [print(" -", x) for x in fails[:40]]; sys.exit(1)
print(f"seo/phone/schema checks passed on {len(urls)} sitemap pages ({ROUTE_TAXI} TaxiService nodes)")
