'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');

const directory = path.resolve(process.env.RESEARCH_PROTOTYPE_DIR ||
  'outputs/reports/dataset/historical_research_prototype_v1/20261123T144811Z_555ee371');
const html = fs.readFileSync(path.join(directory, 'inceleme.html'), 'utf8');
const raw = fs.readFileSync(path.join(directory, 'review_data.js'), 'utf8').trimEnd();
assert(raw.startsWith('globalThis.RESEARCH_DATA=') && raw.endsWith(';'));
const payload = JSON.parse(raw.slice('globalThis.RESEARCH_DATA='.length, -1));

function open(t) {
  const errors = [], console = new VirtualConsole();
  console.on('jsdomError', error => errors.push(error));
  const dom = new JSDOM(html, { runScripts: 'outside-only', virtualConsole: console });
  // No URL/file loader or browser: only audited strings in an isolated test DOM.
  dom.window.fetch = () => { throw new Error('Network calls are not permitted'); };
  dom.window.RESEARCH_DATA = payload;
  for (const file of ['research-core.js', 'research-app.js']) {
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
if(html.includes('name="research-prototype-interface" content="v2"')) {
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
