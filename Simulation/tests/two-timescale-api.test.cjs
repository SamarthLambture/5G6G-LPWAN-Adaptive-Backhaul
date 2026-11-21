const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const app = fs.readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');
const api = fs.readFileSync(path.join(__dirname, '../backend/api.py'), 'utf8');
const frameworkControllerPath = path.resolve(__dirname, '../../Framework/src/core/algorithms.py');
const frameworkAvailable = fs.existsSync(frameworkControllerPath);
const frameworkController = frameworkAvailable ? fs.readFileSync(frameworkControllerPath, 'utf8') : null;

test('laboratory exposes a separate fresh Python/SimPy run for the two-timescale controller', () => {
  assert.match(app, /data-action="simpy-tsc"/);
  assert.match(app, /startFreshSimpy\('TSC'\)/);
  assert.match(app, /controller_diagnostics/);
  assert.match(app, /Math\.min\(demo\.duration,180\)/);
  assert.match(app, /useDefaultTscOutage/);
});

test('FastAPI accepts TSC and constructs it from the documented configuration', () => {
  assert.match(api, /"TSC"/);
  assert.match(api, /load_two_timescale_config\(\)/);
  assert.match(api, /initial_arrival_rate_pps=req\.arrival_rate_pps/);
  if (frameworkAvailable) {
    assert.match(frameworkController, /class TwoTimescale\(/);
  } else {
    assert.match(api, /framework_missing_files\(\)/);
    assert.match(api, /missing_framework_files/);
  }
});

test('optional SimPy bridge explicitly requires the sibling Framework directory', () => {
  assert.match(api, /REPO_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[2\]/);
  assert.match(api, /Missing Framework source files/);
  assert.match(api, /status_code=503/);
});

test('impact page distinguishes implemented TSC mechanisms and completed validation from limitations', () => {
  assert.match(app, /Session\/burst decision/);
  assert.match(app, /EWMA \+ Poisson cluster estimate/);
  assert.match(app, /Packet-level protection/);
  assert.match(app, /New TSC paired matrix/);
  assert.match(app, /30 operating conditions/);
  assert.match(app, /What the matrix does not establish/);
  assert.doesNotMatch(app, /These proposed features are not implemented in the current project or browser simulation/);
});
