#!/usr/bin/env python3
"""Static checks for the built site. Run from anywhere:  python3 tests/check_site.py
Fails (exit 1) on any problem. Standard library only."""
import glob, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
SITE = cfg["site_url"].rstrip("/")
failures = []

def fail(msg): failures.append(msg)

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""; self._t = False; self.h1 = 0; self.meta = {}; self.canonical = None
        self.links = []; self.assets = []; self.ids = set(); self.jsonld = []; self._j = False; self._buf = ""
        self.imgs_no_alt = 0; self.hrefs = []
    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a: self.ids.add(a["id"])
        if tag == "title": self._t = True
        elif tag == "h1": self.h1 += 1
        elif tag == "meta":
            k = a.get("name") or a.get("property")
            if k: self.meta[k] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical": self.canonical = a.get("href")
        elif tag == "link" and a.get("rel") == "stylesheet" and not a.get("href", "").startswith("http"): self.assets.append(a["href"])
        elif tag == "script":
            if a.get("type") == "application/ld+json": self._j = True; self._buf = ""
            elif a.get("src") and not a["src"].startswith("http"): self.assets.append(a["src"])
        elif tag == "a" and "href" in a: self.hrefs.append(a["href"])
        elif tag == "img" and not a.get("alt"): self.imgs_no_alt += 1
    def handle_endtag(self, tag):
        if tag == "title": self._t = False
        if tag == "script" and self._j: self.jsonld.append(self._buf); self._j = False
    def handle_data(self, d):
        if self._t: self.title += d
        if self._j: self._buf += d

pages = sorted(f for f in glob.glob(os.path.join(ROOT, "*.html")) if not os.path.basename(f).startswith("google"))
parsed = {}
for f in pages:
    n = os.path.basename(f)
    raw = open(f, encoding="utf-8").read()
    p = P(); p.feed(raw); parsed[n] = (p, raw)

titles = {}
for n, (p, raw) in parsed.items():
    if n == "404.html":
        pass
    if p.h1 != 1: fail(f"{n}: expected 1 <h1>, found {p.h1}")
    t = p.title.strip()
    if not (15 <= len(t) <= 75): fail(f"{n}: title length {len(t)} outside 15-75")
    titles.setdefault(t, []).append(n)
    d = p.meta.get("description", "")
    if not (50 <= len(d) <= 170): fail(f"{n}: meta description length {len(d)} outside 50-170")
    want = f"{SITE}/" if n == "index.html" else f"{SITE}/{n}"
    if p.canonical != want: fail(f"{n}: canonical {p.canonical!r} != {want!r}")
    if p.meta.get("og:url") != want: fail(f"{n}: og:url mismatch")
    robots = p.meta.get("robots", "")
    expect_noindex = n in ("404.html", "local-products-enquiry.html") and not (n == "local-products-enquiry.html" and cfg.get("indexable_products_page"))
    if expect_noindex and "noindex" not in robots: fail(f"{n}: should be noindex, robots={robots!r}")
    if not expect_noindex and "noindex" in robots: fail(f"{n}: unexpectedly noindex")
    for j in p.jsonld:
        try: json.loads(j)
        except Exception as e: fail(f"{n}: invalid JSON-LD ({e})")
    if p.imgs_no_alt: fail(f"{n}: {p.imgs_no_alt} <img> without alt")
    for a in p.assets:
        a = a.lstrip("/")
        if not os.path.exists(os.path.join(ROOT, a)): fail(f"{n}: missing asset {a}")
    for h in p.hrefs:
        if re.match(r"^(https?:|tel:|mailto:|data:)", h): continue
        if h.startswith("#"): continue
        target, _, frag = h.partition("#")
        target = target.lstrip("/")
        if target and not os.path.exists(os.path.join(ROOT, target)): fail(f"{n}: broken internal link {h}")
        elif frag and target in parsed and frag not in parsed[target][0].ids: fail(f"{n}: link {h} points to missing #{frag}")
    # claims we must never make without verification
    for bad in ("priceRange", "aggregateRating", "AggregateRating", '"review"', "★", "₹", " Rs.", "Rs "):
        if bad in raw: fail(f"{n}: contains unverified-claim marker {bad!r}")
    for num in re.findall(r"tel:\+?(\d+)", raw):
        if num != "919103331334": fail(f"{n}: unexpected phone number {num}")
    if "8493988568" in raw: fail(f"{n}: removed alternate phone number 8493988568 is still present")
    for num in re.findall(r"wa\.me/(\d+)", raw):
        if num != "919103331334": fail(f"{n}: unexpected WhatsApp number {num}")
    if "PRODUCT" in raw.upper() and n not in ("local-products-enquiry.html", "404.html"):
        if re.search(r"honey|rajma|dry fruit|hamper", raw, re.I): fail(f"{n}: advertises products outside the enquiry page")

