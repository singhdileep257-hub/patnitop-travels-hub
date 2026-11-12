#!/usr/bin/env python3
"""Tests the REAL Netlify behaviour for every URL in sitemap.xml, so canonical and sitemap URLs are
changed only on evidence.   python3 tests/check_live_urls.py [https://your-site.netlify.app]

For each sitemap URL it reports (without following redirects):
  * the status of the .html URL itself (200 = served as-is, 301/308 = Netlify "Pretty URLs" is redirecting)
  * the status of the clean variant (/taxi-services) and where it goes
  * whether the page's <link rel=canonical> equals the sitemap URL
Verdict: if every .html URL is 200 and canonicals match, the current canonicals/sitemap are correct and
nothing should change. If .html URLs redirect to clean URLs, switch canonicals + sitemap to the clean form.
Standard library only; read-only GET requests."""
import re, sys, json, os, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
configured = json.load(open(os.path.join(ROOT, "site.config.json")))["site_url"].rstrip("/")
site = (sys.argv[1] if len(sys.argv) > 1 else configured).rstrip("/")   # pass a deploy-preview URL to test it instead

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
opener = urllib.request.build_opener(NoRedirect)

def get(url):
    try:
        r = opener.open(urllib.request.Request(url, headers={"User-Agent": "ptv-url-check"}), timeout=20)
        return r.status, r.headers.get("Location", ""), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", ""), ""
    except Exception as e:
        return 0, str(e), ""

locs = re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read())
bad, redirected, unreachable = [], [], 0
for u in locs:
    path = u.replace(configured, "") or "/"
    code, loc, body = get(site + path)
    if code == 0: unreachable += 1; print(f"UNREACHABLE {path}: {loc}"); continue
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', body)
    line = f"{code} {path}"
    if code in (301, 302, 307, 308): redirected.append(path); line += f" -> {loc}"
    elif code != 200: bad.append(path); line += "  (unexpected status)"
    elif canon and canon.group(1) != u:  # canonical is expected to be the configured address bad.append(path); line += f"  canonical mismatch: {canon.group(1)}"
    if path.endswith(".html"):
        c2, l2, _ = get(site + path[:-5]); line += f" | clean variant: {c2}" + (f" -> {l2}" if l2 else "")
    print(line)
print()
if unreachable: print(f"Could not reach {unreachable} URL(s): run this from a machine with internet access."); sys.exit(2)
if redirected: print(f"{len(redirected)} .html URL(s) redirect: switch canonicals and sitemap to the redirect target."); sys.exit(1)
if bad: print("Problems:", bad); sys.exit(1)
print("All sitemap URLs return 200 and match their canonical: current canonicals/sitemap are correct, change nothing.")
