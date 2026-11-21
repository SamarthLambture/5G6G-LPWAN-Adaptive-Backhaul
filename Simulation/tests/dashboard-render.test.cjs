const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'frontend/data/app-data.json'), 'utf8'));
const context = {
  console,
  document: { addEventListener() {} },
  window: {},
  localStorage: { getItem() { return null; }, setItem() {} },
  setInterval() { return 1; },
  clearInterval() {},
  setTimeout() {},
  URL,
  Blob,
  __data: data
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'frontend/simulation-engine.js'), 'utf8'), context);
vm.runInContext(fs.readFileSync(path.join(root, 'frontend/app.js'), 'utf8'), context);
vm.runInContext('D=__data; LPWANEngine=window.LPWANEngine; demo=initDemo();', context);

const renderers = [
  ['renderOverview', 'Command centre'],
  ['renderTopology', 'Network topology'],
  ['renderLab', 'Interactive network laboratory'],
  ['renderDecision', 'Decision inspector'],
  ['renderBackhaul', 'Backhaul comparison'],
  ['renderAnalytics', 'Performance analytics'],
  ['renderExperiments', 'Experiment explorer'],
  ['renderExplainer', 'Project explainer'],
  ['renderImpact', 'Our modifications & performance impact'],
  ['renderViva', 'Viva mode'],
  ['renderIntegrity', 'Data integrity and provenance']
];

test('all 11 dashboard views render from the bundled research JSON', () => {
  for (const [fn, expected] of renderers) {
    const html = vm.runInContext(`${fn}()`, context);
    assert.equal(typeof html, 'string', `${fn} should return HTML`);
    assert.ok(html.length > 500, `${fn} should not return an empty shell`);
    assert.ok(html.includes(expected), `${fn} should render its expected page title`);
  }
});

test('default route points to an existing landing-page renderer and Viva has its question bank', () => {
  const source = fs.readFileSync(path.join(root, 'frontend/app.js'), 'utf8');
  assert.match(source, /let D=null,view='overview'/);
  assert.match(source, /function renderOverview\(/);
  assert.match(source, /const QAS = \[/);
});

test('browser-side packet simulation advances and processes 1,000 seeded packets', () => {
  vm.runInContext('render=()=>{}; for(let i=0;i<1000;i++) stepPacket();', context);
  const result = JSON.parse(vm.runInContext('JSON.stringify({generated:demo.generated, delivered:demo.delivered, time:demo.time})', context));
  assert.equal(result.generated, 1000);
  assert.ok(result.time > 0);
  assert.ok(result.delivered > 0);
  assert.ok(result.delivered <= result.generated);
});