for t, ns in titles.items():
    if len(ns) > 1: fail(f"duplicate title {t!r}: {ns}")

# 404 must use root-absolute asset paths
raw404 = parsed["404.html"][1]
if 'href="css/style.css"' in raw404 or 'src="js/' in raw404: fail("404.html: relative asset paths would break on nested URLs")

# sitemap / robots
sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
indexable = [n for n, (p, _) in parsed.items() if "noindex" not in p.meta.get("robots", "")]
want_locs = sorted((f"{SITE}/" if n == "index.html" else f"{SITE}/{n}") for n in indexable)
if sorted(locs) != want_locs:
    fail("sitemap.xml does not match the indexable pages.\n  missing: %s\n  extra: %s" % (sorted(set(want_locs) - set(locs)), sorted(set(locs) - set(want_locs))))
if len(set(locs)) != len(locs): fail("sitemap.xml has duplicate URLs")
rb = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
if f"Sitemap: {SITE}/sitemap.xml" not in rb: fail("robots.txt Sitemap line does not match site_url")

# agent data: no prices unless verified rates exist
ad = open(os.path.join(ROOT, "js", "agent-data.js"), encoding="utf-8").read()
data = json.loads(ad[ad.index("{"): ad.rindex("}") + 1])
rates = json.load(open(os.path.join(ROOT, "data", "rates.json"), encoding="utf-8")).get("rates", [])
if len(data["rates"]) != len(rates): fail("agent-data.js rates differ from data/rates.json (re-run build.py)")
for r in data["rates"]:
    for k in ("verified_on", "verified_by", "includes"):
        if not r.get(k): fail(f"rate missing {k}: {r}")

# ---------------------------------------------------------------
# Kashmir taxi pages (Gulmarg, Pahalgam, Sonamarg, Doodhpathri, Yusmarg).
# These guard the honesty rules the pages were written under: pages exist and
# are indexable, canonical + sitemap are right, the only contact number is
# 9103331334, internal links are valid and reciprocal, and nothing invented
# appears (no prices or other figures, no permit/ownership/sightseeing or
# availability claims, "Kud" never "Kudh").
# ---------------------------------------------------------------
import html as _kh
KASHMIR = {
    "gulmarg-taxi.html": ("Gulmarg", False), "pahalgam-taxi.html": ("Pahalgam", False),
    "sonamarg-taxi.html": ("Sonamarg", False), "doodhpathri-taxi.html": ("Doodhpathri", True),
    "yusmarg-taxi.html": ("Yusmarg", True),
}
PRIMARY = "9103331334"
BANNED = [
    (r"₹|\brs\b\.?|\binr\b|\brupees?\b|\busd\b|\$|per\s?km|/\s?km|starting (from|at)", "price wording"),
    (r"permit", "permit claim"),
    (r"licen[cs]ed|authori[sz]ed|certified|insured|guarantee|cheap|lowest|best (price|rate)|discount|refund|free cancellation|round the clock|always available|instant", "unverified promise"),
    (r"experienced|trusted|reliable|professional drivers?|verified drivers?|\byears?\b|customers served|reviews?|\brated\b|testimonial|award|number one|no\. ?1|#1", "unverified business claim"),
    (r"our own (vehicles|fleet|cars|taxis)|(?<!see )all (our )?(vehicles|cars|taxis)|every (vehicle|car|taxi)|our fleet|we own", "vehicle-ownership claim"),
    (r"(local )?sightseeing (is |are )?(included|provided|available|guaranteed)", "sightseeing claim"),
]
ENQUIRY_ONLY_BANNED = r"\bwe (provide|offer|operate|run|serve)\b|available (daily|every day|all year)|regular (service|trips)|daily service|yes, we"

