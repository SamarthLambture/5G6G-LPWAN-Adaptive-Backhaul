const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const frontend = path.join(root, 'frontend');
const html = fs.readFileSync(path.join(frontend, 'index.html'), 'utf8');
const app = fs.readFileSync(path.join(frontend, 'app.js'), 'utf8');

test('HTML entry-point scripts, stylesheet and logo exist', () => {
  const refs = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map(m => m[1]);
  for (const ref of refs) {
    if (/^(https?:|data:|#)/i.test(ref)) continue;
    assert.ok(fs.existsSync(path.join(frontend, ref)), `Missing frontend asset: ${ref}`);
  }
});

test('the topology page does not reference an absent parent-project image', () => {
  assert.doesNotMatch(app, /\.\.\/docs\/figures\/unified_backhaul_architecture\.png/);
  assert.match(app, /function renderTopology\(/);
  assert.match(app, /architecture\('5G',true\)/);
});

test('all archived CSV download targets exist', () => {
  const refs = [...app.matchAll(/(?:csvDownload\()'([^']+\.csv)'/g)].map(m => m[1]);
  assert.ok(refs.length >= 3, 'Expected CSV export targets');
  for (const ref of refs) {
    assert.ok(fs.existsSync(path.join(frontend, ref)), `Missing data export: ${ref}`);
  }
});

test('stylesheet has no empty or remote import dependency', () => {
  const css = fs.readFileSync(path.join(frontend, 'app.css'), 'utf8');
  assert.doesNotMatch(css, /@import\s+url\(\s*['\"]['\"]\s*\)/i);
  assert.doesNotMatch(css, /@import\s+url\(\s*['\"]https?:/i);
});
