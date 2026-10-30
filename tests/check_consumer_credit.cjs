// Exercise the exact generated browser script against its published evidence.
// Browser layout and live network availability are checked separately.
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'docs/consumer-credit.html'), 'utf8');
const dataMatch = html.match(/<script\b[^>]*\bid=["']evidence-data["'][^>]*>([\s\S]*?)<\/script>/);
assert.ok(dataMatch, 'Published aggregate evidence is embedded');
const evidence = JSON.parse(dataMatch[1]);
const modelKeys = ['scorecard', 'challenger', 'cart'];
const labels = {scorecard: 'WoE logistic', challenger: 'Boosting', cart: 'Shallow CART'};
const ratios = [1, 2, 5, 10, 20], capacities = [0.05, 0.1, 0.2];
const near = (actual, expected, label) => assert.ok(Number.isFinite(+actual) && Math.abs(+actual - expected) <= 2e-10 * Math.max(1, Math.abs(expected)), `${label}: ${actual} != ${expected}`);
const numeric = (row, field) => {assert.ok(Number.isFinite(+row[field]), field); return +row[field];};
assert.equal(evidence.summary.n, 30000);
assert.equal(evidence.summary.partitions.test.n, 6001);
assert.equal(evidence.summary.partitions.test.defaults, 1295);
assert.deepEqual(Object.keys(evidence.summary.models).sort(), [...modelKeys].sort());
assert.equal(evidence.policies.length, 15);
assert.equal(evidence.capacities.length, 9);
assert.equal(evidence.leaves.length, 32);
assert.equal(evidence.provenance.strategy_review_status, 'PASS');
assert.equal(evidence.provenance.original_queues_reconciled, true);
for (const hash of [evidence.provenance.strategy_review_sha256, evidence.provenance.original_queues_sha256,
    evidence.provenance.market_report_sha256, ...Object.values(evidence.provenance.strategy_input_sha256)]) {
    assert.match(hash, /^[a-f0-9]{64}$/);
}
assert.equal(evidence.summary.source_sha256, '30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933');
assert.equal(evidence.market.coverage.quarters, 56);
assert.equal(evidence.market.coverage.first_quarter, '2012Q3');
assert.equal(evidence.market.coverage.last_quarter, '2026Q2');
assert.equal(evidence.market.quality.errors, 0);
assert.equal(evidence.market.source_published_on, '2026-10-07');
for (const [field, expected] of Object.entries({balances_bn: 978.09, dpd90_balances_pct: 1.49,
    dpd90_accounts_pct: 0.70, nco_annualized_pct: 5.01, new_sub660_accounts_pct: 18.52,
    new_sub660_commitments_pct: 4.19})) near(evidence.market.latest[field], expected, `US source ${field}`);
const {n, defaults} = evidence.summary.partitions.test;
assert.equal(new Set(evidence.policies.map(r => `${r.model}/${r.missed_default_cost}`)).size, 15);
assert.equal(new Set(evidence.capacities.map(r => `${r.model}/${r.capacity_fraction}`)).size, 9);
let policyChecks = 0, queueChecks = 0;
for (const model of modelKeys) for (const ratio of ratios) {
    const matches = evidence.policies.filter(r => r.model === model && +r.missed_default_cost === ratio);
    assert.equal(matches.length, 1, `policy ${model}/${ratio}`);
    const r = matches[0];
    const tp = numeric(r, 'true_positive'), fp = numeric(r, 'false_positive');
    const fn = numeric(r, 'false_negative'), tn = numeric(r, 'true_negative');
    assert.equal(tp + fp + fn + tn, n);
    assert.equal(tp + fn, defaults);
    assert.equal(tp + fp, +r.reviewed);
    assert.equal(+r.n, n);
    assert.equal(+r.defaults, defaults);
    assert.equal(+r.false_alarm_cost, 1);
    assert.equal(+r.cost_units, ratio * fn + fp);
    assert.equal(+r.review_none_cost_units, ratio * defaults);
    assert.equal(+r.review_all_cost_units, n - defaults);
    assert.equal(+r.minus_best_constant_cost_units, +r.cost_units - Math.min(ratio * defaults, n - defaults));
    near(r.review_rate, (tp + fp) / n, 'review rate');
    near(r.default_capture, tp / defaults, 'capture');
    near(r.queue_default_rate, tp / (tp + fp), 'queue default rate');
    assert.ok(+r.selected_threshold >= 0.01 && +r.selected_threshold <= 0.99);
    policyChecks++;
}
for (const model of modelKeys) for (const capacity of capacities) {
    const matches = evidence.capacities.filter(r => r.model === model && +r.capacity_fraction === capacity);
    assert.equal(matches.length, 1, `capacity ${model}/${capacity}`);
    const r = matches[0];
    assert.equal(+r.capacity_count, Math.floor(n * capacity));
    assert.equal(+r.flagged, +r.capacity_count);
    assert.equal(+r.defaults_flagged + +r.nondefaults_flagged, +r.flagged);
    assert.equal(+r.defaults_flagged + +r.defaults_unflagged, defaults);
    assert.equal(+r.cost_units, 5 * +r.defaults_unflagged + +r.nondefaults_flagged);
    near(r.capture_rate, +r.defaults_flagged / defaults, 'capacity capture');
    near(r.precision, +r.defaults_flagged / +r.flagged, 'capacity precision');
    near(r.flag_rate, +r.flagged / n, 'capacity review rate');
    assert.equal(r.tie_break, 'probability_desc_source_id_asc');
    queueChecks++;
}
const leafIds = [3, 4, 6, 7, 10, 11, 13, 14];
for (const [partition, expected] of Object.entries(evidence.summary.partitions)) {
    const rows = evidence.leaves.filter(r => r.partition === partition);
    assert.deepEqual(rows.map(r => +r.leaf_id), leafIds);
    assert.equal(rows.reduce((sum, r) => sum + +r.n, 0), expected.n);
    assert.equal(rows.reduce((sum, r) => sum + +r.defaults, 0), expected.defaults);
    for (const row of rows) {
        near(row.default_rate, +row.defaults / +row.n, 'leaf rate');
        assert.ok(row.rule.includes('PAY_'));
        assert.ok(+row.raw_probability >= 0 && +row.raw_probability <= 1);
        assert.ok(+row.calibrated_probability >= 0 && +row.calibrated_probability <= 1);
        const training = evidence.leaves.find(r => r.partition === 'train' && +r.leaf_id === +row.leaf_id);
        assert.equal(row.rule, training.rule, 'Rules cannot change with the evaluated partition');
        near(row.raw_probability, +training.defaults / +training.n, 'training-derived leaf prediction');
    }
}

// Execute the code delivered to the browser, rather than copying its functions.
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)]
    .filter(m => !/application\/json/.test(m[1]) && m[2].trim());
