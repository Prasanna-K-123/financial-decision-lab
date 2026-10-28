// Exercise the actual role-navigation script after rebuilding the shared guide.
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'docs/portfolio.html'), 'utf8');
const projects = JSON.parse(fs.readFileSync(path.join(root, 'data/portfolio_projects.json'), 'utf8'));
const keys = ['demand', 'causal', 'credit', 'finance', 'economics', 'treasury', 'insurance'];
assert.deepEqual(projects.map(p => p.key), keys);
const cards = new Map(keys.map(key => ['study-' + key, {id: 'study-' + key, hidden: false}]));
for (const id of cards.keys()) assert.equal(html.split('id="' + id + '"').length - 1, 1);
assert.ok(!html.includes('src/mortgage_risk/') && !html.includes('210 historical M5'));
const routes = {all: keys, credit: ['credit', 'treasury'], insurance: ['insurance', 'treasury'],
    treasury: ['treasury', 'credit'], finance: ['finance', 'economics'],
    analytics: ['causal', 'demand'], economics: ['economics', 'causal']};
const changes = {}, windowEvents = {}, order = [];
const select = {value: 'all', disabled: true, selectedOptions: [{textContent: 'Role'}],
    addEventListener: (name, callback) => {changes[name] = callback;}};
const status = {textContent: ''};
const grid = {appendChild(card) {const at = order.indexOf(card.id); if (at !== -1) order.splice(at, 1); order.push(card.id);}};
const location = {hash: '', pathname: '/portfolio.html', search: ''};
const history = {replaceState(_state, _title, value) {location.hash = new URL(value, 'https://example.test').hash;}};
const document = {getElementById(id) {return id === 'studies' ? grid : id === 'role-select' ? select : id === 'role-status' ? status : cards.get(id);}};
const window = {addEventListener(name, callback) {windowEvents[name] = callback;}};
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1);
vm.runInNewContext(scripts[0][1], {document, window, location, history, Map});
assert.equal(select.disabled, false);
function visible() {return order.filter(id => !cards.get(id).hidden).map(id => id.replace('study-', ''));}
assert.deepEqual(visible(), keys);
for (const [route, expected] of Object.entries(routes)) {
    select.value = route;
    changes.change();
    assert.deepEqual(visible(), expected, route);
    assert.equal(location.hash, route === 'all' ? '' : '#' + route);
}
location.hash = '#economics'; windowEvents.hashchange();
assert.deepEqual(visible(), routes.economics);
location.hash = '#unknown'; windowEvents.hashchange();
assert.deepEqual(visible(), keys);
assert.equal(select.value, 'all');
console.log(JSON.stringify({passed: true, projects: keys.length, role_routes: Object.keys(routes).length,
    hash_navigation_and_unknown_fallback: true, actual_embedded_script: true,
    scope: 'DOM model; native browser layout, accessibility and live links are separate.'}));
