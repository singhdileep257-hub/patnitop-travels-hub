// Browser tests for the website assistant, the enquiry forms, tracking and layout.
// Runs the REAL built site in headless Chromium against a local static server.
//   cd tests && npm install && npx playwright install chromium && node agent.test.js
// Network is blocked except localhost; the lead endpoint is faked and recorded.
const assert = require('assert');
const fs = require('fs');
const http = require('http');
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/npm-tools/node_modules/playwright')); }

const ROOT = path.resolve(__dirname, '..');
const SHOTS = process.env.SHOT_DIR || '';
const LEAD_URL = 'https://leads.test/macros/s/TEST/exec';
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.xml': 'application/xml', '.txt': 'text/plain' };

function serve() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p === '/') p = '/index.html';
    const file = path.join(ROOT, p);
    if (file.startsWith(ROOT) && fs.existsSync(file) && fs.statSync(file).isFile()) {
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
      return fs.createReadStream(file).pipe(res);
    }
    res.writeHead(404, { 'Content-Type': 'text/html' });   // Netlify-style: serve 404.html at the requested URL
    fs.createReadStream(path.join(ROOT, '404.html')).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

const iso = d => d.toISOString().slice(0, 10);
const daysFromNow = n => iso(new Date(Date.now() + n * 86400000));

let passed = 0;
const failures = [];
async function test(name, fn) {
  try { await fn(); passed++; console.log('  ok   ' + name); }
  catch (e) { failures.push(name); console.log('  FAIL ' + name + '\n       ' + String(e.message).split('\n').join('\n       ')); }
}

