(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const payload = globalThis.RESEARCH_DATA, core = globalThis.ResearchReview;
  if (!payload || !core) { $('count').textContent = 'Veri yüklenemedi. Prototip dosyalarının aynı klasörde bulunduğunu kontrol et.'; return; }
  const rows = payload.records, size = 80;
  const names = { Antalya: 'Antalya', Izmir: 'İzmir', Mugla: 'Muğla', Mersin: 'Mersin', not_in_original_package_area_mapping: 'Mevcut alan eşlemesinde yok' };
  const number = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 4 });
  const fmt = value => value === null || value === undefined ? 'Hesaplanmadı' : number.format(value);
  const provinceText = value => value.split('|').map(x => names[x] || x).join(' / ');
  function option(select, value, text) { const o = document.createElement('option'); o.value = value; o.textContent = text; select.appendChild(o); }
  payload.scenarios.forEach((s, i) => option($('scenario'), i, s.replace('d', '').replace('m_t', ' m / ').replace('h', ' saat')));
  ['Antalya', 'Izmir', 'Mersin', 'Mugla'].forEach(p => option($('province'), p, names[p]));
  [...new Set(rows.map(r => r.grid))].sort().forEach(g => option($('cell'), g, g));
  let filtered = [], page = 0, selected = null;
  function settings() { return { cohort: $('cohort').value, scenario: Number($('scenario').value), province: $('province').value, cell: $('cell').value, start: $('start').value, end: $('end').value, quality: $('quality').value, membership: $('membership').value }; }
  function text(tag, value, className) { const e = document.createElement(tag); e.textContent = value; if (className) e.className = className; return e; }
  function td(tr, value, numeric) { const cell = text('td', value, numeric ? 'num' : ''); tr.appendChild(cell); }
  function table(entries, headers) {
    const t = document.createElement('table'); t.className = 'detailtable';
    if (headers) { const head = document.createElement('thead'), tr = document.createElement('tr'); headers.forEach(h => tr.appendChild(text('th', h))); head.appendChild(tr); t.appendChild(head); }
    const body = document.createElement('tbody'); entries.forEach(values => { const tr = document.createElement('tr'); values.forEach(v => td(tr, v)); body.appendChild(tr); }); t.appendChild(body); return t;
  }
  function svgElement(tag, attrs, value) { const e = document.createElementNS('http://www.w3.org/2000/svg', tag); Object.entries(attrs || {}).forEach(([k, v]) => e.setAttribute(k, v)); if (value !== undefined) e.textContent = value; return e; }
  function chart(row, scenario, host) {
    const context = core.monthSeries(rows, row, scenario), data = context.records, n = data.length;
    if (!n) { host.appendChild(text('p', 'Bu hücre ve ayda ana kalite kuralına uygun gün bulunmuyor.')); return; }
    host.appendChild(text('p', row.time.slice(0, 7) + ' · ' + n + ' uygun gün · 1. sıra en yüksek kaynak-bağlamı puanı'));
    const svg = svgElement('svg', { viewBox: '0 0 650 245', class: 'chart', role: 'img', 'aria-label': 'Aynı hücre ve aydaki uygun günlerin deneysel sıra karşılaştırması' });
    svg.appendChild(svgElement('title', {}, 'Kaynak-bağlamı sırası; yangın olasılığı değildir'));
    const x = day => 52 + (day - 1) / 30 * 570, y = rank => 25 + (rank - 1) / Math.max(n - 1, 1) * 170;
    [1, Math.ceil(n / 2), n].filter((v, i, a) => a.indexOf(v) === i).forEach(v => { svg.appendChild(svgElement('line', { x1: 50, x2: 625, y1: y(v), y2: y(v), stroke: '#dce5ee' })); svg.appendChild(svgElement('text', { x: 35, y: y(v) + 5, 'font-size': 13, 'text-anchor': 'end', fill: '#52647a' }, v)); });
    [1, 5, 10, 15, 20, 25, 31].forEach(v => svg.appendChild(svgElement('text', { x: x(v), y: 222, 'font-size': 13, 'text-anchor': 'middle', fill: '#52647a' }, v)));
    svg.appendChild(svgElement('text', { x: 620, y: 242, 'font-size': 13, 'text-anchor': 'end', fill: '#52647a' }, 'Ayın günü (UTC)'));
    const labels = ['Tam alanla öğrenen XGBoost', 'Önceki geniş alan XGBoost', 'Önceki doğrusal model'];
    ['#145f9d', '#b36b18', '#66717f'].forEach((color, variant) => {
      let segment = [];
      function drawSegment() { if (segment.length > 1) svg.appendChild(svgElement('polyline', { points: segment.join(' '), fill: 'none', stroke: color, 'stroke-width': variant === 0 ? 2.5 : 1.4, 'stroke-dasharray': variant === 2 ? '5 4' : 'none' })); segment = []; }
      data.forEach((r, i) => { const day = Number(r.time.slice(8, 10)), rank = context.series[variant][i]; if (i && day - Number(data[i - 1].time.slice(8, 10)) !== 1) drawSegment(); segment.push(x(day) + ',' + y(rank)); }); drawSegment();
      data.forEach((r, i) => { const rank = context.series[variant][i], point = svgElement('circle', { cx: x(Number(r.time.slice(8, 10))), cy: y(rank), r: r.time === row.time ? 5 : 2.5, fill: color }); point.appendChild(svgElement('title', {}, r.time.slice(0, 10) + ' · ' + labels[variant] + ' · sıra ' + fmt(rank) + '/' + n)); svg.appendChild(point); });
    });
    host.appendChild(svg);
    const legend = document.createElement('div'); legend.className = 'legend'; labels.forEach((label, i) => legend.appendChild(text('span', ['● ', '■ ', '▲ '][i] + label, ['blue', 'orange', 'grey'][i]))); host.appendChild(legend);
  }
  function detail(row) {
    const host = $('detail'); host.replaceChildren();
    if (!row) { host.appendChild(text('h2', 'Bu filtrelerde kayıt bulunamadı')); return; }
    const scenario = Number($('scenario').value);
    host.appendChild(text('h2', row.grid + ' · ' + row.time.slice(0, 10)));
    host.appendChild(text('p', provinceText(row.province) + ' · Tahmin başlangıcı 00:00 UTC · Gerçek Y/L atanmadı'));
    host.appendChild(text('p', row.eligible ? 'Ana meteoroloji kuralı ve 15 dinamik alan uygun.' : core.qualityReasons(row).join(' · '), 'badge'));
    const columns = document.createElement('div'); columns.className = 'columns compact'; host.appendChild(columns);
    const plot = document.createElement('div'); plot.appendChild(text('h2', 'Aynı yerde günlerin sırası')); columns.appendChild(plot); chart(row, scenario, plot);
    const quality = document.createElement('div'); quality.appendChild(text('h2', 'Kaynak ve kalite bağlamı'));
    quality.appendChild(table([['Kaynak bağlamı', core.sourceContext(row, scenario) ? 'Kayıtlı aday/kaynak günü' : 'Atamasız; yangın yok anlamına gelmez'], ['Meteoroloji alan desteği', fmt(row.quality[0] * 100) + ' %'], ['30 gün bitki örtüsü', row.quality[1] ? 'Eksik' : 'Mevcut'], ['60 gün bitki örtüsü', row.quality[2] ? 'Eksik' : 'Mevcut'], ['Yeni model puanı', row.eligible ? fmt(row.scores[scenario][0]) : 'Hesaplanmadı'], ['Günlük gözlem durumu', 'Bilinmiyor']])); columns.appendChild(quality);
    const variants = document.createElement('details'); variants.appendChild(text('summary', 'Dokuz ayarı aynı kayıt için karşılaştır'));
    variants.appendChild(table(payload.scenarios.map((s, i) => [s, core.sourceContext(row, i) ? 'Kaynak/aday bağlamı' : 'Atamasız', row.eligible ? fmt(row.scores[i][0]) : 'Hesaplanmadı', row.eligible ? fmt(row.scores[i][1]) : 'Hesaplanmadı', row.eligible ? fmt(row.scores[i][2]) : 'Hesaplanmadı']), ['Ayar', 'Bağlam', 'Yeni tam alan', 'Önceki geniş alan', 'Önceki doğrusal'])); host.appendChild(variants);
    const features = document.createElement('details'); features.open = true; features.appendChild(text('summary', '27 çevresel özellik'));
    features.appendChild(table(payload.dictionary.map((f, i) => [f.meaning_tr, row.x[i] === null ? 'Eksik' : fmt(row.x[i]), f.unit]), ['Özellik', 'Değer', 'Birim'])); host.appendChild(features);
    const origin = document.createElement('details'); origin.appendChild(text('summary', 'Kaynak satırına geri dön'));
    origin.appendChild(text('p', 'CSV veri satırı (1’den): ' + (row.origin[2] + 1)));
    origin.appendChild(text('p', 'Özellik dosyası')); origin.appendChild(text('code', payload.paths[row.origin[0]]));
    origin.appendChild(text('p', 'Üyelik dosyası')); origin.appendChild(text('code', payload.paths[row.origin[1]])); host.appendChild(origin);
  }
  function draw() {
    const s = settings(); $('recordCount').textContent = filtered.length.toLocaleString('tr-TR'); $('scoredCount').textContent = filtered.filter(r => r.eligible).length.toLocaleString('tr-TR'); $('sourceCount').textContent = filtered.filter(r => core.sourceContext(r, s.scenario)).length.toLocaleString('tr-TR'); $('cellCount').textContent = new Set(filtered.map(r => r.grid)).size.toLocaleString('tr-TR');
    $('count').textContent = filtered.length.toLocaleString('tr-TR') + ' / ' + rows.filter(r => r.cohort === s.cohort).length.toLocaleString('tr-TR') + ' kayıt · satır seçerek ayrıntıları aç';
    const body = $('body'); body.replaceChildren();
    filtered.slice(page * size, (page + 1) * size).forEach(r => { const tr = document.createElement('tr'); tr.tabIndex = 0; if (selected && r.grid === selected.grid && r.time === selected.time && r.cohort === selected.cohort) tr.className = 'selected';
      [r.time.slice(0, 10), r.grid, provinceText(r.province), core.sourceContext(r, s.scenario) ? 'Kaynak/aday' : 'Atamasız', r.eligible ? 'Ana kalite uygun' : 'Puan hesaplanmadı'].forEach(v => td(tr, v)); td(tr, r.eligible ? fmt(r.scores[s.scenario][0]) : '—', true);
      const select = () => { selected = r; draw(); detail(r); }; tr.addEventListener('click', select); tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(); } }); body.appendChild(tr); });
    $('range').textContent = filtered.length ? (page * size + 1) + '–' + Math.min((page + 1) * size, filtered.length) : '0'; $('prev').disabled = page === 0; $('next').disabled = (page + 1) * size >= filtered.length;
  }
  function apply() { filtered = core.filterRows(rows, settings()); page = 0; selected = core.chooseSelection(filtered, selected); draw(); detail(selected); }
  ['cohort', 'scenario', 'province', 'cell', 'start', 'end', 'quality', 'membership'].forEach(id => $(id).addEventListener('change', apply));
  $('reset').addEventListener('click', () => { ['province', 'cell', 'start', 'end', 'quality', 'membership'].forEach(id => $(id).value = ''); $('scenario').value = '0'; $('cohort').value = 'four_province'; apply(); });
  $('prev').addEventListener('click', () => { page = Math.max(0, page - 1); draw(); }); $('next').addEventListener('click', () => { page++; draw(); });
  $('identity').appendChild(text('p', 'Model koşusu: ' + payload.model_run)); $('identity').appendChild(text('code', payload.model_run_sha256)); $('identity').appendChild(text('p', 'Prototip yönü: 23 Kasım araştırmacı A seçimi; bilimsel hedef doğrulaması veya nihai birleştirme değil.'));
  apply();
})();
