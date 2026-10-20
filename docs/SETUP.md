# Patnitop Travels Hub — setup, deploy and daily use

Everything below is free. Nothing is required for the site to work: with no setup at all, every button, form and the chat assistant still end in a real phone call or WhatsApp message to 9103331334. Each step below switches on one extra feature.

## How the site is built

The pages are generated. **Do not edit the `.html` files by hand** — they are overwritten.

| You want to change | Edit this | Then run |
|---|---|---|
| Page text, FAQs, routes, vehicles | `build.py` | `python3 build.py` |
| Site address, Google Analytics ID, lead sheet link | `site.config.json` | `python3 build.py` |
| Fares the assistant may quote | `data/rates.json` | `python3 build.py` |
| Colours, layout | `css/style.css` | nothing |

Commit the regenerated files together with your edit. Netlify publishes the repository root as-is (there is no build step on Netlify).

## Check your work before publishing

```
python3 build.py
python3 tests/check_site.py                                   # pages, SEO, links, sitemap, no invented claims
node tests/lead-receiver.test.js                              # lead sheet script
cd tests && npm install && npx playwright install chromium && node agent.test.js   # real-browser tests
```

## 1. Deploy (Netlify)

1. Review the branch `claude/complete-site-and-agent` on GitHub and merge it into `main` when you are happy.
2. Netlify (already linked to this repository) publishes `main` automatically. Nothing else to configure; `netlify.toml` publishes the repository root.
3. After deploy, open the live site and test: tap Call, tap WhatsApp, open the chat (round button, bottom right), and open `/privacy.html` and `/sitemap.xml`.

## 2. Domain: `www.patnitoptravelshub.com`

`site_url` in `site.config.json` is currently the Netlify address, because the real domain does not point at the site yet. Canonical links, the sitemap, `robots.txt` and structured data all follow `site_url`. When the domain is live and working with HTTPS:

1. In Netlify: Domain management → add the custom domain and follow its DNS instructions.
2. Change `site_url` to `https://www.patnitoptravelshub.com`, run `python3 build.py`, commit, push.
3. Search Console: add the new address as a property, submit `https://www.patnitoptravelshub.com/sitemap.xml`.

Do not switch `site_url` before the domain works, or Google is told to index addresses that do not load.

## 3. Google Search Console and Google Business Profile (the biggest lever for local searches)

* Search Console: the site already carries your verification meta tag and file. Submit `<site_url>/sitemap.xml`, then use *URL inspection → Request indexing* on the home page and on each route page (Katra, Jammu, Udhampur, Chenani, Kudh).
* **Google Business Profile** matters more than anything on the website for "taxi near me" and map results. Create or claim the profile for Patnitop Travels Hub, use the exact same name, phone (9103331334) and website, pick the category *Taxi service*, add real photos of your own vehicles, and ask real customers for reviews. The website cannot do this for you, and it never shows reviews that do not exist.

## 4. Lead sheet: store enquiries and track status (free)

Enquiries from the chat and forms can be saved to a private Google Sheet you own. Without this step they only go to WhatsApp.

1. Create a new Google Sheet (name it e.g. *PTH Leads*).
2. Extensions → Apps Script. Delete the sample code and paste in the whole of `apps-script/lead-receiver.gs`. Save.
3. Choose the function `setup` and click Run. Approve the permission prompt (it only touches this sheet). Two tabs appear: **Leads** and **Product Enquiries**.
4. Deploy → New deployment → type *Web app*. *Execute as: Me. Who has access: Anyone.* Deploy and copy the Web app URL (ends in `/exec`).
5. Paste that URL into `lead_endpoint` in `site.config.json`, run `python3 build.py`, commit and push.
6. Test: submit the contact form with your own number. A row should appear within a few seconds with Status **New**.

Status column (a dropdown you change by hand): **New → Quotation Sent → Follow-up Required → Confirmed / Cancelled**. The website can only ever create **New**; it cannot mark anything Confirmed. Only people who can open the sheet see customer details, and the sheet is not published anywhere.

Optional: set `NOTIFY_EMAIL` at the top of the script to get one email per new lead.

If you change the script later: Deploy → Manage deployments → edit → New version.

Follow-up: the site never messages customers by itself. A customer who ticks *"you may follow up"* has said you can call or WhatsApp them about that enquiry. The sheet's **Follow-up consent** column shows who agreed — only follow up where it says Yes (a customer who messages you first on WhatsApp has of course started that conversation themselves).

## 5. Fares the assistant may quote

`data/rates.json` ships **empty**, so the assistant currently quotes **no prices at all** and tells customers you will confirm the fare. To let it quote a fare, add an entry you have personally verified:

```json
{ "route_id": "katra", "vehicle": "Dzire", "trip_type": "one-way", "amount_inr": 0,
  "includes": "what the fare covers, e.g. tolls and waiting included or not",
  "verified_on": "2026-10-20", "verified_by": "Dileep Singh" }
```

Use your real figure in place of `0`. The build stops with a clear message if an entry is incomplete. A rate older than 90 days is not quoted, so refresh `verified_on` when you re-check fares. Allowed `route_id`, `vehicle` and `trip_type` values are listed at the top of the file.

## 6. Conversion tracking (Google Analytics 4, free)

1. Create a GA4 property and copy its Measurement ID (`G-XXXXXXXXXX`).
2. Put it in `ga4_measurement_id` in `site.config.json`, run `python3 build.py`, commit, push. Until then no analytics script loads, and the privacy page says so.
3. In GA4 → Admin → Events, mark these as **key events**: `phone_click`, `whatsapp_click`, `generate_lead`, `quote_request`, `product_enquiry`.

Each carries `link_location` (header, hero, mobile_bar, agent, footer, content) so you can see which button works. **Confirmed bookings cannot be tracked from the website** because they are confirmed on a call or WhatsApp — count them by setting Status = Confirmed in the lead sheet. Phone and WhatsApp taps are counted as *taps*, not completed calls.

If you later use Google Ads call tracking or a cookie/consent banner, update `privacy.html` (in `build.py`) first.

## 7. Local products

`/local-products-enquiry.html` is an enquiry form only (honey, dry fruits, rajma, handicrafts, gift hampers). It has **no prices, stock or cart**, is marked *noindex*, and is not linked from the menu or sitemap, so it is not advertised as a shop. It is reachable through the chat assistant ("Local Products Enquiry"). When your catalogue, prices, stock and order process are verified, set `indexable_products_page` to `true` and build a proper shop page.

## 8. What needs real photos and real facts from you

* Real photos of your vehicles and Patnitop (the site deliberately has none; see `images/README.txt`). Add them, with `alt` text.
* Your exact street/landmark address and, if you want, opening hours, for the business schema and Google Business Profile.
* Real customer reviews, from Google, once you have them.
