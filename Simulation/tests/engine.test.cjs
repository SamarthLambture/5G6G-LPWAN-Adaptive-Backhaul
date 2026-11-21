const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../frontend/simulation-engine.js');
const D = require('../frontend/data/app-data.json');
const params = {
  NB:{bandwidth_bps:66000,base_latency_s:.5,setup_delay_s:1.5,setup_energy_j:1.5,tx_power_w:1,reliability_pct:95},
  '5G':{bandwidth_bps:100000000,base_latency_s:.02,setup_delay_s:.1,setup_energy_j:.5,tx_power_w:3,reliability_pct:99}
};
test('state classification covers all four states and exact 20% boundary',()=>{
 assert.equal(E.classifyState(false,20),'NORMAL'); assert.equal(E.classifyState(false,19.99),'LOW_BATTERY');
 assert.equal(E.classifyState(true,20),'EMERGENCY'); assert.equal(E.classifyState(true,19.99),'CONFLICT');
});
test('invalid battery percentages are rejected',()=>{assert.throws(()=>E.classifyState(false,-1),RangeError);assert.throws(()=>E.classifyState(false,101),RangeError)});
test('AHP weights match canonical state vectors and sum to one',()=>{
 for(const [s,w] of Object.entries(E.WEIGHTS)){assert.ok(Math.abs(w.reduce((a,b)=>a+b,0)-1)<1e-12);assert.deepEqual(E.weightsForState(s),w)}
});
test('pairwise comparison matrix is reciprocal and consistent by construction',()=>{
 const a=E.pairwiseMatrix(E.WEIGHTS.NORMAL);for(let i=0;i<4;i++)for(let j=0;j<4;j++)assert.ok(Math.abs(a[i][j]*a[j][i]-1)<1e-12);
});
test('normalisation is column-wise unit norm',()=>{
 const n=E.vectorNormalize([[3,4],[4,3]]);for(let j=0;j<2;j++)assert.ok(Math.abs(Math.hypot(n[0][j],n[1][j])-1)<1e-12);
});
test('TOPSIS chooses a candidate better on all four criteria',()=>{
 const r=E.rankTOPSIS([{id:'NB',values:[2,2,90,50]},{id:'5G',values:[1,1,99,100]}],[.25,.25,.25,.25]);assert.equal(r.selected,'5G');
});
test('TOPSIS does not execute with zero candidates',()=>{const r=E.rankTOPSIS([],E.WEIGHTS.NORMAL);assert.equal(r.selected,null);assert.equal(r.rows.length,0)});
test('one feasible candidate bypasses TOPSIS',()=>{const c={id:'NB'};const r=E.rankTOPSIS([c],E.WEIGHTS.NORMAL);assert.equal(r.selected,'NB');assert.equal(r.rows[0].closeness,null)});
test('fixed NB-IoT does not fall back when only 5G is feasible',()=>{const r=E.choose('NB',[{id:'5G'}],E.WEIGHTS.NORMAL);assert.equal(r.selected,null)});
test('fixed 5G does not fall back when only NB-IoT is feasible',()=>{const r=E.choose('5G',[{id:'NB'}],E.WEIGHTS.NORMAL);assert.equal(r.selected,null)});
test('latency-first and energy-first select their respective minima',()=>{
 const c=[{id:'NB',predictedLatency:2,instantEnergy:1},{id:'5G',predictedLatency:1,instantEnergy:2}];assert.equal(E.choose('LAT',c,E.WEIGHTS.NORMAL).selected,'5G');assert.equal(E.choose('ENG',c,E.WEIGHTS.NORMAL).selected,'NB');
});
test('evaluation enforces the emergency one-second deadline',()=>{
 const x=E.evaluate({payloadBytes:200,emergency:true,batteryPct:100,algorithm:'AHP',backhauls:params,availability:{NB:true,'5G':true},modemStates:{NB:'SLEEP','5G':'SLEEP'}});
 assert.equal(x.deadline,1);assert.equal(x.nb.feasible,false);assert.equal(x.g5.feasible,true);assert.equal(x.selected,'5G');
});
test('evaluation returns no selected path when both alternatives are unavailable',()=>{
 const x=E.evaluate({payloadBytes:50,emergency:false,batteryPct:100,algorithm:'AHP',backhauls:params,availability:{NB:false,'5G':false}});assert.equal(x.selected,null);assert.deepEqual(x.feasible,[]);
});
test('archived data has the expected primary and separate pilot boundaries',()=>{
 assert.equal(D.source.primary_rows,4320);assert.equal(D.source.scenario_count,24);assert.equal(D.source.seed_count,30);assert.equal(D.source.algorithm_count,6);assert.equal(D.source.supplementary_outage_rows,30);
});
test('archived baseline confirms 5G and adaptive AHP are equal in baseline',()=>{
 const a=D.baseline.find(x=>x.Algorithm==='AHP'),g=D.baseline.find(x=>x.Algorithm==='5G');assert.ok(Math.abs(a.PDR_Mean-g.PDR_Mean)<1e-12);assert.ok(Math.abs(a.Avg_Lat_s_Mean-g.Avg_Lat_s_Mean)<1e-12);
});
