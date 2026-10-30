// Exercise the generated role-navigation script and evidence URL contracts.
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'docs/portfolio.html'), 'utf8');
const projects = JSON.parse(fs.readFileSync(path.join(root, 'data/portfolio_projects.json'), 'utf8'));
const keys = ['cards', 'credit', 'causal', 'demand', 'finance', 'economics', 'treasury', 'insurance'];
assert.deepEqual(projects.map(p => p.key), keys);
assert.ok(!html.includes('__STUDY_') && !html.includes('__PROJECT_CARDS__'));
assert.ok(html.includes('All 8 studies') && html.includes('8 core projects'));
assert.ok(!html.includes('src/mortgage_risk/') && !html.includes('210 historical M5'));
const routes = {all: keys, 'consumer-credit': ['cards', 'credit', 'causal'],
    credit: ['cards', 'credit', 'treasury'], insurance: ['insurance', 'treasury'],
    treasury: ['treasury', 'credit'], finance: ['finance', 'economics'],
    analytics: ['causal', 'demand'], economics: ['economics', 'causal']};
const optionKeys = [...html.matchAll(/<option value="([^"]+)">/g)].map(m => m[1]);
assert.deepEqual(optionKeys, Object.keys(routes));
for (const key of keys) assert.equal(html.split('id="study-' + key + '"').length - 1, 1);
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1);
function environment(initialHash = '') {
    const cards = new Map(keys.map(key => ['study-' + key, {id: 'study-' + key, hidden: false}]));
    const changes = {}, windowEvents = {}, order = [];
    const select = {value: 'all', disabled: true, selectedOptions: [{textContent: 'Role'}],
        addEventListener: (name, callback) => {changes[name] = callback;}};
    const status = {textContent: ''};
    const grid = {appendChild(card) {assert.ok(card); const at = order.indexOf(card.id); if (at !== -1) order.splice(at, 1); order.push(card.id);}};
    const location = {hash: initialHash, pathname: '/portfolio.html', search: '?view=research'};
    const history = {replaceState(_state, _title, value) {
        const target = new URL(value, 'https://example.test');
        assert.equal(target.pathname, '/portfolio.html');
        assert.equal(target.search, '?view=research');
        location.hash = target.hash;
    }};
    const document = {getElementById(id) {return id === 'studies' ? grid : id === 'role-select' ? select : id === 'role-status' ? status : cards.get(id);}};
    const window = {addEventListener(name, callback) {windowEvents[name] = callback;}};
    vm.runInNewContext(scripts[0][1], {document, window, location, history, Map});
    const visible = () => order.filter(id => !cards.get(id).hidden).map(id => id.replace('study-', ''));
    return {cards, changes, windowEvents, select, status, location, visible};
}
const e = environment();
assert.equal(e.select.disabled, false);
assert.deepEqual(e.visible(), keys);
assert.equal(e.status.textContent, 'Showing all 8 studies.');
for (const [route, expected] of Object.entries(routes)) {
    e.select.value = route;
    e.changes.change();
    assert.deepEqual(e.visible(), expected, route);
    assert.equal(e.location.hash, route === 'all' ? '' : '#' + route);
    assert.ok(e.status.textContent.startsWith(route === 'all' ? 'Showing all 8 studies.' : 'Showing ' + expected.length + ' complementary studies for '));
    const direct = environment('#' + route);
    assert.deepEqual(direct.visible(), expected, 'initial hash ' + route);
    assert.equal(direct.select.value, route);
    e.location.hash = '#' + route;
    e.windowEvents.hashchange();
    assert.deepEqual(e.visible(), expected, 'hash event ' + route);
}
for (const hash of ['#unknown', '#__proto__', '#constructor']) {
    e.location.hash = hash; e.windowEvents.hashchange();
    assert.deepEqual(e.visible(), keys);
    assert.equal(e.select.value, 'all');
}
// Check every generated link against its declared project or existing local export.
const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map(m => m[1].replaceAll('&amp;', '&'));
for (const href of hrefs) {
    if (!href.startsWith('https://')) {
        assert.ok(href.startsWith('exports/') && !href.includes('..'));
        assert.ok(fs.statSync(path.join(root, 'docs', href)).isFile(), href);
        continue;
    }
    const target = new URL(href);
    assert.ok(['github.com', 'prasanna-k-123.github.io', 'www.linkedin.com'].includes(target.hostname), href);
}
for (const project of projects) {
    const repository = 'https://github.com/Prasanna-K-123/' + project.repo;
    assert.ok(hrefs.includes(repository));
    const demo = Object.hasOwn(project, 'demo_url') ? project.demo_url : 'https://prasanna-k-123.github.io/' + project.repo + '/';
    if (demo) assert.ok(hrefs.includes(demo));
    else assert.ok(!hrefs.includes('https://prasanna-k-123.github.io/' + project.repo + '/'));
    for (const item of project.evidence) {
        assert.ok(!item.path.startsWith('/') && !item.path.split('/').includes('..'));
        const kind = item.path.endsWith('/') ? 'tree' : 'blob';
        assert.ok(hrefs.includes(repository + '/' + kind + '/main/' + item.path));
    }
}
const card = projects.find(project => project.key === 'cards');
assert.equal(card.demo_url, 'https://prasanna-k-123.github.io/financial-decision-lab/consumer-credit.html');
assert.ok(fs.statSync(path.join(root, 'docs/consumer-credit.html')).isFile());
assert.ok(card.description.includes('Taiwanese') && card.description.includes('separate 56-quarter US'));
assert.ok(card.description.includes('not joined') && card.methods.includes('independent SQL'));
console.log(JSON.stringify({passed: true, projects: keys.length, role_routes: Object.keys(routes).length,
    evidence_links: hrefs.length, hash_navigation_and_unknown_fallback: true,
    dynamic_route_counts: true, actual_embedded_script: true,
    scope: 'DOM model and URL/local-export contracts; live remote availability and browser layout are checked separately.'}));
