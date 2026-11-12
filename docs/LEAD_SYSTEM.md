# Lead system: what was built and the 4 things only you can switch on

Goal: genuine taxi calls first, WhatsApp second, form third. Nothing here is paid.

## What the website does now (already in the code)

| Feature | Where |
|---|---|
| Call Now (9103331334) in the header, in the page content and in a sticky bottom bar on phones, before WhatsApp everywhere | every page |
| Taxi enquiry form: name, mobile, pickup, destination, travel date, passengers, vehicle (Dzire, Ertiga, Glanza, Innova / Toyota Crysta, Tempo Traveller, Urbania) | every route / location / vehicle page (25 pages) and `contact.html` |
| After a form submit the customer sees **Call** first, then WhatsApp with the details pre-filled | route pages |
| Call, WhatsApp and email taps recorded **separately** from form enquiries, with the page, button position and traffic source | all pages |
| Traffic source (google_organic, google_business_profile, direct, social, referral) captured on landing and attached to every enquiry and tap | all pages |
| Owner dashboard `dashboard.html` (private: noindex, unlinked, not in the sitemap, counts only, unlocked with a key) | new |
| "Confirmed bookings" exist only when **you** change Status to Confirmed in the sheet. The website can never create one | lead sheet |

New landing pages: Jammu Airport Taxi, Katra Railway Station Taxi, Katra to Jammu Taxi, Tempo Traveller Booking, Urbania Booking, Glanza Taxi Service, Ramban Taxi Service, Banihal Taxi Service. The combined `airport-railway-transfer.html` is kept and now links to the two dedicated pages. No fares, distances, journey times or seat counts are published on any of them.

## The 4 things only you can do (they need your Google accounts)

I cannot sign in to your Google or Netlify accounts, and I will never ask for a password, OTP or recovery code.

1. **Create the lead sheet (10 minutes, free).** Follow `docs/ANDROID_SETUP.md` (phone) or section 4 of `docs/SETUP.md` (computer): new Google Sheet, Extensions, Apps Script, paste `apps-script/lead-receiver.gs`, run `setup`, then run `createDashboardKey` and read the key in View, Logs. Deploy as a Web app (Execute as: Me, Access: Anyone). Copy the `/exec` URL.
2. **Create the free GA4 property** at analytics.google.com, add a Web data stream for the Netlify address, and copy the Measurement ID (looks like `G-XXXXXXXXXX`). In GA4, Admin, Events, mark `generate_lead` as a key event.
3. **Put both values in `site.config.json`** (`ga4_measurement_id`, `lead_endpoint`) and tell me, or run `python3 build.py` yourself. Nothing else needs editing; the privacy page text updates by itself.
4. **Search Console:** submit `https://patnitoptravelshub.netlify.app/sitemap.xml` (Indexing, Sitemaps) and use URL Inspection, Request indexing, on the 8 new pages.

## Dashboard
Open `/dashboard.html` on your phone, enter the key from step 1, tap Load numbers. For Google search keywords: Search Console, Performance, Export, download Queries.csv, then choose that file on the dashboard (read on your device only).

## Honest limits
- Call and WhatsApp taps show interest. They are not answered calls and never count as bookings.
- Google does not tell websites which keyword a visitor searched; keywords come only from Search Console.
- "Genuine leads" means enquiries you have not marked Cancelled. Only you can judge genuineness, by calling back.
- Anyone could tap a button repeatedly, so treat tap counts as a trend, not an exact figure.
- If you already created a Leads sheet with the older script, add the three new column headers (Traffic source, Landing page, Referrer) before Internal notes, or start a fresh sheet.

## Google Business Profile (needs your approval, nothing changed yet)
Use the website link `https://patnitoptravelshub.netlify.app/?utm_source=google&utm_medium=organic&utm_campaign=gbp`. Calls and website visits from the profile then show up as google_business_profile on the dashboard. Keep category, 24-hour opening hours, 9103331334 and service areas (including Gaurikund) as already decided.
