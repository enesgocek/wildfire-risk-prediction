(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  function node(tag, attrs, content) {
    const element = document.createElementNS(NS, tag);
    Object.entries(attrs || {}).forEach(([key, value]) => element.setAttribute(key, String(value)));
    if (content !== undefined) element.textContent = content;
    return element;
  }
  function create(host, geo, onSelect) {
    const svg = node('svg', {class: 'location-map', role: 'group', 'aria-label': 'Çalışma alanı ve kayıtlı 5 km hücrelerin konumu'});
    svg.appendChild(node('title', {}, 'Hücre konumları; yangın konumu veya risk sınıfı değildir'));
    const background = node('g', {'aria-hidden': 'true'});
    geo.areas.forEach(path => background.appendChild(node('path', {d: path, class: 'study-area', 'fill-rule': 'evenodd'})));
    svg.appendChild(background);
    const cells = node('g', {class: 'map-cells'});
    svg.appendChild(cells); host.replaceChildren(svg);
    let selected = null;
    function overview() { svg.setAttribute('viewBox', geo.study_view_box.join(' ')); }
    function focus() {
      const cell = selected && geo.cells[selected];
      if (!cell) return;
      const [x0, y0, x1, y1] = cell.display_bounds;
      const width = Math.max(110, (x1 - x0) * 9), height = Math.max(70, (y1 - y0) * 9);
      svg.setAttribute('viewBox', [(x0 + x1 - width) / 2, (y0 + y1 - height) / 2, width, height].join(' '));
    }
    overview();
    return {overview, focus, draw(records, selectedRow) {
      const ids = [...new Set(records.map(r => r.grid))].sort();
      selected = selectedRow ? selectedRow.grid : null;
      const mapped = ids.filter(id => geo.cells[id]);
      cells.replaceChildren();
      mapped.forEach(id => {
        const path = node('path', {d: geo.cells[id].path, class: 'map-cell' + (id === selected ? ' selected-cell' : ''),
          tabindex: 0, role: 'button', 'data-grid-id': id, 'aria-label': id + ' hücresinin kayıtlarını göster',
          'aria-pressed': String(id === selected), 'fill-rule': 'evenodd'});
        path.appendChild(node('title', {}, id + ' · 5 km hücrenin tamamı'));
        const choose = () => {
          onSelect(id);
          [...cells.querySelectorAll('[data-grid-id]')].find(p => p.getAttribute('data-grid-id') === id)?.focus();
        };
        path.addEventListener('click', choose);
        path.addEventListener('keydown', event => {
          if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(); }
        });
        cells.appendChild(path);
      });
      return {visible: ids.length, mapped: mapped.length, missing: ids.length - mapped.length,
        selectedMapped: Boolean(selected && geo.cells[selected])};
    }};
  }
  globalThis.ResearchMap = {create};
})();