assert.equal(scripts.length, 1, 'Exactly one local executable script');
const elements = new Map(), events = new Map();
for (const match of html.matchAll(/\bid=["']([^"']+)["']/g)) {
    assert.ok(!elements.has(match[1]), `unique DOM id ${match[1]}`);
    const node = {id: match[1], value: '', textContent: '', innerHTML: '', disabled: false,
        addEventListener(name, callback) {events.set(`${this.id}/${name}`, callback);},
        setAttribute(name, value) {this[name] = value;},
        getAttribute(name) {return this[name];}};
    elements.set(match[1], node);
}
elements.get('evidence-data').textContent = dataMatch[1];
for (const [id, value] of [['model-select', 'challenger'], ['ratio-select', '5'], ['capacity-select', '0.1']]) {
    assert.ok(elements.has(id), id);
    elements.get(id).value = value;
}
const document = {
    getElementById(id) {assert.ok(elements.has(id), `existing DOM node ${id}`); return elements.get(id);},
    querySelectorAll(selector) {
        if (selector === 'select') return ['model-select', 'ratio-select', 'capacity-select'].map(id => elements.get(id));
        throw new Error(`Unexpected DOM selector: ${selector}`);
    }
};
const window = {};
vm.runInNewContext(scripts[0][2], {document, window, Intl, Math, Number, JSON, Error, console});
const explorer = window.ConsumerCreditExplorer;
assert.ok(explorer && typeof explorer.render === 'function', 'Published testable explorer API');
assert.deepEqual(JSON.parse(JSON.stringify(explorer.data)), evidence);
for (const id of ['summary-heading', 'scenario-status', 'capacity-metrics', 'policy-metrics', 'capacity-rows', 'policy-rows', 'model-rows', 'leaf-rows', 'market-metrics']) {
    const node = elements.get(id);
    assert.ok(node && (node.textContent || node.innerHTML), `initial output ${id}`);
}
function output(id) {const node = elements.get(id); return `${node.textContent} ${node.innerHTML}`;}
const format = value => new Intl.NumberFormat('en-US', {maximumFractionDigits: 0}).format(value);
const percent = value => `${(100 * value).toFixed(1)}%`;
function metricValues(id) {
    return [...output(id).matchAll(/<strong>([^<]+)<\/strong>/g)].map(match => match[1]);
}
function selectedLabel(id) {
    const matches = [...output(id).matchAll(/<tr class="selected"><th scope="row">([^<]+)<\/th>/g)];
    assert.equal(matches.length, 1, `exactly one selected model in ${id}`);
    return matches[0][1];
}
let interactionChecks = 0;
for (const model of modelKeys) for (const ratio of ratios) for (const capacity of capacities) {
    for (const [id, value] of [['model-select', model], ['ratio-select', String(ratio)], ['capacity-select', String(capacity)]]) {
        elements.get(id).value = value;
        const callback = events.get(`${id}/change`);
        assert.equal(typeof callback, 'function', `native ${id} change handler`);
        callback({target: elements.get(id)});
    }
    const expectedPolicy = evidence.policies.find(r => r.model === model && +r.missed_default_cost === ratio);
    const expectedQueue = evidence.capacities.find(r => r.model === model && +r.capacity_fraction === capacity);
    assert.deepEqual(JSON.parse(JSON.stringify(explorer.policyFor(model, ratio))), expectedPolicy);
    assert.deepEqual(JSON.parse(JSON.stringify(explorer.queueFor(model, capacity))), expectedQueue);
    assert.deepEqual(metricValues('capacity-metrics'), [format(expectedQueue.flagged), percent(expectedQueue.capture_rate),
        percent(expectedQueue.precision), format(expectedQueue.defaults_unflagged)]);
    assert.deepEqual(metricValues('policy-metrics'), [expectedPolicy.selected_threshold.toFixed(2), format(expectedPolicy.reviewed),
        percent(expectedPolicy.default_capture), format(expectedPolicy.cost_units)]);
    assert.equal(elements.get('summary-heading').textContent, `${labels[model]} · ${percent(capacity).replace('.0%', '%')} review capacity`);
    assert.deepEqual(elements.get('scenario-status').textContent.match(/[\d,]+/g).map(value => +value.replaceAll(',', '')),
        [expectedQueue.flagged, expectedQueue.defaults_flagged, expectedQueue.nondefaults_flagged, expectedQueue.defaults_unflagged, defaults]);
    for (const id of ['capacity-rows', 'policy-rows', 'model-rows']) assert.equal(selectedLabel(id), labels[model]);
    assert.ok(elements.get('policy-caption').textContent.startsWith(`${ratio} cost unit`));
    assert.ok(output('capacity-rows').includes(format(expectedQueue.flagged)) || output('capacity-rows').includes(String(expectedQueue.flagged)));
    assert.ok(output('policy-rows').includes(format(expectedPolicy.reviewed)) || output('policy-rows').includes(String(expectedPolicy.reviewed)));
    interactionChecks++;
}
const pairedLeaves = JSON.parse(JSON.stringify(explorer.leafRows()));
assert.equal(pairedLeaves.length, 8);
for (const {train, test} of pairedLeaves) {
    assert.deepEqual(train, evidence.leaves.find(r => r.partition === 'train' && r.leaf_id === train.leaf_id));
    assert.deepEqual(test, evidence.leaves.find(r => r.partition === 'test' && r.leaf_id === train.leaf_id));
}
assert.deepEqual(metricValues('market-metrics'), ['$978.09bn', '1.49%', '0.70%', '5.01%']);
for (const id of ['model-select', 'ratio-select', 'capacity-select']) {
    assert.equal(elements.get(id).disabled, false, `enable native ${id}`);
    const old = elements.get(id).value;
    elements.get(id).value = 'unknown';
    assert.throws(() => events.get(`${id}/change`)({target: elements.get(id)}), /Unknown published scenario/);
    elements.get(id).value = old;
    events.get(`${id}/change`)({target: elements.get(id)});
}
assert.ok(html.includes('Taiwan') && html.includes('2005') && html.includes('retrospective'));
assert.ok(!/<script\b[^>]*\bsrc=/.test(html), 'No external runtime scripts');
assert.ok(!/\bfetch\s*\(/.test(scripts[0][2]), 'Explorer uses embedded executed evidence');
console.log(JSON.stringify({passed: true, actual_embedded_script: true, policy_arithmetic_checks: policyChecks,
    capacity_arithmetic_checks: queueChecks, partition_leaf_rows: evidence.leaves.length,
    native_control_combinations: interactionChecks,
    scope: 'Executed aggregate evidence, exact browser script and native-change handlers; live browser layout and availability are checked separately.'}));
