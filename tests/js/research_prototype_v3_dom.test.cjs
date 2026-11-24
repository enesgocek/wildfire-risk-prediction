'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');

assert(process.env.RESEARCH_PROTOTYPE_DIR, 'Select the actual generated v3 prototype');
const directory = path.resolve(process.env.RESEARCH_PROTOTYPE_DIR);
const html = fs.readFileSync(path.join(directory, 'inceleme.html'), 'utf8');
const raw = fs.readFileSync(path.join(directory, 'review_data.js'), 'utf8').trimEnd();
assert(raw.startsWith('globalThis.RESEARCH_DATA=') && raw.endsWith(';'));
const payload = JSON.parse(raw.slice('globalThis.RESEARCH_DATA='.length, -1));
function supplement(file, prefix) {
  const raw = fs.readFileSync(path.join(directory, file), 'utf8').trim();
  assert(raw.startsWith(prefix) && raw.endsWith(';'));
  return JSON.parse(raw.slice(prefix.length, -1));
}
const geography = supplement('geography_data.js', 'globalThis.RESEARCH_GEOGRAPHY=');
const context = supplement('research_context.js', 'globalThis.RESEARCH_CONTEXT=');
assert(html.includes('name="research-prototype-interface" content="v3"'));

function open(t, geo = geography) {
  const errors = [], console = new VirtualConsole();
  console.on('jsdomError', error => errors.push(error));
  const dom = new JSDOM(html, { runScripts: 'outside-only', virtualConsole: console });
  // No URL/file loader or browser: only audited strings in an isolated test DOM.
  dom.window.fetch = () => { throw new Error('Network calls are not permitted'); };
  dom.window.RESEARCH_DATA = payload;
  dom.window.RESEARCH_GEOGRAPHY = geo;
  dom.window.RESEARCH_CONTEXT = context;
  for (const file of ['research-core.js', 'research-map.js', 'research-app.js']) {
    dom.window.eval(fs.readFileSync(path.join(directory, file), 'utf8'));
  }
  t.after(() => { dom.window.close(); assert.deepEqual(errors, []); });
  return dom;
}
function el(dom, id) { return dom.window.document.getElementById(id); }
function change(dom, id, value) {
  el(dom, id).value = value;
  el(dom, id).dispatchEvent(new dom.window.Event('change', { bubbles: true }));
}
function counts(dom) {
  return ['recordCount','scoredCount','sourceCount','cellCount']
    .map(id => Number(el(dom, id).textContent.replaceAll('.', '')));
}

