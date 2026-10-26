#!/usr/bin/env python3
"""Behaviour tests for the photographer portfolio section.

Builds the site in throw-away copies of the project (the real project is never
touched) with different portfolio manifests and checks what the couple-shoot
page shows. Standard library only.   Run:  python3 tests/portfolio.test.py
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "couple-photoshoot-srinagar-patnitop.html"
IG = "https://www.instagram.com/example.photographer/"
passed, failed = 0, []

def check(name, cond, detail=""):
    global passed
    if cond:
        passed += 1
        print(f"  ok   {name}")
    else:
        failed.append(name)
        print(f"  FAIL {name} {detail}")

def make_copy(tmp):
    dst = os.path.join(tmp, "site")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
    return dst

def entry(file, loc="srinagar", **kw):
    e = {"file": file, "location": loc, "alt": f"Couple photoshoot {file}", "approved": True,
         "approved_by": "Test Photographer", "approved_on": "2026-11-01"}
    e.update(kw)
    return e

def build(site, images=(), ig="", files=()):
    """Write a manifest + dummy image files into the copy, build, return (exit code, output, page html)."""
    pdir = os.path.join(site, "images", "photography", "portfolio")
    os.makedirs(pdir, exist_ok=True)
    for f in files:
        with open(os.path.join(pdir, f), "wb") as fh:
            fh.write(b"\xff\xd8\xff\xd9")
    with open(os.path.join(site, "data", "photographer-portfolio.json"), "w", encoding="utf-8") as fh:
        json.dump({"images": list(images)}, fh)
    cfg_path = os.path.join(site, "site.config.json")
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    cfg["photographer_instagram_url"] = ig
    json.dump(cfg, open(cfg_path, "w", encoding="utf-8"))
    env = {k: v for k, v in os.environ.items() if k != "PHOTOGRAPHER_INSTAGRAM_URL"}
    r = subprocess.run([sys.executable, os.path.join(site, "build.py")], capture_output=True, text=True, env=env)
    page = ""
    if r.returncode == 0:
        page = open(os.path.join(site, PAGE), encoding="utf-8").read()
    return r.returncode, r.stdout + r.stderr, page

def portfolio_imgs(page):
    return re.findall(r'<img src="images/photography/portfolio/([^"]+)"', page)

with tempfile.TemporaryDirectory() as tmp:
    site = make_copy(tmp)

    print("No approved photos")
    code, out, page = build(site)
    check("builds cleanly", code == 0, out[-300:])
    check("shows the clean placeholder", 'class="portfolio-placeholder"' in page)
    check("shows no portfolio images", portfolio_imgs(page) == [])
    check("no Instagram link while none is configured", "instagram.com" not in page)

    print("Only unapproved entries")
    code, out, page = build(site, images=[entry("a.jpg", approved=False), entry("b.jpg", approved="yes")], files=["a.jpg", "b.jpg"])
    check("unapproved (false or non-boolean) photos are never shown", code == 0 and portfolio_imgs(page) == [])
    check("placeholder is kept", 'class="portfolio-placeholder"' in page)
    for f in ("a.jpg", "b.jpg"):
        os.remove(os.path.join(site, "images", "photography", "portfolio", f))

    print("Mixed approved and unapproved")
    imgs = [entry("sri-1.jpg", "srinagar", credit="Test Photographer"),
            entry("pat-1.jpg", "patnitop"),
            entry("secret.jpg", "srinagar", approved=False)]
    code, out, page = build(site, images=imgs, ig=IG, files=["sri-1.jpg", "pat-1.jpg", "secret.jpg"])
    check("builds cleanly", code == 0, out[-300:])
    check("shows exactly the approved photos", sorted(portfolio_imgs(page)) == ["pat-1.jpg", "sri-1.jpg"], str(portfolio_imgs(page)))
    check("an unapproved file sitting in the folder is not shown", "secret.jpg" not in page)
    check("placeholder is gone once photos exist", 'class="portfolio-placeholder"' not in page)
    check("photos are grouped under Srinagar and Patnitop", "<h3>Srinagar</h3>" in page and "<h3>Patnitop</h3>" in page)
    check("photos carry alt text", 'alt="Couple photoshoot sri-1.jpg"' in page)
    check("credit shown only when given", page.count("<figcaption>") == 1 and "Photo: Test Photographer" in page)
    check("Instagram profile link is kept, opens safely", f'href="{IG}"' in page and 'rel="noopener noreferrer"' in page)

    print("One location only")
    os.remove(os.path.join(site, "images", "photography", "portfolio", "pat-1.jpg"))
    code, out, page = build(site, images=[entry("sri-1.jpg", "srinagar")], files=["sri-1.jpg"])
    check("a location without photos gets a short note, not a broken grid",
          code == 0 and "Photographs from Patnitop will be added soon." in page and portfolio_imgs(page) == ["sri-1.jpg"])

    print("Mistakes in the approval record stop the build")
    cases = {
        "approved photo whose file is missing": ([entry("ghost.jpg")], []),
        "approved photo without approved_by": ([entry("x.jpg", approved_by="")], ["x.jpg"]),
        "approved photo without alt text": ([entry("x.jpg", alt=" ")], ["x.jpg"]),
        "approved photo without a valid approved_on date": ([entry("x.jpg", approved_on="yesterday")], ["x.jpg"]),
        "approved photo with an unknown location": ([entry("x.jpg", loc="jammu")], ["x.jpg"]),
        "path traversal in file name": ([entry("../../css/style.css")], []),
        "unsupported file type": ([entry("x.gif")], ["x.gif"]),
        "same file listed twice": ([entry("x.jpg"), entry("x.jpg")], ["x.jpg"]),
    }
    for label, (images, files) in cases.items():
        code, out, _ = build(site, images=images, files=files)
        check(label, code != 0, "build unexpectedly succeeded")
        for f in files:
            p = os.path.join(site, "images", "photography", "portfolio", f)
            if os.path.exists(p): os.remove(p)

    print("Instagram link")
    code, out, page = build(site, ig="http://instagram.com/someone")
    check("a non-https link is rejected", code != 0)
    code, out, page = build(site, ig="https://example.com/someone")
    check("a non-Instagram link is rejected", code != 0)
    code, out, page = build(site, ig=IG)
    check("shown in the placeholder state when configured", code == 0 and f'href="{IG}"' in page and 'class="portfolio-placeholder"' in page)

print(f"\n{passed} passed, {len(failed)} failed")
if failed:
    print("FAILED:", *failed, sep="\n - ")
    sys.exit(1)
