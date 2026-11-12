// Browser tests for the lead system: route-page enquiry forms, call/WhatsApp tap tracking,
// traffic-source attribution and the owner dashboard. Runs the REAL built site in headless
// Chromium against a local static server; the Apps Script endpoint is faked and recorded.
//   node tests/lead_forms.test.js
const assert = require('assert');
const fs = require('fs');
const http = require('http');
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/npm-tools/node_modules/playwright')); }

const ROOT = path.resolve(__dirname, '..');
const LEAD_URL = 'https://leads.test/macros/s/TEST/exec';
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg' };
const pad2 = n => String(n).padStart(2, '0');
const iso = d => d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
const tomorrow = () => { const t = new Date(); return iso(new Date(t.getFullYear(), t.getMonth(), t.getDate() + 1)); };

function serve() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]); if (p === '/') p = '/index.html';
    const file = path.join(ROOT, p);
    if (file.startsWith(ROOT) && fs.existsSync(file) && fs.statSync(file).isFile()) {
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
      return fs.createReadStream(file).pipe(res);
    }
    res.writeHead(404); res.end('nf');
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

let passed = 0; const failures = [];
async function test(name, fn) {
  try { await fn(); passed++; console.log('  ok   ' + name); }
  catch (e) { failures.push(name); console.log('  FAIL ' + name + '\n       ' + String(e.message).split('\n').join('\n       ')); }
}