test('actual app initializes cards and paginated rows without browser or network', t => {
  const dom = open(t);
  assert.deepEqual(counts(dom), [6573,4841,225,185]);
  assert.equal(el(dom,'body').children.length,80);
  assert.equal(el(dom,'range').textContent,'1–80');
  assert.equal(el(dom,'prev').disabled,true);
});
test('Mersin province filter explains the reported 2038 records', t => {
  const dom=open(t);
  change(dom,'province','Mersin');
  assert.deepEqual(counts(dom),[2038,1576,74,49]);
  assert.match(el(dom,'count').textContent,/2\.038 \/ 6\.573/);
});
test('separate Mersin calendar has its own source and quality counts', t => {
  const dom=open(t);
  change(dom,'cohort','separate_Mersin');
  assert.deepEqual(counts(dom),[2383,1929,81,68]);
});
test('row click and keyboard selection build daily chart and 27 actual feature rows', t => {
  const dom=open(t), doc=dom.window.document;
  change(dom,'quality','eligible');
  const row=el(dom,'body').children[1];
  const grid=row.children[1].textContent, date=row.children[0].textContent;
  row.click();
  assert.match(el(dom,'detail').querySelector('h2').textContent,new RegExp(grid));
  assert(el(dom,'detail').querySelector('h2').textContent.includes(date));
  const featureTable=[...el(dom,'detail').querySelectorAll('details')]
    .find(d=>d.querySelector('summary').textContent==='27 çevresel özellik');
  assert.equal(featureTable.querySelectorAll('tbody tr').length,27);
  const svg=el(dom,'detail').querySelector('svg');
  assert(svg && svg.querySelectorAll('circle').length>0);
  for(const point of svg.querySelectorAll('circle')) {
    assert(Number.isFinite(Number(point.getAttribute('cx'))));
    assert(Number.isFinite(Number(point.getAttribute('cy'))));
  }
  const first=el(dom,'body').children[0], title=first.children[1].textContent;
  first.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
  assert(doc.querySelector('#detail h2').textContent.includes(title));
});
if(html.includes('name="research-prototype-interface" content="v3"')) {
  test('score card is explicit and active province context is visible', t => {
    const dom=open(t);
    assert.match(el(dom,'scoredCount').parentElement.textContent,/Puan hesaplanan kayıt/);
    change(dom,'province','Mersin');
    assert.match(el(dom,'activeFilters').textContent,/İl ek filtresi: Mersin/);
    assert.deepEqual(counts(dom),[2038,1576,74,49]);
  });
  test('changing calendar clears dependent province and cell filters', t => {
    const dom=open(t);
    change(dom,'province','Mersin');
    change(dom,'cell',payload.records.find(r=>r.cohort==='four_province').grid);
    change(dom,'cohort','separate_Mersin');
    assert.equal(el(dom,'province').value,'');assert.equal(el(dom,'cell').value,'');
    assert.deepEqual(counts(dom),[2383,1929,81,68]);
    assert.match(el(dom,'activeFilters').textContent,/İl ek filtresi: Tümü/);
  });
}
test('pagination moves 80 rows and empty results reset correctly', t => {
  const dom=open(t), before=el(dom,'body').children[0].textContent;
  el(dom,'next').click();
  assert.equal(el(dom,'range').textContent,'81–160');
  assert.notEqual(el(dom,'body').children[0].textContent,before);
  el(dom,'prev').click();
  assert.equal(el(dom,'body').children[0].textContent,before);
  change(dom,'start','2022-12-31');change(dom,'end','2022-12-31');
  assert.deepEqual(counts(dom),[0,0,0,0]);
  assert.equal(el(dom,'body').children.length,0);
  assert.match(el(dom,'detail').textContent,/kayıt bulunamadı/);
  el(dom,'reset').click();assert.deepEqual(counts(dom),[6573,4841,225,185]);
});
test('all nine view settings update context counts while preserving quality support', t => {
  const dom=open(t);
  const source=[225,223,221,220,218,215,242,239,237];
  source.forEach((n,i)=>{change(dom,'scenario',String(i));assert.deepEqual(counts(dom),[6573,4841,n,185]);});
});
test('unsupported records remain visible and never receive a zero score', t => {
  const dom=open(t);change(dom,'quality','unavailable');
  assert.equal(counts(dom)[0],1732);assert.equal(counts(dom)[1],0);
  for(const row of el(dom,'body').children) assert.equal(row.lastElementChild.textContent,'—');
  assert.match(el(dom,'detail').textContent,/eksik|desteği|koşulları/i);
});

test('map covers filtered cell keys, uses selection color and preserves row counts', t => {
  const dom = open(t), svg = el(dom, 'locationMap').querySelector('svg');
  const cells = svg.querySelectorAll('[data-grid-id]');
  const expected = new Set(payload.records.filter(r => r.cohort === 'four_province').map(r => r.grid));
  const mapped = [...expected].filter(id => geography.cells[id]);
  assert.equal(cells.length, mapped.length);
  assert.equal(svg.querySelectorAll('.selected-cell').length, 1);
  assert.match(svg.getAttribute('aria-label'), /hücrelerin konumu/);
  const candidate = [...cells].find(c => c.getAttribute('aria-pressed') === 'false');
  const id = candidate.getAttribute('data-grid-id');
  candidate.dispatchEvent(new dom.window.MouseEvent('click', {bubbles: true}));
  assert.equal(el(dom, 'cell').value, id);
  assert.equal(counts(dom)[0], payload.records.filter(r => r.cohort === 'four_province' && r.grid === id).length);
  assert(el(dom, 'detail').querySelector('h2').textContent.includes(id));
  assert.equal(svg.querySelectorAll('[data-grid-id]').length, mapped.length);
  el(dom, 'mapClear').click();
  assert.deepEqual(counts(dom), [6573, 4841, 225, 185]);
});

