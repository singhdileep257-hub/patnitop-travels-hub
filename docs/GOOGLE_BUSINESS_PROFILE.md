# Google Business Profile for Patnitop Travels Hub — step by step (phone)

A Google Business Profile (GBP) is what appears in Google Maps and the local results for searches like "Patnitop taxi" and "taxi near me". It is free. **It can only be created and verified by you, from your own Google account**, because Google must confirm you really run the business. Nobody else (including me) can do that step for you.

Google's own rules are at <https://support.google.com/business/answer/3038177>. What matters for you:

* **Only one profile per business.** Do not make a second one "to be safe" — duplicates are suppressed and can get both profiles in trouble.
* **Business name = your real-world name**, exactly as on your signboard, visiting card or vehicle branding. Do **not** add keywords, places or services ("Patnitop Travels Hub – Best Taxi in Patnitop, Katra, Jammu" would be a violation and can get the profile suspended).
* **Phone number must be one you control directly**, not one that redirects to another number: use **9103331334**.
* **Website must be your own site**, not a social-media page. Use the live website link.
* **No links in the business description.**
* **No fake or bought reviews, and no reviews from you or your family.** Reviews are only valuable (and only allowed) when they come from real customers.
* **No promise of ranking.** Google decides what appears and where. A complete, accurate, active profile with genuine reviews gives you the best honest chance.

## Step 0 — check whether a profile already exists (2 minutes)

1. Open the **Google Maps** app, search **Patnitop Travels Hub**, and also your phone number **9103331334**.
2. If a listing for your business already appears, **do not create a new one**. Tap it → **Claim this business** (or **Own this business?**) and follow the prompts. If someone else already owns it, Google lets you *request access*; the owner has 3 days to respond.
3. Only if nothing for your business exists, continue with Step 1.

## Step 1 — create the profile (10 minutes)

1. Sign in to Google on your phone with the account you want to own the business long-term (a Gmail you will keep — `patnitoptravelshub@gmail.com` is a sensible choice if you control it).
2. Open <https://business.google.com/create> in your phone browser (or in Google Maps: tap your profile picture → **Your Business Profile** → **Add your business**).
3. **Business name:** type exactly your real-world name. *(Confirm what is on your signboard/branding before typing — "Patnitop Travels Hub" is what the website uses.)*
4. **Category:** choose **Taxi service** as the main category. You can add more later (for example *Travel agency* or *Tour operator*) only if they are really true of what you do.
5. **Do you have a location customers can visit?**
   * If customers **do not** come to an office/shop but you **travel to them** (pick-ups, drop-offs): choose **No / I deliver goods and services to my customers**. This makes you a *service-area business*; Google asks you to **hide your address**.
   * If you have a real, staffed office or stand customers visit during set hours, you may show that address. Do **not** use a made-up or virtual address.
6. **Service areas:** add the places you actually serve, for example *Patnitop, Kud, Chenani, Udhampur, Katra*. Google advises that a service area should not extend much beyond about **2 hours' driving** from your base, so keep the list realistic (add farther towns like Jammu only if you can genuinely serve them from your base).
7. **Contact details:** phone **9103331334**, website: your live website address (see the link in the final report, or the address in `site.config.json`).
8. Add your real **opening hours** (or "open 24 hours" only if that is true — customers will call and expect an answer).
9. Continue to verification.

## Step 2 — verify (Google decides the method)

Google shows only the verification options it will accept for your business. Typical options are a **video recording**, a **phone call or text**, **email**, or a **postcard** — you can use only what the screen offers.

* **Video:** Google asks you to record a continuous video showing your real vehicle(s) (number plate, branding), the area where you operate, and proof you manage the business (for example a document with the business name, or you operating from the base). Keep it continuous, do not edit it, and follow the on-screen list exactly.
* **Postcard:** only available when Google offers it; it can take about a week to arrive. **Do not request a second code before the first arrives** — it may cancel the first.
* If verification is refused, read the reason on screen; do not create a new profile. Ask in the Business Profile Help community or contact Google support from the profile's **Help** menu.

When the status shows **Verified**, the profile is live (updates can take a few days to appear everywhere).

## Step 3 — complete the profile with real information

* **Description** (up to 750 characters, plain text, no links, no phone number): describe truthfully what you do — for example taxi service for tourists and local travel in Patnitop, Kud, Chenani, Udhampur, Katra and Jammu, with sightseeing and hotel booking help. Say nothing you cannot deliver.
* **Services:** add the services you really provide (Patnitop taxi, airport/railway transfers, sightseeing taxi, hotel booking assistance).
* **Photos:** your **own** vehicles, drivers (with their permission), and real trips. Avoid stock or downloaded photos. Add photos regularly.
* **Phone:** 9103331334 (primary). Do not add a number that forwards elsewhere.
* **Do not list prices you have not verified.**
* **Posts/updates:** occasional real updates (road/weather notes, availability) keep the profile active.

## Step 4 — get genuine reviews (the biggest honest lever)

1. In your profile choose **Get more reviews** / **Share review form** to get your real review link.
2. Send it to **real customers after a completed trip**, politely, by WhatsApp. Ask for an honest review — do not offer money, gifts or discounts for reviews, do not ask only happy customers, and never write or buy reviews yourself.
3. Reply to every review, good or bad, politely and truthfully.

## Step 5 — connect the profile to the website

1. In your profile, tap **Share profile** and copy the **Maps link** and the **review link**.
2. Put them in `site.config.json`:

   ```json
   "gbp_maps_url": "https://maps.app.goo.gl/…your real link…",
   "gbp_review_url": "https://g.page/r/…your real review link…/review"
   ```
3. Run `python3 build.py`, commit and push (or ask me to do it). This adds "View on Google Maps" and "Review us on Google" buttons to the contact page, a Maps link in the footer, and your profile as `sameAs` / `hasMap` in the site's structured data. Until you do this, none of those appear, so no empty or fake links are shown.

## Step 6 — Search Console (also free, also needs your Google account)

The site already carries your Search Console verification tag and file. In Search Console:

1. Add the property for the live site address and confirm it shows **Verified**.
2. **Sitemaps → Add** `sitemap.xml`.
3. **URL inspection** → paste each of these and press **Request indexing** (a few per day is fine): home page, `taxi-services.html`, `katra-to-patnitop-taxi.html`, `jammu-to-patnitop-taxi.html`, `udhampur-to-patnitop-taxi.html`, `chenani-to-patnitop-taxi.html`, `kudh-to-patnitop-taxi.html`, `contact.html`.
4. Check back in a few days under **Pages** for any "not indexed" reasons.

## What not to do

Do not create more than one profile, buy or exchange reviews, use a fake or borrowed address, add keywords to the business name, list places you cannot serve, use a call-forwarding number, or ask anyone to "boost" your ranking — all of these can get the profile suspended and none of them is needed.
