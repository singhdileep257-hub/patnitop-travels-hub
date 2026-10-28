#!/usr/bin/env python3
"""Proves the Kashmir taxi page checks in check_site.py really catch problems.

For each case it copies the built site into a throw-away folder, injects one
problem (a price, a second phone number, a permit claim, a broken link and so
on), runs tests/check_site.py there, and requires it to FAIL. A final case
requires the untouched copy to PASS. The real project is never modified.
Standard library only.   Run:  python3 tests/kashmir_pages.test.py
"""
import os, re, shutil, subprocess, sys, tempfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://patnitoptravelshub.netlify.app"
passed, failed = 0, []


def fresh(tmp):
    d = os.path.join(tmp, "c")
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(SRC, d, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
    return d


def edit(d, f, old, new, count=1):
    p = os.path.join(d, f)
    s = open(p, encoding="utf-8").read()
    if old not in s:
        raise AssertionError(f"mutation anchor not found in {f}: {old[:60]!r}")
    open(p, "w", encoding="utf-8").write(s.replace(old, new, count))


def edit_all(d, f, old, new):
    p = os.path.join(d, f)
    s = open(p, encoding="utf-8").read()
    if old not in s:
        raise AssertionError(f"mutation anchor not found in {f}: {old[:60]!r}")
    open(p, "w", encoding="utf-8").write(s.replace(old, new))


def run_checks(d):
    r = subprocess.run([sys.executable, os.path.join(d, "tests", "check_site.py")], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _allow_agent_quote(d):
    p = os.path.join(d, "js", "agent-data.js")
    s = open(p, encoding="utf-8").read()
    i = s.index('"id": "gulmarg"')
    j = s.index('"quoteEndpoints": null', i)
    open(p, "w", encoding="utf-8").write(s[:j] + '"quoteEndpoints": [["jammu"], ["gulmarg"]]' + s[j + len('"quoteEndpoints": null'):])


CASES = [
    ("a price in the text",
     lambda d: edit_all(d, "gulmarg-taxi.html", "for the current rate.</p>", "for the current rate. Fares start at ₹4500.</p>"), "gulmarg-taxi.html"),
    ("a distance or other number in the text",
     lambda d: edit_all(d, "pahalgam-taxi.html", "Route, timing and number of days planned", "About 300 km. Route, timing and number of days planned"), "pahalgam-taxi.html"),
    ("a different phone number on a call button",
     lambda d: edit(d, "sonamarg-taxi.html", 'tel:+919103331334" class="btn btn-pine"', 'tel:+919999999999" class="btn btn-pine"'), "sonamarg-taxi.html"),
    ("a permit claim in the intro",
     lambda d: edit_all(d, "gulmarg-taxi.html", "before anything is booked.</p>", "before anything is booked. We hold all required permits.</p>"), "gulmarg-taxi.html"),
    ("a vehicle-ownership claim in visible text",
     lambda d: edit_all(d, "sonamarg-taxi.html", "using our vehicles and partner drivers", "using all our vehicles and partner drivers"), "sonamarg-taxi.html"),
    ("a vehicle-ownership claim only inside the FAQ structured data",
     lambda d: edit(d, "pahalgam-taxi.html", "partner drivers, depending", "partner drivers, and every vehicle is ours, depending"), "pahalgam-taxi.html"),
    ("an availability claim on Doodhpathri",
     lambda d: edit_all(d, "doodhpathri-taxi.html", "Interested in Doodhpathri?", "We provide daily service to Doodhpathri. Interested in Doodhpathri?"), "doodhpathri-taxi.html"),
    ("Doodhpathri listed as an area served in the Service schema",
     lambda d: edit(d, "doodhpathri-taxi.html", '"areaServed": ["Jammu","Katra","Udhampur"]', '"areaServed": ["Doodhpathri","Jammu","Katra","Udhampur"]'), "doodhpathri-taxi.html"),
    ("a local sightseeing claim",
     lambda d: edit_all(d, "yusmarg-taxi.html", "We do not publish fares", "Local sightseeing is included. We do not publish fares"), "yusmarg-taxi.html"),
    ("'Kudh' in written content",
     lambda d: edit_all(d, "yusmarg-taxi.html", "We do not publish fares", "Also see our Kudh taxi. We do not publish fares"), "yusmarg-taxi.html"),
    ("a missing sitemap entry",
     lambda d: edit(d, "sitemap.xml", f"<loc>{SITE}/yusmarg-taxi.html</loc>", f"<loc>{SITE}/yusmarg-taxi-x.html</loc>"), "sitemap"),
    ("a wrong canonical URL",
     lambda d: edit(d, "pahalgam-taxi.html", f'rel="canonical" href="{SITE}/pahalgam-taxi.html"', f'rel="canonical" href="{SITE}/pahalgam.html"'), "canonical"),
    ("a broken internal link",
     lambda d: edit(d, "gulmarg-taxi.html", 'href="pahalgam-taxi.html"', 'href="pahalgam-taxi-old.html"'), "broken internal link"),
    ("a missing link from the home page",
     lambda d: edit(d, "index.html", '<span><a href="sonamarg-taxi.html">Sonamarg</a></span>', "<span>Sonamarg</span>"), "not linked from the content of index.html"),
    ("a missing footer link on one page",
     lambda d: edit(d, "faq.html", '<li><a href="yusmarg-taxi.html">Yusmarg Taxi</a></li>', ""), "yusmarg-taxi.html: not linked from faq.html"),
    ("the assistant being allowed to quote a fare",
     lambda d: _allow_agent_quote(d), "assistant must not be able to quote"),
]

with tempfile.TemporaryDirectory() as tmp:
    print("Untouched site")
    code, out = run_checks(fresh(tmp))
    if code == 0:
        passed += 1
        print("  ok   passes with no changes")
    else:
        failed.append("untouched site")
        print("  FAIL untouched site does not pass:\n" + out[-600:])

    print("Injected problems must be caught")
    for name, mutate, expect in CASES:
        d = fresh(tmp)
        try:
            mutate(d)
        except AssertionError as e:
            failed.append(name)
            print(f"  FAIL {name}: test setup problem: {e}")
            continue
        code, out = run_checks(d)
        if code != 0 and expect.lower() in out.lower():
            passed += 1
            print(f"  ok   catches {name}")
        elif code != 0:
            failed.append(name)
            print(f"  FAIL {name}: failed, but not for the expected reason ({expect!r}):\n" + "\n".join(out.splitlines()[-4:]))
        else:
            failed.append(name)
            print(f"  FAIL {name}: NOT caught")

print(f"\n{passed} passed, {len(failed)} failed")
if failed:
    print("FAILED:", *failed, sep="\n - ")
    sys.exit(1)
