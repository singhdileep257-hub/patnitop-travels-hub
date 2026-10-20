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
        if num not in ("919103331334", "918493988568"): fail(f"{n}: unexpected phone number {num}")
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

print(f"checked {len(parsed)} pages, {len(locs)} sitemap URLs, {len(data['rates'])} verified rates")
if failures:
    print("\nFAILED:"); [print(" -", f) for f in failures]; sys.exit(1)
print("ALL STATIC CHECKS PASSED")
