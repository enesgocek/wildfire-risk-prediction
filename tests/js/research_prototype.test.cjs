const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const core = require('../../scripts/quality/research_prototype_core.js');

function row(time, cohort='four_province', grid='a', eligible=true, score=1, flags=0) {
  return {time,cohort,grid,eligible,province:'Mersin',scores:[[score,score,score]],flags,quality:[1,false,false]};
}
test('ties retain average position and missing is never zero', () => {
  assert.deepEqual(core.positions([5,5,null,2]), [1.5,1.5,null,3]);
});
test('source flag is a scenario context, not absence of fire', () => {
  const r=row('2022-01-01');r.flags=2;
  assert.equal(core.sourceContext(r,0),false);assert.equal(core.sourceContext(r,1),true);
});
test('filters keep cohort, quality and date meanings separate', () => {
  const records=[row('2022-01-01'),row('2022-01-02','four_province','a',false),row('2022-01-01','separate_Mersin')];
  assert.equal(core.filterRows(records,{cohort:'four_province',scenario:0}).length,2);
  assert.equal(core.filterRows(records,{cohort:'four_province',scenario:0,quality:'unavailable'}).length,1);
  assert.equal(core.filterRows(records,{cohort:'four_province',scenario:0,start:'2022-01-02'}).length,1);
});
test('month ranks use original complete context and do not change with source filter', () => {
  const records=[row('2022-01-01','four_province','a',true,2,1),row('2022-01-02','four_province','a',true,4),row('2022-01-03','four_province','a',false,9),row('2022-02-01','four_province','a',true,100)];
  const filtered=core.filterRows(records,{cohort:'four_province',scenario:0,membership:'source'});
  const series=core.monthSeries(records,filtered[0],0);
  assert.equal(series.availableDays,2);assert.deepEqual(series.series[0],[2,1]);
});
test('selection cannot retain a record hidden by changed filters', () => {
  const a=row('2022-01-01'), b=row('2022-01-02');
  assert.equal(core.chooseSelection([b],a),b);assert.equal(core.chooseSelection([],a),null);
});
test('quality explains partial coverage without inventing cloud cause', () => {
  const a=row('2022-01-01','four_province','a',false);a.quality=[0.03,true,false];
  assert.equal(core.qualityReasons(a).length,2);assert(!core.qualityReasons(a).join(' ').includes('bulut'));
});
if(process.env.RESEARCH_PAYLOAD_PATH) {
  test('actual frozen payload has exact filter counts and unchanged 2022-only scope', () => {
    const raw=fs.readFileSync(process.env.RESEARCH_PAYLOAD_PATH,'utf8').trimEnd();
    assert(raw.startsWith('globalThis.RESEARCH_DATA=')&&raw.endsWith(';'));
    const data=JSON.parse(raw.slice('globalThis.RESEARCH_DATA='.length,-1));
    assert.equal(data.records.length,8956);
    for(const [cohort,n,eligible] of [['four_province',6573,4841],['separate_Mersin',2383,1929]]) {
      assert.equal(core.filterRows(data.records,{cohort,scenario:0}).length,n);
      assert.equal(core.filterRows(data.records,{cohort,scenario:0,quality:'eligible'}).length,eligible);
    }
    assert(data.records.every(r=>r.time.startsWith('2022-')&&r.scores.length===9&&r.x.length===27));
    assert.equal(data.scientific_state.target,null);assert.equal(data.scientific_state.fire_risk_validated,false);
  });
}