def _kvisible(raw):
    main = raw[raw.find('class="page-hero"'):raw.find("<footer")]
    main = re.sub(r"<script.*?</script>|<style.*?</style>", " ", main, flags=re.S)
    return _kh.unescape(re.sub(r"<[^>]+>", " ", main))

sm_locs = set(re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()))
agent_js = open(os.path.join(ROOT, "js", "agent-data.js"), encoding="utf-8").read()
agent_routes = {r["path"]: r for r in json.loads(agent_js[agent_js.index("{"): agent_js.rindex("}") + 1])["routes"]}

for fn, (place, enquiry_only) in KASHMIR.items():
    tag = f"{fn}"
    if fn not in parsed:
        fail(f"{tag}: page is missing"); continue
    p, raw = parsed[fn]
    if f"{SITE}/{fn}" not in sm_locs: fail(f"{tag}: not in sitemap.xml")
    if p.canonical != f"{SITE}/{fn}": fail(f"{tag}: canonical wrong ({p.canonical!r})")
    if "noindex" in p.meta.get("robots", ""): fail(f"{tag}: must be indexable")
    for field, text in (("title", p.title), ("meta description", p.meta.get("description", ""))):
        if place not in _kh.unescape(text): fail(f"{tag}: {field} does not name {place}")
    if place not in _kh.unescape(re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S).group(1)): fail(f"{tag}: H1 does not name {place}")
    vis = _kvisible(raw)
    meta_all = _kh.unescape(p.title + " " + p.meta.get("description", "") + " " + p.meta.get("og:description", "") + " " + p.meta.get("twitter:description", ""))
    # the FAQ and Service structured data are published text too, so they are held to the same rules
    # (LocalBusiness/TravelAgency is the same site-wide block on every page and is checked elsewhere)
    def _strings(o):
        if isinstance(o, str): yield o
        elif isinstance(o, dict):
            for v in o.values(): yield from _strings(v)
        elif isinstance(o, list):
            for v in o: yield from _strings(v)
    schema_text = ""
    for j in p.jsonld:
        d = json.loads(j)
        for node in (d if isinstance(d, list) else [d]):
            if node.get("@type") in ("FAQPage", "Service"):
                schema_text += " " + " ".join(s for k, v in node.items() if k not in ("@context", "@type", "provider") for s in _strings(v))
    scan = vis + " " + meta_all + " " + _kh.unescape(schema_text)

    # contact: only the primary number, for calls and WhatsApp, and it must be prominent
    if not re.search(r'<a href="tel:\+91' + PRIMARY + r'" class="btn btn-pine">', raw): fail(f"{tag}: missing the main Call button for {PRIMARY}")
    if not re.search(r'href="https://wa\.me/91' + PRIMARY + r'\?text=[^"]*" data-whatsapp', raw): fail(f"{tag}: missing the WhatsApp button for {PRIMARY}")
    if "Call or WhatsApp Dileep Singh at " + PRIMARY not in vis: fail(f"{tag}: hero must show {PRIMARY}")
    if set(re.findall(r"tel:\+?(\d+)", raw)) != {"91" + PRIMARY}: fail(f"{tag}: tel: links must all be +91{PRIMARY}")
    if set(re.findall(r"wa\.me/(\d+)", raw)) != {"91" + PRIMARY}: fail(f"{tag}: wa.me links must all be 91{PRIMARY}")
    if set(re.findall(r'"telephone":\s*"([^"]+)"', raw)) != {"+91" + PRIMARY}: fail(f"{tag}: structured-data telephone must be +91{PRIMARY}")
    other_numbers = set(re.findall(r"(?<!\d)\d{10}(?!\d)", _kh.unescape(re.sub(r"<[^>]+>", " ", raw)))) - {PRIMARY}
    if other_numbers: fail(f"{tag}: other phone-like numbers on page: {sorted(other_numbers)}")

    # no invented prices or figures: the phone number is the only number allowed in visible text/meta
    leftover = re.sub(PRIMARY, "", scan)
    if re.search(r"\d", leftover): fail(f"{tag}: contains numbers other than {PRIMARY} (prices, distances, times, years?): {re.findall(r'.{15}\d+.{10}', leftover)[:3]}")
    for pat, why in BANNED:
        m = re.search(pat, scan, re.I)
        if m: fail(f"{tag}: {why}: {m.group(0)!r}")
    if enquiry_only:
        m = re.search(ENQUIRY_ONLY_BANNED, scan, re.I)
        if m: fail(f"{tag}: claims service availability for an unverified destination: {m.group(0)!r}")
        if "confirm whether we can arrange" not in vis: fail(f"{tag}: enquiry-only page must say availability is confirmed first")
        if "commonly available" in vis: fail(f"{tag}: enquiry-only page must not say vehicles are commonly available")
    else:
        if "subject to availability" not in vis: fail(f"{tag}: must say 'subject to availability'")
    for must in ("Jammu", "Katra", "Udhampur", "partner drivers", "do not publish fares", "no fixed fares", "current rate", "Call or WhatsApp"):
        if must not in vis: fail(f"{tag}: missing required wording {must!r}")
    if re.search(r"\bKudh\b", scan + " " + " ".join(_kh.unescape(j) for j in p.jsonld)): fail(f"{tag}: use 'Kud', never 'Kudh', in written content")

    # structured data
    types = set()
    svc_areas = []
    for j in p.jsonld:
        d = json.loads(j)
        for node in (d if isinstance(d, list) else [d]):
            t = node.get("@type"); types.update(t if isinstance(t, list) else [t])
            if t == "Service": svc_areas = [a if isinstance(a, str) else a.get("name") for a in node.get("areaServed", [])]
            if t == "FAQPage" and len(node.get("mainEntity", [])) < 5: fail(f"{tag}: FAQ schema has fewer than 5 questions")
    for want in ("Service", "FAQPage", "BreadcrumbList", "TravelAgency"):
        if want not in types: fail(f"{tag}: missing {want} structured data")
    if enquiry_only and place in svc_areas: fail(f"{tag}: Service schema must not list {place} as an area served until service there is verified")
    if len(re.findall(r'<details class="faq-item">', raw)) < 5: fail(f"{tag}: visible FAQ has fewer than 5 questions")

    # internal links: valid (also covered globally) and connected both ways
    links = {h.split("#")[0] for h in p.hrefs if h.endswith(".html") or ".html#" in h}
    for need in ("srinagar-taxi.html", "tour-packages.html", "taxi-services.html", "jammu-to-patnitop-taxi.html", "katra-to-patnitop-taxi.html", "udhampur-to-patnitop-taxi.html", "contact.html"):
        if need not in links: fail(f"{tag}: should link to {need}")
    for l in links:
        if not os.path.exists(os.path.join(ROOT, l)): fail(f"{tag}: broken internal link {l}")
    # linked from the page content (not only the footer) of the hub pages, and from every page's footer
    for src in ("index.html", "taxi-services.html", "tour-packages.html"):
        body_part = parsed[src][1][:parsed[src][1].find("<footer")]
        if f'href="{fn}"' not in body_part: fail(f"{fn}: not linked from the content of {src}")
    for src, (sp, sraw) in parsed.items():
        if src in ("local-products-enquiry.html",) or src.startswith("google"): continue
        if f'href="{fn}"' not in sraw and f'href="/{fn}"' not in sraw: fail(f"{fn}: not linked from {src}")
    if not enquiry_only and fn not in {h.split('#')[0] for h in parsed["srinagar-taxi.html"][0].hrefs}: fail(f"{fn}: not linked from srinagar-taxi.html")

    # assistant: listed, and never given a fare
    ar = agent_routes.get(fn)
    if not ar: fail(f"{tag}: missing from js/agent-data.js")
    elif ar.get("quoteEndpoints"): fail(f"{tag}: assistant must not be able to quote a fare here")

print(f"checked {len(parsed)} pages, {len(locs)} sitemap URLs, {len(data['rates'])} verified rates")
if failures:
    print("\nFAILED:"); [print(" -", f) for f in failures]; sys.exit(1)
print("ALL STATIC CHECKS PASSED")
