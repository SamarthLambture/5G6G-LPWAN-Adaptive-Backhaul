const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const appSource = fs.readFileSync(path.join(root, 'frontend/app.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'frontend/index.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'frontend/data/app-data.json'), 'utf8'));

function extractFunction(name, nextName) {
  const start = appSource.indexOf(`function ${name}(`);
  const end = appSource.indexOf(`\nfunction ${nextName}(`, start);
  assert.ok(start >= 0 && end > start, `Could not extract ${name}`);
  return appSource.slice(start, end);
}

const renderSource = extractFunction('renderImpact', 'renderViva');
const context = {
  D: data,
  C: { NB:'#f2a34a', '5G':'#43c6d7', AHP:'#b69aff' },
  base: id => data.baseline.find(x => x.Algorithm === id) || {},
  pct: x => (Number(x) * 100).toFixed(2) + '%',
  fmt: (x,n=2) => Number(x).toFixed(n),
  num: x => Number(x).toLocaleString('en-IN'),
  pageHead: (title, sub, actions='') => `<header><h1>${title}</h1><p>${sub}</p>${actions}</header>`,
  chartBars: (title, labels, series, opt={}) => `<div data-chart="${title}"></div>`,
  panel: (title, sub, body) => `<section><h3>${title}</h3><p>${sub}</p>${body}</section>`,
  kpi: (label, value, foot) => `<div data-kpi="${label}">${value}<small>${foot}</small></div>`
};
vm.createContext(context);
vm.runInContext(renderSource, context);

 test('impact page renders the complete modification-to-result story', () => {
  const htmlOut = vm.runInContext('renderImpact()', context);
  for (const phrase of [
    'Original/reference system', 'What the upgrade added',
    'Primary baseline: fixed NB-IoT vs fixed 5G vs adaptive AHP-TOPSIS',
    'New TSC paired matrix', 'Where TSC is statistically different',
    'What the matrix does not establish', 'Condition-wise statistically significant end-to-end results'
  ]) assert.ok(htmlOut.includes(phrase), `Missing section: ${phrase}`);
});

test('impact page uses recorded baseline values and does not claim superiority over fixed 5G', () => {
  const htmlOut = vm.runInContext('renderImpact()', context);
  assert.ok(htmlOut.includes('86.83%'));
  assert.ok(htmlOut.includes('99.02%'));
  assert.ok(htmlOut.includes('2.8689 s'));
  assert.ok(htmlOut.includes('0.0274 s'));
  assert.ok(htmlOut.includes('135.24 J'));
  assert.ok(htmlOut.includes('5,768,175'));
  assert.ok(htmlOut.includes('does not show that adaptive AHP-TOPSIS outperforms fixed 5G'));
  assert.ok(htmlOut.includes('900 paired traces'));
});

test('navigation exposes the new page and render routing includes it', () => {
  assert.match(html, /data-view="impact"/);
  assert.match(appSource, /impact:\['RESEARCH CONTRIBUTION','Our modifications & impact'\]/);
  assert.match(appSource, /impact:renderImpact/);
});

test('impact page renders completed TSC matrix evidence and negative findings', () => {
  const htmlOut = vm.runInContext('renderImpact()', context);
  for (const phrase of ['30 operating conditions', '900 paired traces', '30/30', 'PDR', 'Emergency PDR', '2,436', '2,404', '0.0736%']) {
    assert.ok(htmlOut.includes(phrase), `Missing research evidence: ${phrase}`);
  }
});
