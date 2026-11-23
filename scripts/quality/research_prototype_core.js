(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ResearchReview = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function sourceContext(row, scenario) { return Boolean(row.flags & (1 << scenario)); }
  function filterRows(rows, options) {
    return rows.filter(r =>
      r.cohort === options.cohort &&
      (!options.province || r.province.split('|').includes(options.province)) &&
      (!options.cell || r.grid === options.cell) &&
      (!options.start || r.time.slice(0, 10) >= options.start) &&
      (!options.end || r.time.slice(0, 10) <= options.end) &&
      (!options.quality || (options.quality === 'eligible' ? r.eligible : !r.eligible)) &&
      (!options.membership || (options.membership === 'source' ? sourceContext(r, options.scenario) : !sourceContext(r, options.scenario))));
  }
  function positions(values) {
    const finite = values.filter(Number.isFinite);
    return values.map(v => Number.isFinite(v)
      ? 1 + finite.filter(x => x > v).length + (finite.filter(x => x === v).length - 1) / 2
      : null);
  }
  function monthSeries(allRows, selected, scenario) {
    const records = allRows.filter(r => r.cohort === selected.cohort && r.grid === selected.grid &&
      r.time.slice(0, 7) === selected.time.slice(0, 7) && r.eligible)
      .sort((a, b) => a.time.localeCompare(b.time));
    const series = [0, 1, 2].map(variant => positions(records.map(r => r.scores[scenario][variant])));
    return { records, series, availableDays: records.length };
  }
  function chooseSelection(rows, previous) {
    return rows.find(r => previous && r.cohort === previous.cohort && r.grid === previous.grid && r.time === previous.time) || rows[0] || null;
  }
  function qualityReasons(row) {
    const reasons = [];
    if (row.quality[0] === 0) reasons.push('Meteorolojide geçerli alan desteği yok');
    else if (row.quality[0] < 1 - 1e-9) reasons.push('Meteoroloji alan desteği tam değil');
    if (row.quality[1]) reasons.push('30 günlük bitki örtüsü alanları eksik');
    if (row.quality[2]) reasons.push('60 günlük bitki örtüsü alanları eksik');
    if (!row.eligible && !reasons.length) reasons.push('Ana kalite ve tam girdi koşulları sağlanmıyor');
    return reasons;
  }
  return { sourceContext, filterRows, positions, monthSeries, chooseSelection, qualityReasons };
});
