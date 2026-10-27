# SEO coverage review, 27 Oct 2026

Scope: Patnitop, Kud, Katra, Sanasar, Udhampur and Kashmir taxi tours.
Method: read from the generated pages, `sitemap.xml` and `robots.txt` in this branch.

**This is a review of what the site contains, not of how it performs.** It makes no claim
about Google rankings, impressions, clicks, traffic or indexing. Those numbers exist only in
Google Search Console (Performance and Pages reports) and Google Business Profile Insights.
Nothing here was measured from Google.

## What is in place (verified in source)

| Target | Page | In sitemap | Title / H1 names the place | FAQ + breadcrumb schema |
|---|---|---|---|---|
| Patnitop | `index.html`, `taxi-services.html`, `patnitop-sightseeing.html`, `things-to-do-in-patnitop.html` | yes | yes | yes (home: FAQ + WebSite) |
| Kud | `kudh-to-patnitop-taxi.html` | yes | "Kud to Patnitop Taxi" | yes |
| Katra | `katra-to-patnitop-taxi.html` | yes | yes | yes |
| Udhampur | `udhampur-to-patnitop-taxi.html` | yes | yes | yes |
| Sanasar | `nathatop-sanasar-taxi.html` (shared with Nathatop) | yes | yes, in title and H1 | yes |
| Srinagar / Kashmir | `srinagar-taxi.html`, `tour-packages.html`, `couple-photoshoot-srinagar-patnitop.html` | yes | yes | Srinagar and photo page: yes. Tour packages: breadcrumb only |

Also confirmed: every indexable page has one H1, a canonical URL on the Netlify address, and a
sitemap entry; `robots.txt` points at the sitemap; the local-products page is `noindex`.
Visible text uses "Kud", never "Kudh". Only the file name `kudh-to-patnitop-taxi.html` keeps the
old spelling, deliberately, so the existing URL is not broken.

## Gaps and opportunities (none applied in this PR)

1. **Kashmir taxi tours are the thinnest area.** `tour-packages.html` (about 330 words) lists
   Srinagar, Gulmarg, Pahalgam, Sonamarg, Doodhpathri and Yusmarg as plain words, with no page
   of their own and no FAQ or Service schema. Someone searching "Srinagar to Gulmarg taxi" has no
   matching page. Suggested next step: one page per destination or a Srinagar sightseeing page,
   written only from facts you confirm (routes, how you operate). No invented prices, timings or
   itineraries.
2. **Sanasar has no page of its own.** It shares a page with Nathatop. That can serve both
   searches, but a "Sanasar taxi" query competes against pages built just for it.
3. **Route pages are short** (about 400 to 430 words each for Katra, Udhampur, Kud, Chenani,
   Jammu). Adding verified, specific detail (pickup points, typical route stops you actually
   serve, common questions customers ask you) would help more than adding keywords.
4. **Meta descriptions are similar to each other** ("Call or WhatsApp 9103331334 for fare and
   availability"). Making each distinct is a low-risk improvement.
5. **`tour-packages.html`, `vehicles.html` and `contact.html` have no Service or FAQ schema.**
6. **Internal links are mostly header/footer links.** Every page has the same 23 sitewide links;
   contextual links in body text between related pages (for example Sanasar to Nathatop to
   Kud) are fewer. Adding a few helps Google see which pages relate.
7. **Off-site signals cannot be judged from the code.** `gbp_maps_url` and `gbp_review_url` in
   `site.config.json` are still empty, and the site runs on a `netlify.app` address, since the
   custom domain is not live. A verified Google Business Profile with real reviews and a
   verified Search Console property are the next real signals. Only genuine reviews should be used.

## What to check in Search Console (no guessing)

- Pages report: are the 23 sitemap URLs "Indexed", and why not if any are excluded?
- Performance report: real queries and pages for Patnitop, Kud, Katra, Sanasar, Udhampur and Srinagar.
- Sitemaps report: is `sitemap.xml` submitted and read without errors?