test('map keyboard selection and zoom have finite view boxes and reset', t => {
  const dom = open(t), svg = el(dom, 'locationMap').querySelector('svg');
  const original = svg.getAttribute('viewBox');
  const target = [...svg.querySelectorAll('[data-grid-id]')].find(p => p.getAttribute('aria-pressed') === 'false');
  const id = target.getAttribute('data-grid-id');
  target.dispatchEvent(new dom.window.KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
  assert.equal(el(dom, 'cell').value, id);
  el(dom, 'mapFocus').click();
  const zoom = svg.getAttribute('viewBox').split(' ').map(Number);
  assert(zoom.every(Number.isFinite) && zoom[2] > 0 && zoom[3] > 0);
  assert(zoom[2] < Number(original.split(' ')[2]));
  el(dom, 'mapOverview').click(); assert.equal(svg.getAttribute('viewBox'), original);
  change(dom, 'province', 'Mersin');
  const ids = new Set(payload.records.filter(r => r.cohort === 'four_province' && r.province.split('|').includes('Mersin')).map(r => r.grid));
  assert.equal(svg.querySelectorAll('[data-grid-id]').length, [...ids].filter(id => geography.cells[id]).length);
});

test('all twelve fixed examples select the exact existing row and monthly context', t => {
  const dom = open(t);
  assert.equal(el(dom, 'exampleJump').options.length, 13);
  for (const example of context.examples) {
    change(dom, 'exampleJump', example.case_id);
    assert.equal(el(dom, 'cohort').value, example.cohort);
    assert.equal(el(dom, 'cell').value, example.grid);
    const title = el(dom, 'detail').querySelector('h2').textContent;
    assert(title.includes(example.grid) && title.includes(example.time.slice(0, 10)));
    assert.equal(el(dom, 'start').value, example.time.slice(0, 7) + '-01');
    const exact = payload.records.find(r => r.cohort === example.cohort && r.grid === example.grid && r.time === example.time);
    assert(exact && exact.eligible && exact.flags === 511);
    assert.equal(el(dom, 'body').querySelectorAll('.selected').length, 1);
  }
});

test('missing geometry keeps scientific rows and scores available', t => {
  const first = payload.records.find(r => r.cohort === 'four_province' && r.eligible);
  const geo = {...geography, cells: {...geography.cells}};
  delete geo.cells[first.grid];
  const dom = open(t, geo);
  change(dom, 'cell', first.grid);
  assert(counts(dom)[0] > 0 && counts(dom)[1] > 0);
  assert.equal(el(dom, 'mapFocus').disabled, true);
  assert.match(el(dom, 'mapSelection').textContent, /kayıt korunuyor/);
  assert(el(dom, 'detail').querySelector('h2').textContent.includes(first.grid));
});

test('completed findings use frozen context and local evidence links only', t => {
  const dom = open(t);
  const table = el(dom, 'studySummary').querySelector('table');
  assert.equal(table.querySelectorAll('tbody tr').length, 3);
  assert.match(table.textContent, /65 gün/); assert.match(table.textContent, /59 gün/);
  for (const link of el(dom, 'evidenceLinks').querySelectorAll('a')) {
    assert(!/^(https?:|data:|javascript:)/i.test(link.getAttribute('href')));
    assert.equal(link.rel, 'noopener');
  }
  assert(!el(dom, 'locationMap').querySelector('image'));
});
