# Google Search Console: get the new pages indexed (Android phone, free)

Do this only AFTER you have approved the merge and Netlify has deployed. Google can only index pages that are live.
Google decides whether and when to index or rank a page. Requesting indexing asks Google to look; it does not guarantee a place in results.

Use Chrome with **Desktop site** ticked (three dots → Desktop site). Search Console is much easier to use that way.

## A. One-time: prove the site is yours
1. Open `search.google.com/search-console` and sign in with the Google account you want to own it.
2. **Add property** → choose **URL prefix** → type `https://patnitoptravelshub.netlify.app/` → **Continue**.
3. Verification: your site already contains a Google verification tag (and a verification file). Choose **HTML tag** or **HTML file** if asked and tap **Verify**. If Google says it is not found, the live site must be deployed from this repository first.

## B. Submit the sitemap
1. Left menu (tap the ☰ icon) → **Sitemaps**.
2. In "Add a new sitemap" type `sitemap.xml` → **Submit**.
3. Status should become **Success** and show **36 discovered pages**. "Couldn't fetch" at first can be normal; wait a few minutes and refresh.

## C. Request indexing for the important pages (one at a time)
1. Tap the search box at the top ("Inspect any URL in …") and paste the full page address, for example `https://patnitoptravelshub.netlify.app/jammu-airport-taxi.html` → Enter.
2. Wait for the result:
   - **"URL is on Google"** → nothing to do.
   - **"URL is not on Google"** → tap **Request indexing**. Wait for "Indexing requested" and tap **Got it**.
3. Repeat for these pages, most important first (Google limits how many requests you can make per day, so do a few each day):
   1. `https://patnitoptravelshub.netlify.app/` (home)
   2. `https://patnitoptravelshub.netlify.app/jammu-to-patnitop-taxi.html`
   3. `https://patnitoptravelshub.netlify.app/katra-to-patnitop-taxi.html`
   4. `https://patnitoptravelshub.netlify.app/udhampur-to-patnitop-taxi.html`
   5. `https://patnitoptravelshub.netlify.app/jammu-airport-taxi.html`
   6. `https://patnitoptravelshub.netlify.app/katra-railway-station-taxi.html`
   7. `https://patnitoptravelshub.netlify.app/katra-to-jammu-taxi.html`
   8. `https://patnitoptravelshub.netlify.app/tempo-traveller-booking.html`
   9. `https://patnitoptravelshub.netlify.app/urbania-booking.html`
   10. `https://patnitoptravelshub.netlify.app/glanza-taxi-service.html`
   11. `https://patnitoptravelshub.netlify.app/ramban-taxi-service.html`
   12. `https://patnitoptravelshub.netlify.app/banihal-taxi-service.html`
   13. `https://patnitoptravelshub.netlify.app/patnitop-sightseeing.html`
   14. `https://patnitoptravelshub.netlify.app/taxi-services.html`
   Do not request indexing for `dashboard.html`: it is private on purpose.

## D. Check structured data (free, 2 minutes per page)
Open `search.google.com/test/rich-results`, paste a page address, tap **Test URL**. You should see **Local business** (and **Breadcrumbs**) detected with no errors. Warnings about optional fields are normal. FAQ and TaxiService items do not produce special search-result features for a site like this; they are still valid and harmless.

## E. Check again after a few days
- **Pages** (left menu → Indexing → Pages): see how many pages are indexed and the reason for any that are not. "Crawled – currently not indexed" or "Discovered – currently not indexed" on a new page usually just means Google has not got to it yet; improve the page and wait rather than re-requesting repeatedly.
- **Performance** → **Search results**: after Google starts showing the site you will see queries, clicks, impressions and positions. Export the Queries CSV to read it on the lead dashboard.
- Send Claude the Pages list, the Sitemaps status and the Queries export and it will write the real audit.