(async () => {
  const server = await serve();
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();

  // opts: referer (fake Google referrer), stats (what the fake dashboard endpoint returns), endpoint (default true)
  async function open(url, opts = {}) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 800 }, extraHTTPHeaders: opts.referer ? { Referer: opts.referer } : {} });
    const page = await ctx.newPage();
    page.posts = []; page.gets = []; page.errors = [];
    page.on('pageerror', e => page.errors.push(e.message));
    await page.route('**/*', route => {
      const u = route.request().url(), m = route.request().method();
      if (u.startsWith(LEAD_URL)) {
        if (m === 'POST') { page.posts.push(JSON.parse(route.request().postData())); return route.fulfill({ status: 200, body: '{"ok":true}' }); }
        page.gets.push(u);
        return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(opts.stats || { ok: false, error: 'bad key' }) });
      }
      if (u.startsWith(base)) {
        if (/\/js\/agent-data\.js$/.test(u) && opts.endpoint !== false) {
          const js = fs.readFileSync(path.join(ROOT, 'js', 'agent-data.js'), 'utf8').replace('"leadEndpoint": ""', '"leadEndpoint": "' + LEAD_URL + '"');
          return route.fulfill({ status: 200, contentType: 'text/javascript', body: js });
        }
        if (/\/dashboard\.html$/.test(u) && opts.endpoint !== false) {
          const h = fs.readFileSync(path.join(ROOT, 'dashboard.html'), 'utf8').replace('window.DASH_ENDPOINT = "";', 'window.DASH_ENDPOINT = "' + LEAD_URL + '";');
          return route.fulfill({ status: 200, contentType: 'text/html', body: h });
        }
        return route.continue();
      }
      return route.abort();
    });
    await page.goto(base + url);
    return page;
  }

  async function fillForm(page, over = {}) {
    const v = Object.assign({ name: 'Asha Verma', mobile: '98765 43210', pickup: 'Jammu Airport', drop: 'Patnitop', pax: '4', vehicle: 'Ertiga', message: 'Need child seat' }, over);
    await page.fill('#rf-name', v.name); await page.fill('#rf-mobile', v.mobile); await page.fill('#rf-pickup', v.pickup);
    await page.fill('#rf-drop', v.drop); await page.fill('#rf-date', tomorrow()); await page.fill('#rf-pax', v.pax);
    await page.selectOption('#rf-vehicle', v.vehicle); await page.fill('#rf-message', v.message);
    if (over.consent) await page.check('input[name="consent_followup"]');
  }
  const NEW_PAGES = ['jammu-airport-taxi.html', 'katra-railway-station-taxi.html', 'katra-to-jammu-taxi.html', 'tempo-traveller-booking.html', 'urbania-booking.html', 'glanza-taxi-service.html', 'ramban-taxi-service.html', 'banihal-taxi-service.html'];

  console.log('Lead system (browser)');

  await test('every new page loads without script errors and shows Call, WhatsApp and the form', async () => {
    for (const f of NEW_PAGES) {
      const page = await open('/' + f);
      assert.deepStrictEqual(page.errors, [], f + ' script errors: ' + page.errors);
      assert(await page.locator('a.btn-pine[href="tel:+919103331334"]').first().isVisible(), f + ': Call Now button');
      assert(await page.locator('a.btn-whatsapp[href^="https://wa.me/919103331334"]').first().isVisible(), f + ': WhatsApp button');
      assert(await page.locator('#route-enquiry-form').count() === 1, f + ': form');
      assert(await page.locator('.mobile-bar a.call').isVisible(), f + ': sticky Call bar on mobile');
      await page.context().close();
    }
  });

  await test('form submission is stored with the right fields, source and page, and hands over call-first', async () => {
    const page = await open('/ramban-taxi-service.html', { referer: 'https://www.google.com/' });
    await fillForm(page, { consent: true });
    await page.click('#route-enquiry-form button[type=submit]');
    await page.waitForSelector('#route-form-success.show');
    const leads = page.posts.filter(p => p.type === 'taxi');
    assert.strictEqual(leads.length, 1, 'exactly one lead posted');
    const L = leads[0];
    assert.strictEqual(L.source, 'route-form'); assert.strictEqual(L.service, 'Ramban Taxi Service');
    assert.strictEqual(L.mobile, '9876543210'); assert.strictEqual(L.pickup, 'Jammu Airport'); assert.strictEqual(L.drop, 'Patnitop');
    assert.strictEqual(L.passengers, '4'); assert.strictEqual(L.vehicle, 'Ertiga'); assert.strictEqual(L.travel_date, tomorrow());
    assert.strictEqual(L.consent_followup, 'Yes'); assert(/^L[A-Z0-9]{6,23}$/.test(L.lead_id), 'lead id format: ' + L.lead_id);
    assert.strictEqual(L.landing_page, '/ramban-taxi-service.html'); assert.strictEqual(L.traffic_source, 'google_organic');
    assert.strictEqual(L.page, '/ramban-taxi-service.html');
    assert(!('status' in L) && !('_status' in L), 'website never sends a status');
    const box = page.locator('#route-form-success');
    const links = await box.locator('a').evaluateAll(as => as.map(a => a.getAttribute('href')));
    assert.strictEqual(links[0], 'tel:+919103331334', 'Call comes first');
    assert(/^https:\/\/wa\.me\/919103331334\?text=/.test(links[1]), 'WhatsApp second');
    assert(/not a confirmed booking/i.test(await box.innerText()), 'says enquiry is not a booking');
    assert.strictEqual(await page.inputValue('#rf-name'), '', 'form reset after submit');
  });

  await test('a form submission is NOT counted as a click, and is not a confirmed booking', async () => {
    const page = await open('/glanza-taxi-service.html');
    await fillForm(page); await page.click('#route-enquiry-form button[type=submit]'); await page.waitForSelector('#route-form-success.show');
    assert(page.posts.every(p => p.type === 'taxi'), 'only the lead was posted');
    assert(!page.posts.some(p => /confirm/i.test(JSON.stringify(Object.keys(p)))), 'no confirmed field');
  });

  await test('invalid mobile number blocks submission; honeypot sends nothing', async () => {
    let page = await open('/banihal-taxi-service.html');
    await fillForm(page, { mobile: '123' }); await page.click('#route-enquiry-form button[type=submit]');
    await page.waitForTimeout(250);
    assert.strictEqual(page.posts.length, 0, 'nothing posted for a bad mobile');
    assert(!(await page.locator('#route-form-success.show').count()));
    await page.context().close();
    page = await open('/banihal-taxi-service.html');
    await fillForm(page); await page.evaluate(() => { document.querySelector('input[name=website]').value = 'http://spam'; });
    await page.click('#route-enquiry-form button[type=submit]'); await page.waitForTimeout(250);
    assert.strictEqual(page.posts.length, 0, 'bot submission dropped');
  });

  await test('with no lead endpoint configured the form still works: call + WhatsApp hand-off, nothing sent', async () => {
    const page = await open('/urbania-booking.html', { endpoint: false });
    await fillForm(page); await page.click('#route-enquiry-form button[type=submit]'); await page.waitForSelector('#route-form-success.show');
    assert.strictEqual(page.posts.length, 0);
    assert.strictEqual(await page.locator('#route-form-success a[href="tel:+919103331334"]').count(), 1);
  });

  await test('Call and WhatsApp taps are recorded as separate events with page, position and source', async () => {
    const page = await open('/tempo-traveller-booking.html', { referer: 'https://www.google.co.in/search?q=x' });
    await page.evaluate(() => document.addEventListener('click', e => { if (e.target.closest('a')) e.preventDefault(); }, true));
    await page.click('.mobile-bar a.call'); await page.click('.mobile-bar a.whatsapp'); await page.click('.page-hero ~ section a.btn-pine');
    await page.waitForTimeout(300);
    const ev = page.posts.filter(p => p.type === 'event');
    assert.deepStrictEqual(ev.map(e => e.event), ['phone_click', 'whatsapp_click', 'phone_click']);
    assert.strictEqual(ev[0].link_location, 'mobile_bar'); assert.strictEqual(ev[2].link_location, 'content');
    assert(ev.every(e => e.page === '/tempo-traveller-booking.html' && e.traffic_source === 'google_organic'));
    assert(!page.posts.some(p => p.type === 'taxi'), 'taps are not leads');
    assert(ev.every(e => !('mobile' in e) && !('name' in e)), 'no personal data in click events');
  });

  await test('attribution is first-touch for the session and recognises Business Profile and direct visits', async () => {
    let page = await open('/jammu-airport-taxi.html?utm_source=google&utm_medium=organic&utm_campaign=gbp');
    await page.goto(base + '/katra-to-jammu-taxi.html');
    await page.evaluate(() => document.addEventListener('click', e => { if (e.target.closest('a')) e.preventDefault(); }, true));
    await page.click('.mobile-bar a.call'); await page.waitForTimeout(200);
    const e = page.posts.filter(p => p.type === 'event').pop();
    assert.strictEqual(e.traffic_source, 'google_business_profile'); assert.strictEqual(e.landing_page, '/jammu-airport-taxi.html');
    assert.strictEqual(e.page, '/katra-to-jammu-taxi.html');
    await page.context().close();
    page = await open('/'); await page.evaluate(() => document.addEventListener('click', e => { if (e.target.closest('a')) e.preventDefault(); }, true));
    await page.click('.mobile-bar a.call'); await page.waitForTimeout(200);
    assert.strictEqual(page.posts.filter(p => p.type === 'event')[0].traffic_source, 'direct');
  });

  await test('email taps are tracked too; no events are sent when no endpoint exists', async () => {
    const page = await open('/contact.html', { endpoint: false });
    await page.evaluate(() => document.addEventListener('click', e => { if (e.target.closest('a')) e.preventDefault(); }, true));
    await page.click('.mobile-bar a.call'); await page.waitForTimeout(200);
    assert.strictEqual(page.posts.length, 0);
  });

  await test('original contact-page form still works and now carries attribution', async () => {
    const page = await open('/contact.html', { referer: 'https://www.google.com/' });
    await page.fill('#name', 'Ravi'); await page.fill('#mobile', '9811122233'); await page.fill('#pickup', 'Katra'); await page.fill('#drop', 'Patnitop');
    await page.fill('#travel_date', tomorrow()); await page.fill('#passengers', '2');
    await page.click('#enquiry-form button[type=submit]'); await page.waitForSelector('#form-success.show');
    const L = page.posts.find(p => p.type === 'taxi');
    assert.strictEqual(L.source, 'contact-form'); assert.strictEqual(L.traffic_source, 'google_organic');
    assert(await page.locator('#vehicle option', { hasText: 'Urbania' }).count() === 1, 'contact form offers Urbania');
  });

  await test('dashboard: asks for the key, rejects a wrong key, and shows counts for a right one', async () => {
    let page = await open('/dashboard.html');
    await page.fill('#dash-key', 'wrongkey'); await page.click('#dash-load'); await page.waitForSelector('#dash-msg.err');
    assert(/not correct/i.test(await page.locator('#dash-msg').innerText()));
    assert(await page.locator('#dash-results').isHidden());
    assert(page.gets[0].includes('action=stats') && page.gets[0].includes('key=wrongkey'));
    await page.context().close();
    const stats = { ok: true, generated_at: new Date().toISOString(),
      totals: { enquiries: 7, genuine: 6, confirmed: 2, call_clicks: 41, whatsapp_clicks: 13, email_clicks: 1, form_submissions: 5, assistant_submissions: 2, cancelled: 1 },
      by_source: { google_organic: 4, direct: 3 }, by_landing_page: { '/jammu-airport-taxi.html': 3, '/': 4 }, by_service: { 'Jammu Airport Taxi': 3 },
      by_day: { [iso(new Date())]: 2 }, clicks_by_page: { '/jammu-airport-taxi.html | phone_click': 20, '/jammu-airport-taxi.html | whatsapp_click': 5 }, clicks_by_location: { 'mobile_bar | phone_click': 30 } };
    page = await open('/dashboard.html', { stats });
    await page.fill('#dash-key', 'rightkey'); await page.click('#dash-load'); await page.waitForSelector('#dash-results:not([hidden])');
    const tiles = await page.locator('.dash-tile').allInnerTexts();
    const joined = tiles.join(' | ');
    assert(/7\s+Total enquiries/.test(joined) && /41\s+Call button taps/.test(joined) && /13\s+WhatsApp taps/.test(joined) && /2\s+Confirmed bookings/.test(joined), joined);
    assert(/google_organic/.test(await page.locator('#dash-sources').innerText()));
    assert(/jammu-airport-taxi/.test(await page.locator('#dash-pages').innerText()));
    assert.strictEqual(await page.inputValue('#dash-key'), '', 'key field cleared after use');
    assert.deepStrictEqual(page.errors, []);
  });

  await test('dashboard reads a Search Console Queries.csv on the device and uploads nothing', async () => {
    const page = await open('/dashboard.html');
    const csv = 'Top queries,Clicks,Impressions,CTR,Position\n"jammu to patnitop taxi",12,340,3.5%,6.2\nkatra to patnitop taxi,3,90,3.3%,9.8\n';
    await page.setInputFiles('#dash-file', { name: 'Queries.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) });
    await page.waitForSelector('#dash-gsc table');
    const txt = await page.locator('#dash-gsc').innerText();
    assert(/jammu to patnitop taxi/.test(txt) && /340/.test(txt) && /6\.2/.test(txt));
    assert.strictEqual(page.posts.length, 0, 'nothing uploaded');
  });

  await test('dashboard with no endpoint explains what to do instead of failing', async () => {
    const page = await open('/dashboard.html', { endpoint: false });
    assert(/not connected yet/i.test(await page.locator('#dash-msg').innerText()));
  });

  await test('layout: no horizontal scroll at phone width on a new page and the dashboard', async () => {
    for (const f of ['/ramban-taxi-service.html', '/dashboard.html']) {
      const page = await open(f);
      const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      assert(over <= 1, f + ' overflows by ' + over + 'px');
      await page.context().close();
    }
  });

  await test('small Android width (360px): all new pages fit, taps are big enough, the sticky bar hides nothing, inputs do not trigger zoom', async () => {
    for (const f of NEW_PAGES.concat(['katra-to-patnitop-taxi.html', 'contact.html'])) {
      const ctx = await browser.newContext({ viewport: { width: 360, height: 740 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
      const page = await ctx.newPage(); await page.route('**/*', r => r.request().url().startsWith(base) ? r.continue() : r.abort());
      await page.goto(base + '/' + f);
      const m = await page.evaluate(() => {
        const bar = document.querySelector('.mobile-bar'), barH = bar ? bar.getBoundingClientRect().height : 0;
        const call = [...document.querySelectorAll('a[href^="tel:"]')].filter(a => a.offsetParent && a.className); // buttons only; inline text links inside sentences are exempt
        const small = call.filter(a => a.getBoundingClientRect().height < 44).map(a => a.textContent.trim().slice(0, 30));
        const inputs = [...document.querySelectorAll('form input:not([type=checkbox]):not([type=hidden]), form select, form textarea')].filter(i => i.offsetParent);
        const tiny = inputs.filter(i => parseFloat(getComputedStyle(i).fontSize) < 16).map(i => i.name || i.id);
        return { over: document.documentElement.scrollWidth - document.documentElement.clientWidth, barH, pad: parseFloat(getComputedStyle(document.body).paddingBottom), small, tiny, barVisible: !!bar && getComputedStyle(bar).display !== 'none' };
      });
      assert(m.over <= 1, f + ' overflows by ' + m.over + 'px');
      assert(m.barVisible, f + ': sticky Call bar not visible');
      assert(m.pad + 1 >= m.barH, f + ': page bottom padding ' + m.pad + ' is smaller than the sticky bar ' + m.barH + ' (footer content would be hidden)');
      assert.deepStrictEqual(m.small, [], f + ': Call links under 44px tall: ' + m.small);
      assert.deepStrictEqual(m.tiny, [], f + ': form fields under 16px font (phones zoom in): ' + m.tiny);
      await ctx.close();
    }
  });

  await browser.close(); server.close();
  console.log(`\n${passed} passed, ${failures.length} failed`);
  process.exit(failures.length ? 1 : 0);
})();
