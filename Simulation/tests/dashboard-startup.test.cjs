const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'frontend/data/app-data.json'), 'utf8'));

function makeContext(fetchImpl) {
  const elements = new Map();
  const makeElement = () => ({
    dataset: {}, textContent: '', innerHTML: '', onclick: null,
    classList: { toggle() {}, remove() {}, add() {} },
    addEventListener() {}, querySelector() { return null; }
  });
  const doc = {
    documentElement: { dataset: {} },
    addEventListener(event, callback) { if (event === 'DOMContentLoaded') this.ready = callback; },
    querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, makeElement());
      return elements.get(selector);
    },
    querySelectorAll() { return []; }
  };
  const win = { location: { href: 'http://127.0.0.1:8000/', reload() {} }, scrollTo() {} };
  const context = {
    console: { error() {}, warn() {}, log() {} }, document: doc, window: win,
    localStorage: { getItem() { return null; }, setItem() {} },
    setInterval() { return 1; }, clearInterval() {}, setTimeout() {},
    URL, Blob, fetch: fetchImpl
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(root, 'frontend/simulation-engine.js'), 'utf8'), context);
  vm.runInContext(fs.readFileSync(path.join(root, 'frontend/app.js'), 'utf8'), context);
  return { context, elements };
}

test('startup fetches, validates and renders the bundled dataset before reporting DATA READY', async () => {
  const { context, elements } = makeContext(async url => ({
    ok: true, status: 200, json: async () => data
  }));
  await vm.runInContext('init()', context);
  const view = elements.get('#view-root');
  const ready = elements.get('#ready-label');
  assert.ok(view.innerHTML.includes('Command centre'));
  assert.ok(view.innerHTML.includes('PRIMARY DATA ROWS'));
  assert.equal(ready.textContent, 'DATA READY');
});

test('a failed data request is reported as a data error, not a rendering error', async () => {
  const { context, elements } = makeContext(async () => { throw new Error('Synthetic network failure'); });
  await vm.runInContext('init()', context);
  const view = elements.get('#view-root');
  const ready = elements.get('#ready-label');
  assert.ok(view.innerHTML.includes('Research data could not be loaded'));
  assert.ok(view.innerHTML.includes('Synthetic network failure'));
  assert.equal(ready.textContent, 'DATA UNAVAILABLE');
});
