# Set up lead tracking from an Android phone (free, no laptop)

You need: your Google account, the Chrome app, about 20 minutes. Everything is free.
Never share a password, OTP or recovery code with anyone, including in a chat with Claude.

**Important first step on Android:** the Apps Script menu does not appear in the Google Sheets *app*. Use the **Chrome** app and turn on **Desktop site**: tap the three dots (top right) → tick **Desktop site**. Use Chrome for every part of this guide, and pinch to zoom when the text is small.

## Part A. Lead sheet (about 12 minutes)

1. In Chrome (Desktop site on) open **sheets.google.com** → **Blank spreadsheet**. Name it **PTH Leads** (tap "Untitled spreadsheet").
2. Get the script text. In a new Chrome tab open this link:
   `https://raw.githubusercontent.com/singhdileep257-hub/patnitop-travels-hub/claude/lead-system-seo-pages/apps-script/lead-receiver.gs`
   Long-press the text → **Select all** → **Copy**.
   (After the PR is merged, replace `claude/lead-system-seo-pages` in the link with `main`.)
   If that link does not open, use this instead: in Chrome open `https://github.com/singhdileep257-hub/patnitop-travels-hub/blob/claude/lead-system-seo-pages/apps-script/lead-receiver.gs` and tap the **copy** icon at the top right of the code box ("Copy raw file").
3. Back in the sheet: **Extensions → Apps Script**. A new tab opens. Delete the sample `function myFunction() {}` text, **paste** your copy, tap the disk icon (**Save**).
4. In the toolbar choose the function **setup** (dropdown next to Run) → **Run**. Tap **Review permissions** → choose your account. If Google says *"Google hasn't verified this app"* this is your own script: tap **Advanced → Go to (project name) → Allow**. Three tabs are created: **Leads**, **Product Enquiries**, **Events**.
5. Choose the function **createDashboardKey** → **Run** → open **Execution log** at the bottom. Copy the line `Dashboard key: ...`. Keep it private (it is your dashboard password). Running it again makes a new key and the old one stops working.
6. **Deploy → New deployment** → gear icon → **Web app**. *Execute as:* **Me**. *Who has access:* **Anyone**. Tap **Deploy**, then **Copy** the Web app URL (it ends with `/exec`).
7. Send that `/exec` URL to Claude in this chat (the URL is not a password; do not send the dashboard key). Claude adds it to the pull request and re-runs the tests. If you would rather do it yourself: open the repository on GitHub in Chrome, open `site.config.json`, tap the pencil, paste the URL as the value of `lead_endpoint`, and commit to the branch `claude/lead-system-seo-pages`. Do not merge.
8. Optional: at the top of the script set `NOTIFY_EMAIL` to your Gmail to receive one email per new enquiry (uses your free quota).

**Test it** (after the site with the URL is live or on the Netlify preview): submit an enquiry on any taxi page with your own number. A row appears in **Leads** with Status **New**. Tap Call and WhatsApp on a page: rows appear in **Events**.

**Daily use:** open the sheet, call the customer, then change the **Status** dropdown: New → Quotation Sent → Follow-up Required → **Confirmed** or Cancelled. A booking is counted as confirmed only when you set Confirmed yourself.

**Already made a Leads sheet earlier with the old script?** Start a fresh sheet for this version, or add the headers *Traffic source, Landing page, Referrer* before the *Internal notes* column.

## Part B. Dashboard

1. After the URL is deployed, open `https://patnitoptravelshub.netlify.app/dashboard.html` in Chrome. (It is hidden from Google and not linked from the site; bookmark it.)
2. Paste your dashboard key → **Load numbers**.
3. For search keywords: Search Console → Performance → **Export** → Download CSV → on the dashboard choose the **Queries.csv** file. It is read on your phone only.

How to read it: *Call button taps* are call attempts, not answered calls. *WhatsApp taps* are chats opened, not messages sent. Neither is a booking. *Genuine leads* means enquiries you have not marked Cancelled.

## Part C. Google Analytics 4 (optional, free)

Status now: **not configured.** `ga4_measurement_id` in `site.config.json` is empty, so the website loads no Google Analytics code at all. Nothing is broken; the lead sheet above works without GA4.

To switch it on: in Chrome (Desktop site) open **analytics.google.com** → **Start measuring** → create an account and property → platform **Web** → site address `https://patnitoptravelshub.netlify.app` → copy the **Measurement ID** (looks like `G-XXXXXXXXXX`). Send the ID to Claude, or paste it into `ga4_measurement_id` on the branch like in step 7. Then in GA4: **Admin → Events** → mark **generate_lead** as a key event. The website already sends `phone_click`, `whatsapp_click`, `email_click` and `generate_lead` as separate events.

## Part D. Search Console (needs you, takes 5 minutes)

After you approve the merge and Netlify deploys: Search Console (Chrome, Desktop site) → **Sitemaps** → add `sitemap.xml` → Submit. Then **URL inspection** → paste each new page address → **Request indexing** (8 pages: jammu-airport-taxi, katra-railway-station-taxi, katra-to-jammu-taxi, tempo-traveller-booking, urbania-booking, glanza-taxi-service, ramban-taxi-service, banihal-taxi-service). Google decides if and when pages are indexed or ranked; nothing here can guarantee that.

## Business Profile (not touched)
Nothing was changed on your Business Profile. If you decide to, you can set the profile's Website link to `https://patnitoptravelshub.netlify.app/?utm_source=google&utm_medium=organic&utm_campaign=gbp` so visits from the profile show up as *google_business_profile* on the dashboard. This is your decision, and you make the edit.