(async () => {
  const server = await serve();
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();

  // Opens a page with network blocked, the lead endpoint faked, and optional edits to agent-data.js.
  async function newPage(url, { viewport, mutateData } = {}) {
    const ctx = await browser.newContext({ viewport: viewport || { width: 1100, height: 800 } });
    const page = await ctx.newPage();
    page.posts = []; page.errors = [];
    page.on('pageerror', e => page.errors.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) page.errors.push('console: ' + m.text()); });
    await page.route('**/*', route => {
      const u = route.request().url();
      if (u === LEAD_URL) {
        if (page.failLead) return route.abort('failed');
        page.posts.push(JSON.parse(route.request().postData())); return route.fulfill({ status: 200, body: '{"ok":true}' });
      }
      if (u.startsWith(base)) {
        if (mutateData && u.endsWith('/js/agent-data.js')) {
          let js = fs.readFileSync(path.join(ROOT, 'js', 'agent-data.js'), 'utf8');
          return route.fulfill({ status: 200, contentType: 'text/javascript', body: mutateData(js) });
        }
        return route.continue();
      }
      return route.abort();
    });
    await page.goto(base + url);
    return page;
  }
  const withEndpoint = js => js.replace('"leadEndpoint": ""', '"leadEndpoint": "' + LEAD_URL + '"');
  const withRates = rates => js => withEndpoint(js).replace('"rates": []', '"rates": ' + JSON.stringify(rates));

  const openAgent = async page => { await page.click('#ptv-agent-launcher'); await page.waitForSelector('#ptv-agent-panel:not([hidden])'); };
  const choose = (page, label) => page.locator('#ptv-agent-body button:not([disabled])').filter({ hasText: new RegExp('^' + label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$') }).last().click();
  const answer = async (page, value) => {
    await page.locator('#ptv-agent-body input:not([disabled])').last().fill(value);
    await page.locator('#ptv-agent-body .ptv-input-submit:not([disabled])').last().click();
  };
  const bodyText = page => page.locator('#ptv-agent-body').innerText();

  // Drives the Katra taxi flow up to the summary.
  async function katraFlow(page, { vehicle = 'Dzire', mobile = '98765 43210', pickup = 'Katra Railway Station', drop = 'Hotel in Patnitop', confirm = true } = {}) {
    await openAgent(page);
    await choose(page, '🚕 Book a Taxi');
    await choose(page, 'Katra to Patnitop');
    await choose(page, '📝 Start Enquiry');
    await answer(page, 'Asha Test');
    await answer(page, mobile);
    await answer(page, daysFromNow(10));
    await answer(page, pickup);
    await answer(page, drop);
    await answer(page, '4');
    await choose(page, vehicle);
    await choose(page, 'One-way');
    await choose(page, 'Yes');   // sightseeing
    await choose(page, 'No');    // hotel
    await choose(page, 'Yes, you may follow up');
    await page.waitForSelector('.ptv-summary-card');
    if (confirm) await choose(page, "✅ Yes, that's correct");
  }

  console.log('Assistant');

  await test('widget is styled: launcher floats, panel opens as an overlay with a menu', async () => {
    const page = await newPage('/index.html');
    const pos = await page.$eval('#ptv-agent-launcher', el => getComputedStyle(el.parentElement).position);
    assert.strictEqual(pos, 'fixed', 'agent root must be position:fixed (CSS missing?)');
    await openAgent(page);
    const t = await bodyText(page);
    assert(/Welcome to Patnitop Travels Hub/.test(t));
    assert(/Book a Taxi/.test(t) && /Local Products Enquiry/.test(t));
    const panelPos = await page.$eval('#ptv-agent-panel', el => getComputedStyle(el).position);
    assert.strictEqual(panelPos, 'absolute');
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'agent-desktop-menu.png') });
    assert.deepStrictEqual(page.errors, []);
  });

  await test('taxi flow: validates inputs, shows summary, no fare is invented, lead recorded only on action', async () => {
    const page = await newPage('/katra-to-patnitop-taxi.html', { mutateData: withEndpoint });
    await openAgent(page);
    await choose(page, '🚕 Book a Taxi');
    await choose(page, 'Katra to Patnitop');
    await choose(page, '📝 Start Enquiry');
    await answer(page, 'Asha Test');
    await answer(page, 'abc');                                                // invalid mobile
    assert(/valid mobile number/.test(await bodyText(page)), 'invalid mobile must show an error');
    await answer(page, '98765 43210');
    const dateMin = await page.locator('#ptv-agent-body input[type=date]').last().getAttribute('min');
    assert.strictEqual(dateMin, daysFromNow(0), 'date picker must block past dates');
    await answer(page, daysFromNow(-3));
    assert(/already passed/.test(await bodyText(page)), 'a past date must be refused');
    await answer(page, daysFromNow(10));
    await answer(page, 'Katra Railway Station');
    await answer(page, 'katra railway station');
    assert(/same place/.test(await bodyText(page)), 'pickup = drop must be refused');
    await answer(page, 'Hotel in Patnitop');
    await answer(page, '0');                                                  // invalid passengers
    assert(/between 1 and 60/.test(await bodyText(page)));
    await answer(page, '4');
    await choose(page, 'Dzire');
    await choose(page, 'One-way');
    await choose(page, 'Yes');
    await choose(page, 'No');
    await choose(page, 'Yes, you may follow up');
    await page.waitForSelector('.ptv-summary-card');
    let t = await bodyText(page);
    assert(t.includes('9876543210'), 'cleaned mobile in summary');
    assert(/Trip outline/.test(t) && /Katra Railway Station → Hotel in Patnitop/.test(t));
    assert(/don't have a verified fare/.test(t), 'must say it has no verified fare');
    assert(!/₹/.test(t), 'no price may appear when data/rates.json is empty');
    assert(/Is everything correct\?/.test(t));
    assert.strictEqual(await page.locator('#ptv-agent-body a.btn-whatsapp').count(), 0, 'no send buttons before the customer confirms');
    assert.strictEqual(page.posts.length, 0, 'nothing is stored before the visitor acts');
    await choose(page, "✅ Yes, that's correct");
    t = await bodyText(page);
    assert(/not a confirmed booking/.test(t));
    assert.strictEqual(page.posts.length, 0, 'confirming alone does not store anything; sending does');
    const wa = await page.getAttribute('#ptv-agent-body a.btn-whatsapp', 'href');
    assert(wa.startsWith('https://wa.me/919103331334?text='));
    const msg = decodeURIComponent(wa.split('text=')[1]);
    assert(/Mobile: 9876543210/.test(msg) && /OK to follow up: Yes/.test(msg) && /Ref: L[A-Z0-9]+/.test(msg));
    await page.evaluate(() => document.addEventListener('click', e => e.preventDefault()));  // don't navigate away
    await page.click('#ptv-agent-body a.btn-whatsapp');
    await page.click('#ptv-agent-body a.btn-whatsapp');                       // double tap
    await page.waitForFunction(() => true); await new Promise(r => setTimeout(r, 200));
    assert.strictEqual(page.posts.length, 1, 'exactly one lead per enquiry');
    const lead = page.posts[0];
    assert.strictEqual(lead.type, 'taxi'); assert.strictEqual(lead.source, 'agent');
    assert.strictEqual(lead.mobile, '9876543210'); assert.strictEqual(lead.consent_followup, 'Yes');
    assert.strictEqual(lead.trip_type, 'one-way'); assert.strictEqual(lead.quote_shown, 'No verified fare shown');
    assert(msg.includes('Ref: ' + lead.lead_id), 'WhatsApp message and stored lead share the same reference');
    const events = await page.evaluate(() => window.dataLayer.map(e => e.event));
    assert(events.includes('quote_request') && events.includes('generate_lead') && events.includes('whatsapp_click'), 'events: ' + events);
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'agent-desktop-summary.png') });
    assert.deepStrictEqual(page.errors, []);
  });

  await test('quotes ONLY from a verified, recent rate; stale or missing rates are never quoted', async () => {
    const rates = [
      { route_id: 'katra', vehicle: 'Dzire', trip_type: 'one-way', amount_inr: 4321, includes: 'TEST fare incl. tolls', verified_on: daysFromNow(-5), verified_by: 'Test Owner' },
      { route_id: 'katra', vehicle: 'Ertiga', trip_type: 'one-way', amount_inr: 9999, includes: 'TEST stale', verified_on: daysFromNow(-200), verified_by: 'Test Owner' },
    ];
    let page = await newPage('/index.html', { mutateData: withRates(rates) });
    await katraFlow(page, { vehicle: 'Dzire' });
    let t = await bodyText(page);
    assert(/Verified fare: ₹4,321/.test(t), 'fresh verified rate is shown');
    assert(/Fare checked on/.test(t) && /Test Owner/.test(t) && /confirms the final fare/.test(t));
    page = await newPage('/index.html', { mutateData: withRates(rates) });
    await katraFlow(page, { vehicle: 'Ertiga' });
    t = await bodyText(page);
    assert(!/9,999|₹/.test(t), 'a rate older than 90 days must not be quoted');
    assert(/don't have a verified fare/.test(t));
    page = await newPage('/index.html', { mutateData: withRates(rates) });
    await katraFlow(page, { vehicle: 'Innova / Toyota Crysta' });
    assert(!/₹/.test(await bodyText(page)), 'vehicle without a rate gets no price');
  });

  await test('"Just send my details" appears only with an endpoint and records one lead', async () => {
    let page = await newPage('/index.html');                                  // no endpoint configured
    await katraFlow(page);
    assert.strictEqual(await page.locator('#ptv-agent-body button', { hasText: 'Just send my details' }).count(), 0);
    page = await newPage('/index.html', { mutateData: withEndpoint });
    await katraFlow(page);
    await page.locator('#ptv-agent-body button', { hasText: 'Just send my details' }).click();
    await page.waitForFunction(() => /have been sent to Dileep/.test(document.getElementById("ptv-agent-body").innerText));
    assert.strictEqual(page.posts.length, 1);
    assert.strictEqual(page.posts[0].name, 'Asha Test');
  });

  await test('product enquiry is a separate flow: no trip outline, no fare, product label, type=product', async () => {
    const page = await newPage('/index.html', { mutateData: withEndpoint });
    await openAgent(page);
    await choose(page, '🛍️ Local Products Enquiry');
    assert(/no online shop, price list or stock list/.test(await bodyText(page)));
    await choose(page, '📝 Start Product Enquiry');
    await answer(page, 'Ravi Test');
    await answer(page, '+91 91234 56789');
    await answer(page, 'honey and rajma');
    await answer(page, '2 kg, Delhi');
    await choose(page, "No, I'll contact you");
    await page.waitForSelector('.ptv-summary-card');
    await choose(page, "✅ Yes, that's correct");
    const t = await bodyText(page);
    assert(!/Trip outline|verified fare|Pickup/.test(t));
    assert(/This is an enquiry, not an order/.test(t));
    const wa = decodeURIComponent((await page.getAttribute('#ptv-agent-body a.btn-whatsapp', 'href')).split('text=')[1]);
    assert(/^PRODUCT ENQUIRY \(not a taxi booking\)/.test(wa));
    await page.evaluate(() => document.addEventListener('click', e => e.preventDefault()));
    await page.click('#ptv-agent-body a.btn-whatsapp');
    await new Promise(r => setTimeout(r, 200));
    assert.strictEqual(page.posts[0].type, 'product');
    assert.strictEqual(page.posts[0].mobile, '+919123456789');
    assert.strictEqual(page.posts[0].consent_followup, 'No');
    const events = await page.evaluate(() => window.dataLayer.map(e => e.event));
    assert(events.includes('product_enquiry'));
  });

  await test('free text: products, prices, places and FAQs are routed sensibly', async () => {
    const page = await newPage('/index.html');
    await openAgent(page);
    await choose(page, '❓ Ask a Question');
    await answer(page, 'do you sell honey');
    assert(/Local Products Enquiry/.test(await bodyText(page)));
    await choose(page, '⬅ Main Menu'.replace('⬅ ', '⬅ ')).catch(() => {});
    const p2 = await newPage('/index.html');
    await openAgent(p2); await choose(p2, '❓ Ask a Question');
    await answer(p2, 'how much is a taxi to kudh');
    let t = await bodyText(p2);
    assert(/can't give a price without checking/.test(t) && /Enquire: Kudh \(Kud\) to Patnitop/.test(t));
    assert(!/₹/.test(t));
    const p3 = await newPage('/index.html');
    await openAgent(p3); await choose(p3, '❓ Ask a Question');
    await answer(p3, 'taxi from udhampur');
    assert(/Udhampur to Patnitop/.test(await bodyText(p3)));
    const p4 = await newPage('/index.html');
    await openAgent(p4); await choose(p4, '❓ Ask a Question');
    await answer(p4, 'do you have tempo traveller');
    assert(/Tempo Traveller service is available/.test(await bodyText(p4)));
    const p5 = await newPage('/index.html');
    await openAgent(p5); await choose(p5, '❓ Ask a Question');
    await answer(p5, 'what is the meaning of life');
    assert(/continue on WhatsApp/.test(await bodyText(p5)));
  });


  await test('a fare is never stretched to a different trip: Katra button + Delhi→Goa gets no fare', async () => {
    const rates = [{ route_id: 'katra', vehicle: 'Dzire', trip_type: 'one-way', amount_inr: 4321, includes: 'TEST', verified_on: daysFromNow(-5), verified_by: 'Test Owner' }];
    const page = await newPage('/index.html', { mutateData: withRates(rates) });
    await katraFlow(page, { vehicle: 'Dzire', pickup: 'Delhi', drop: 'Goa', confirm: false });
    const t = await bodyText(page);
    assert(!/₹|4,321/.test(t), 'no fare for a trip that is not Katra <-> Patnitop');
    assert(/outside the routes I have verified fares for/.test(t) && /manual confirmation/.test(t));
  });

  await test('"Not sure" vehicle or trip type never gets a fare, even on a verified route', async () => {
    const rates = [{ route_id: 'katra', vehicle: 'Dzire', trip_type: 'one-way', amount_inr: 4321, includes: 'TEST', verified_on: daysFromNow(-5), verified_by: 'Test Owner' }];
    const page = await newPage('/index.html', { mutateData: withRates(rates) });
    await katraFlow(page, { vehicle: 'Not sure — please suggest', confirm: false });
    assert(!/₹/.test(await bodyText(page)));
  });

  await test('describe in your own words: details are picked out, only the missing ones are asked', async () => {
    const page = await newPage('/index.html', { mutateData: withEndpoint });
    await openAgent(page);
    await choose(page, '✍️ Describe my trip');
    await answer(page, 'from Katra railway station to Patnitop on 25 December for 4 people, innova one way, my name is Asha Test, 98765 43210');
    const t = await bodyText(page);
    assert(/Here is what I understood/.test(t));
    for (const want of ['Name: Asha Test', 'Mobile: 9876543210', 'Pickup: Katra Railway Station', 'Drop: Patnitop', 'Passengers: 4', 'Vehicle: Innova / Toyota Crysta', 'Trip type: one-way'])
      assert(t.includes(want), 'missing "' + want + '" in:\n' + t);
    assert(/Date: 20\d\d-12-25/.test(t), 'date understood');
    // everything was given except consent: that must be the very next question
    await page.waitForSelector('#ptv-agent-body button:has-text("Yes, you may follow up")');
    assert.strictEqual(await page.locator('#ptv-agent-body input:not([disabled])').count(), 0, 'no further typed answers needed');
    await choose(page, 'Yes, you may follow up');
    await page.waitForSelector('.ptv-summary-card');
    const s2 = await bodyText(page);
    assert(/Katra Railway Station → Patnitop/.test(s2) && /Is everything correct\?/.test(s2));
    assert.strictEqual(page.posts.length, 0);
    await choose(page, "✅ Yes, that's correct");
    await page.evaluate(() => document.addEventListener('click', e => e.preventDefault()));
    await page.click('#ptv-agent-body a.btn-whatsapp');
    await new Promise(r => setTimeout(r, 200));
    assert.strictEqual(page.posts.length, 1);
    assert.strictEqual(page.posts[0].pickup, 'Katra Railway Station'); assert.strictEqual(page.posts[0].trip_type, 'one-way');
    assert.strictEqual(page.posts[0].service, 'Taxi enquiry');
  });

  await test('describe: vague text falls back to step-by-step questions', async () => {
    const page = await newPage('/index.html');
    await openAgent(page);
    await choose(page, '✍️ Describe my trip');
    await answer(page, 'we want a cab for our family trip');
    assert(/I'll ask step by step/.test(await bodyText(page)));
    assert(/What name should I note down/.test(await bodyText(page)));
  });

  await test('trip parser: dates, head-counts, phone numbers and junk are read safely', async () => {
    const page = await newPage('/index.html');
    const parse = txt => page.evaluate(t => window.__ptvAgentTest.parseTrip(t), txt);
    const d = n => daysFromNow(n);
    assert.strictEqual((await parse('need taxi tomorrow')).date, d(1));
    assert.strictEqual((await parse('day after tomorrow please')).date, d(2));
    assert.strictEqual((await parse('on 5th nov 2027 for 2 adults')).date, '2027-11-05');
    assert.strictEqual((await parse('12/03/2027')).date, '2027-03-12');
    assert.strictEqual((await parse('31 feb 2027')).date, undefined, 'impossible date ignored');
    assert.strictEqual((await parse('on 3 jan 2020')).date, undefined, 'a past date is ignored');
    assert.strictEqual((await parse('family of 5')).passengers, '5');
    assert.strictEqual((await parse('we are 6')).passengers, '6');
    assert.strictEqual((await parse('99 people')).passengers, undefined, 'absurd head-count ignored');
    const ph = await parse('call me on 98765 43210 or 98765-43210');
    assert.strictEqual(ph.mobile, '9876543210'); assert.strictEqual(ph.date, undefined); assert.strictEqual(ph.passengers, undefined);
    assert.strictEqual((await parse('call +91 91234 56789')).mobile, '9123456789');
    assert.strictEqual((await parse('tempo traveller round trip')).vehicle, 'Tempo Traveller');
    assert.strictEqual((await parse('tempo traveller round trip')).tripType, 'round-trip');
    assert.deepStrictEqual(await parse('hello'), {});
    assert.deepStrictEqual(await parse('from Jammu to Jammu'), {}, 'same pickup and drop ignored');
    const ft = await parse('from kudh to patnitop for 3 people');
    assert.strictEqual(ft.pickup, 'Kudh'); assert.strictEqual(ft.drop, 'Patnitop');
    const rt = (a, b) => page.evaluate(([x, y]) => { const r = window.__ptvAgentTest.routeForTrip(x, y); return r ? r.id : null; }, [a, b]);
    assert.strictEqual(await rt('Kudh', 'Patnitop hotel'), 'kudh');
    assert.strictEqual(await rt('Hotel in Patnitop', 'Chenani'), 'chenani');
    assert.strictEqual(await rt('Katra', 'Srinagar'), null);
    assert.strictEqual(await rt('Udhampur', 'Jammu'), null, 'Udhampur<->Jammu is not a Patnitop route');
  });

  await test('confirm step: customer can change an answer, capacity is checked, nothing sent meanwhile', async () => {
    const page = await newPage('/index.html', { mutateData: withEndpoint });
    await katraFlow(page, { vehicle: 'Dzire', confirm: false });
    await choose(page, '✏️ Change something');
    await choose(page, 'Passengers: 4');
    await answer(page, '5');
    await page.waitForFunction(() => /Please check your enquiry/.test(document.getElementById('ptv-agent-body').innerText) && document.querySelectorAll('.ptv-summary-card').length === 2);
    const t = await bodyText(page);
    assert(/Passengers\s*5/.test(t), 'new head-count shown');
    assert(/A Dzire seats up to 4/.test(t), 'capacity warning for 5 people in a Dzire');
    assert.strictEqual(page.posts.length, 0);
    await choose(page, '✏️ Change something');
    await choose(page, 'Vehicle: Dzire');
    await choose(page, 'Ertiga');
    await page.waitForFunction(() => document.querySelectorAll('.ptv-summary-card').length === 3);
    assert(!/A Ertiga seats/.test(await bodyText(page).then(x => x.split('Please check your enquiry').pop())), 'no warning once the vehicle fits');
  });

  await test('connection failure is reported honestly, can be retried, and never loses the WhatsApp route', async () => {
    const page = await newPage('/index.html', { mutateData: withEndpoint });
    page.failLead = true;
    await katraFlow(page);
    await page.locator('#ptv-agent-body button', { hasText: 'Just send my details' }).click();
    await page.waitForFunction(() => /have not/.test(document.getElementById('ptv-agent-body').innerText) || /not been sent/.test(document.getElementById('ptv-agent-body').innerText));
    let t = await bodyText(page);
    assert(/not\s+been sent/.test(t) && /connection failed/.test(t), t.slice(-300));
    assert(!/have been sent to Dileep/.test(t), 'must not claim success');
    assert.strictEqual(page.posts.length, 0);
    assert(await page.locator('#ptv-agent-body a.btn-whatsapp').count() === 1, 'WhatsApp button still available');
    page.failLead = false;                                          // connection is back
    await page.locator('#ptv-agent-body button', { hasText: 'Try again' }).click();
    await page.waitForFunction(() => /have been sent to Dileep/.test(document.getElementById('ptv-agent-body').innerText));
    assert.strictEqual(page.posts.length, 1, 'retry stores the lead exactly once');
    // offline browser
    const p2 = await newPage('/index.html', { mutateData: withEndpoint });
    await katraFlow(p2);
    await p2.context().setOffline(true);
    await p2.locator('#ptv-agent-body button', { hasText: 'Just send my details' }).click();
    await p2.waitForFunction(() => /offline/.test(document.getElementById('ptv-agent-body').innerText));
    assert(/not\s+been sent/.test(await bodyText(p2)));
  });

  console.log('Forms and tracking');

  await test('contact form: blocks bad mobile and bots, records lead, hands off to WhatsApp with same Ref', async () => {
    const page = await newPage('/contact.html', { mutateData: withEndpoint });
    const fill = async mobile => {
      await page.fill('#name', 'Meena Test'); await page.fill('#mobile', mobile);
      await page.fill('#pickup', 'Jammu Airport'); await page.fill('#drop', 'Patnitop');
      await page.fill('#travel_date', daysFromNow(7)); await page.fill('#passengers', '3');
    };
    await fill('12');
    await page.click('#enquiry-form button[type=submit]');
    assert.strictEqual(page.posts.length, 0, 'invalid mobile must not submit');
    assert(await page.$eval('#mobile', el => !el.validity.valid));
    await page.fill('#mobile', '9876543210');
    await page.check('input[name=consent_followup]');
    await page.click('#enquiry-form button[type=submit]');
    await page.waitForSelector('#form-success.show');
    await new Promise(r => setTimeout(r, 200));
    assert.strictEqual(page.posts.length, 1);
    const lead = page.posts[0];
    assert.strictEqual(lead.type, 'taxi'); assert.strictEqual(lead.source, 'contact-form'); assert.strictEqual(lead.consent_followup, 'Yes');
    const href = await page.getAttribute('#form-success a.btn-whatsapp', 'href');
    assert(decodeURIComponent(href).includes('Ref: ' + lead.lead_id));
    assert(/not a confirmed booking/.test(await page.innerText('#form-success')));
    const events = await page.evaluate(() => window.dataLayer.map(e => e.event));
    assert(events.includes('generate_lead') && events.includes('quote_request'));
    // honeypot: a bot filling the hidden field is silently dropped
    await fill('9876543210');
    await page.evaluate(() => { document.querySelector('input[name=website]').value = 'http://spam.example'; });
    await page.click('#enquiry-form button[type=submit]');
    await new Promise(r => setTimeout(r, 200));
    assert.strictEqual(page.posts.length, 1, 'honeypot submissions must not create a lead');
    assert.deepStrictEqual(page.errors, []);
  });

  await test('contact form: a name containing HTML is shown as text, not injected', async () => {
    const page = await newPage('/contact.html');
    await page.fill('#name', '<img src=x onerror=window.__xss=1>'); await page.fill('#mobile', '9876543210');
    await page.fill('#pickup', 'a'); await page.fill('#drop', 'b'); await page.fill('#travel_date', daysFromNow(3)); await page.fill('#passengers', '2');
    await page.click('#enquiry-form button[type=submit]');
    await page.waitForSelector('#form-success.show');
    assert.strictEqual(await page.evaluate(() => window.__xss), undefined);
    assert(await page.locator('#form-success img').count() === 0);
  });

  await test('product page: separate form, product-labelled WhatsApp message, noindex, requires a product', async () => {
    const page = await newPage('/local-products-enquiry.html', { mutateData: withEndpoint });
    assert.strictEqual(await page.getAttribute('meta[name=robots]', 'content'), 'noindex, nofollow');
    assert(/not a shop/.test(await page.innerText('#product-form')));
    await page.fill('#p-name', 'Ravi Test'); await page.fill('#p-mobile', '9876543210');
    await page.evaluate(() => { document.querySelectorAll('input[name=products]').forEach(c => c.required = false); });
    await page.click('#product-enquiry-form button[type=submit]');
    assert.strictEqual(page.posts.length, 0, 'no product ticked -> no submit');
    await page.check('input[name=products][value="Honey"]'); await page.check('input[name=products][value="Gift hampers"]');
    await page.click('#product-enquiry-form button[type=submit]');
    await page.waitForSelector('#product-form-success.show');
    await new Promise(r => setTimeout(r, 200));
    assert.strictEqual(page.posts.length, 1);
    assert.strictEqual(page.posts[0].type, 'product'); assert.strictEqual(page.posts[0].products, 'Honey, Gift hampers');
    const href = decodeURIComponent(await page.getAttribute('#product-form-success a.btn-whatsapp', 'href'));
    assert(/PRODUCT ENQUIRY \(not a taxi booking\)/.test(href));
  });

  await test('tracking: phone and WhatsApp clicks are recorded with their placement', async () => {
    const page = await newPage('/index.html');
    await page.evaluate(() => document.addEventListener('click', e => e.preventDefault()));
    await page.click('.header-call');
    await page.click('.hero a.btn-whatsapp');
    const evs = await page.evaluate(() => window.dataLayer);
    const phone = evs.find(e => e.event === 'phone_click'), wa = evs.find(e => e.event === 'whatsapp_click');
    assert(phone && phone.link_location === 'header', JSON.stringify(evs));
    assert(wa && wa.link_location === 'hero', JSON.stringify(evs));
  });

  await test('no analytics or third-party script is requested while no GA4 ID is configured', async () => {
    const page = await newPage('/index.html');
    const external = await page.evaluate(() => [...document.scripts].map(s => s.src).filter(s => s && !s.startsWith(location.origin)));
    assert.deepStrictEqual(external, []);
  });

  console.log('Layout');

  await test('mobile: launcher clears the call bar, panel stays on screen, 404 page keeps its styles on nested URLs', async () => {
    const page = await newPage('/index.html', { viewport: { width: 390, height: 844 } });
    const bar = await page.locator('.mobile-bar').boundingBox();
    const btn = await page.locator('#ptv-agent-launcher').boundingBox();
    assert(bar && btn && btn.y + btn.height <= bar.y + 1, `launcher (${btn.y + btn.height}) must sit above the call bar (${bar.y})`);
    await openAgent(page);
    const pb = await page.locator('#ptv-agent-panel').boundingBox();
    assert(pb.x >= 0 && pb.x + pb.width <= 390 && pb.y >= 0 && pb.y + pb.height <= bar.y + 1, 'panel inside viewport above call bar');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    assert(!overflow, 'no horizontal scroll');
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, 'agent-mobile-menu.png') });
    await page.context().close();
    const pm = await newPage('/index.html', { viewport: { width: 390, height: 844 } });
    await katraFlow(pm, { confirm: false });
    const pmb = await pm.locator('#ptv-agent-panel').boundingBox();
    assert(pmb.x >= 0 && pmb.x + pmb.width <= 390, 'panel fits the phone width on the confirm screen');
    assert(!(await pm.evaluate(() => document.documentElement.scrollWidth > innerWidth)), 'no horizontal scroll on the confirm screen');
    if (SHOTS) await pm.screenshot({ path: path.join(SHOTS, 'agent-mobile-confirm.png') });
    const p404 = await newPage('/no/such/page', { viewport: { width: 390, height: 844 } });
    const bg = await p404.$eval('.page-hero', el => getComputedStyle(el).backgroundColor);
    assert.notStrictEqual(bg, 'rgba(0, 0, 0, 0)', '404 must load css from root-absolute paths');
    assert(/Page not found/.test(await p404.innerText('h1')));
  });

  await test('header: never wraps or overflows at common widths (desktop nav or hamburger)', async () => {
    for (const w of [360, 390, 768, 900, 1024, 1100, 1139, 1141, 1280, 1440]) {
      const page = await newPage('/index.html', { viewport: { width: w, height: 800 } });
      const h = await page.$eval('header.site-header .container', el => el.getBoundingClientRect().height);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      assert(!overflow, `horizontal scroll at ${w}px`);
      const toggleShown = await page.$eval('.nav-toggle', el => getComputedStyle(el).display !== 'none');
      if (!toggleShown) {
        const wrapped = await page.$$eval('nav.main-nav a', as => as.some(a => a.getBoundingClientRect().height > 30));
        assert(!wrapped, `nav link wraps onto two lines at ${w}px`);
        const callH = await page.$eval('.header-call', el => el.getBoundingClientRect().height);
        assert(callH < 50, `call button wraps at ${w}px (height ${callH})`);
      }
      if (SHOTS && (w === 1280 || w === 1024)) await page.screenshot({ path: path.join(SHOTS, `header-${w}.png`), clip: { x: 0, y: 0, width: w, height: 160 } });
    }
  });

  await test('new location pages render with call, WhatsApp and assistant', async () => {
    for (const p of ['udhampur', 'chenani', 'kudh']) {
      const page = await newPage(`/${p}-to-patnitop-taxi.html`);
      assert(/Taxi/.test(await page.innerText('h1')));
      assert(await page.locator('a[href^="tel:+919103331334"]').count() > 0);
      assert(await page.locator('a[href^="https://wa.me/919103331334"]').count() > 0);
      assert(await page.locator('#ptv-agent-launcher').count() === 1);
      assert.deepStrictEqual(page.errors, []);
    }
  });

  await browser.close(); server.close();
  console.log(`\n${passed} passed, ${failures.length} failed`);
  if (failures.length) { console.log('Failed: ' + failures.join('; ')); process.exit(1); }
})().catch(e => { console.error(e); process.exit(1); });
