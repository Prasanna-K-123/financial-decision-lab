"""Build a static explorer from reviewed, executed consumer-card evidence.

The sibling checkout is needed only to regenerate this publication. The hub's
verification checks the embedded publication without downloading another repo.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("scorecard", "challenger", "cart")
LABELS = {"scorecard": "WoE logistic", "challenger": "Boosting", "cart": "Shallow CART"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key, value in row.items():
            if key in {"model", "partition", "rule", "tie_break"}:
                continue
            row[key] = None if value == "" else float(value) if any(c in value.lower() for c in ".e") else int(value)
    return rows


def evidence(source: Path) -> dict:
    folder = source / "reference/card_strategy"
    review_path = folder / "independent_review.json"
    review = json.loads(review_path.read_text())
    if review.get("status") != "PASS" or not review.get("source_labels_and_rules_checked"):
        raise ValueError("A passing source-reconciled independent strategy review is required.")
    for name, identity in review["input_sha256"].items():
        if Path(name).name != name or sha(folder / name) != identity:
            raise ValueError(f"Reviewed strategy evidence changed: {name}")
    summary = json.loads((folder / "summary.json").read_text())
    if not summary.get("baseline_test_probabilities_reconciled"):
        raise ValueError("Historical model probabilities must be reconciled.")
    policies = table(folder / "policy_sensitivity.csv")
    capacities = table(folder / "capacity.csv")
    leaves = table(folder / "leaf_segments.csv")
    expected_policies = {(m, c) for m in MODELS for c in (1, 2, 5, 10, 20)}
    if len(policies) != 15 or {(r["model"], r["missed_default_cost"]) for r in policies} != expected_policies:
        raise ValueError("Expected all three models and five cost assumptions.")
    for row in policies:
        if row["n"] != 6001 or row["defaults"] != 1295 or row["false_alarm_cost"] != 1:
            raise ValueError("Unexpected evaluation population or cost units.")
        if row["cost_units"] != row["missed_default_cost"] * row["false_negative"] + row["false_positive"]:
            raise ValueError("Scenario cost does not reconcile.")
        if row["reviewed"] != row["true_positive"] + row["false_positive"]:
            raise ValueError("Scenario review workload does not reconcile.")
    expected_capacity = {(m, c) for m in MODELS for c in (.05, .1, .2)}
    if len(capacities) != 9 or {(r["model"], r["capacity_fraction"]) for r in capacities} != expected_capacity:
        raise ValueError("Expected three capacities for every model.")
    original_path = source / "reference/card_clients/replay/decision_queue.csv"
    original = {(r["model"], r["capacity_fraction"]): r for r in table(original_path)}
    for row in capacities:
        if row["flagged"] != int(6001 * row["capacity_fraction"]) or row["capacity_count"] != row["flagged"]:
            raise ValueError("Capacity must use the exact floor rule.")
        if row["defaults_flagged"] + row["defaults_unflagged"] != 1295:
            raise ValueError("Capacity defaults do not reconcile.")
        if row["model"] != "cart":
            old = original[(row["model"], row["capacity_fraction"])]
            if any(row[k] != old[k] for k in ("flagged", "defaults_flagged", "nondefaults_flagged", "defaults_unflagged", "tied_at_cutoff")):
                raise ValueError("Original capacity evidence changed.")
    if len(leaves) != 32 or len({r["leaf_id"] for r in leaves}) != 8:
        raise ValueError("Expected eight CART leaves across four roles.")
    for role, count in summary["partitions"].items():
        rows = [r for r in leaves if r["partition"] == role]
        if len(rows) != 8 or sum(r["n"] for r in rows) != count["n"] or sum(r["defaults"] for r in rows) != count["defaults"]:
            raise ValueError("CART role support does not reconcile.")
    market_path = source / "reference/us_market/report.json"
    market = json.loads(market_path.read_text())
    if market["quality"]["errors"] or market["coverage"]["quarters"] != 56:
        raise ValueError("Expected the reviewed 56-quarter US market pack.")
    return {"summary": summary, "policies": policies, "capacities": capacities, "leaves": leaves,
            "market": {k: market[k] for k in ("source_release", "source_published_on", "coverage", "quality", "latest", "series_status")},
            "provenance": {"strategy_review_status": review["status"],
                           "strategy_review_sha256": sha(review_path),
                           "strategy_input_sha256": review["input_sha256"],
                           "original_queues_sha256": sha(original_path), "original_queues_reconciled": True,
                           "market_report_sha256": sha(market_path)}}


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Consumer credit risk and review strategy | Prasanna K</title>
<meta name="description" content="Explore historical card-review capacity, cost assumptions and interpretable CART segments, backed by executed Python and independent SQL evidence.">
<style>
:root{color-scheme:light;--ink:#172d3e;--muted:#526878;--teal:#006c65;--line:#cbd6dd;--paper:#fff;--wash:#eaf1f3}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f6f7f5;color:var(--ink);font:16px/1.6 system-ui,sans-serif}header,main,footer{max-width:1180px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:center;gap:20px;border-bottom:1px solid var(--line)}header nav{display:flex;gap:22px;flex-wrap:wrap}a{color:var(--teal);text-underline-offset:4px}header a{font-size:.9rem}h1{font:500 clamp(2.4rem,5vw,4rem)/1.08 Georgia,serif;letter-spacing:-.035em;max-width:950px;margin:20px 0}h2{font:500 clamp(1.6rem,3vw,2rem)/1.25 Georgia,serif;margin:0 0 13px}h3{font-size:1rem;margin:0 0 8px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.75rem;color:var(--teal);font-weight:750}.lead{font-size:1.12rem;max-width:850px;color:#405969}.scope{max-width:900px;border-left:3px solid var(--teal);padding:10px 17px;background:var(--wash);font-size:.94rem}.actions,.section-nav{display:flex;flex-wrap:wrap;gap:12px 22px;margin:23px 0}.actions a{display:inline-flex;align-items:center;min-height:46px;border:1px solid var(--ink);border-radius:4px;padding:9px 15px;text-decoration:none}.actions a:first-child{color:white;background:#203d57}.section-nav{font-size:.9rem;border-block:1px solid var(--line);padding:14px 0;margin:30px 0}.section-nav a{min-height:30px;display:inline-flex;align-items:center}.panel{background:var(--paper);border:1px solid #d5dfe5;border-radius:7px;padding:28px;margin:0 0 26px}.section-top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.number{color:var(--teal);font-size:.75rem;letter-spacing:.08em;font-weight:750;margin:0 0 7px}.section-copy{max-width:850px;color:var(--muted);margin:0 0 22px}.controls{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;background:var(--wash);padding:20px;border-radius:5px;margin-bottom:25px}.controls label{display:block;font-size:.85rem;font-weight:700;margin-bottom:6px}select{width:100%;min-height:48px;border:1px solid #627b89;border-radius:4px;padding:9px 11px;background:white;color:var(--ink);font:inherit}.control-note{font-size:.78rem;color:var(--muted);margin:7px 0 0}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin:18px 0 20px}.metric{padding:17px;background:#f0f5f5;border-top:2px solid #8baea9}.metric strong{display:block;font-size:clamp(1.4rem,3vw,2rem);line-height:1.3;font-variant-numeric:tabular-nums}.metric span{display:block;color:var(--muted);font-size:.82rem;margin-top:4px}.decision-note{font-size:.98rem;max-width:920px}.help{font-size:.85rem;color:var(--muted)}.table-wrap{overflow-x:auto;border:1px solid #d7e0e4;border-radius:4px;margin:16px 0 9px}table{border-collapse:collapse;width:100%;font-size:.87rem;font-variant-numeric:tabular-nums}caption{text-align:left;font-size:.84rem;padding:10px 13px;background:#f7f9f9;color:var(--muted)}th,td{padding:12px 13px;text-align:right;vertical-align:top;border-bottom:1px solid #e1e7eb;white-space:nowrap}th:first-child,td:first-child{text-align:left}thead th{font-size:.76rem;background:#edf2f4;color:#405969}tbody th{font-weight:600;text-align:left}tbody tr:last-child>*{border-bottom:0}.selected>*{background:#eaf4f1}.selected th{box-shadow:inset 3px 0 var(--teal)}.constant>*{color:var(--muted);background:#fafafa}.meter{height:7px;width:100%;background:#e2e9eb;border-radius:2px;overflow:hidden;margin-top:7px}.meter span{display:block;background:#007a70;height:100%}.rule{max-width:340px;min-width:260px;white-space:normal;text-align:left;font-family:ui-monospace,monospace;font-size:.76rem;line-height:1.6}.subtle{display:block;font-size:.75rem;color:var(--muted)}.market{border-top:4px solid #8c6643}.market .metric{border-color:#bca78d;background:#f8f4ef}.source-list{padding-left:19px;font-size:.92rem}.source-list li{margin-bottom:7px}details{border-top:1px solid var(--line);padding-top:14px;margin-top:20px}summary{cursor:pointer;font-weight:650;min-height:40px}.identities{overflow-wrap:anywhere;font: .76rem/1.7 ui-monospace,monospace;color:var(--muted)}footer{font-size:.8rem;color:var(--muted)}a:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #ba742b;outline-offset:4px}[hidden]{display:none!important}.skip{position:absolute;left:-9999px}.skip:focus{left:20px;top:10px;background:white;padding:12px;z-index:9}
@media(max-width:780px){header,main,footer{padding:18px}.panel{padding:20px}.controls{grid-template-columns:1fr;padding:16px;gap:16px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.section-top{display:block}header{align-items:flex-start}header nav{justify-content:flex-end;gap:10px 16px}h1{margin-top:18px}.rule{min-width:220px}.section-nav{gap:7px 17px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.controls,.section-nav{display:none}.panel{break-inside:avoid}body{background:white}header,main,footer{max-width:none}.table-wrap{overflow:visible}a{color:var(--ink)}}
</style></head><body>
<a class="skip" href="#main">Skip to evidence</a>
<header><strong>Prasanna K</strong><nav aria-label="Research navigation"><a href="portfolio.html#consumer-credit">Research portfolio</a><a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy">Source code</a></nav></header>
<main id="main"><div class="eyebrow">Consumer credit · Python and SQL · Historical research</div>
<h1>What does a credit-review policy ask the team to do?</h1>
<p class="lead">Compare review workload, observed default concentration and readable customer segments. Three model approaches answer the same decision questions, with independently checked evidence.</p>
<p class="scope"><strong>Taiwan, 2005:</strong> 30,000 existing card clients; 6,001 in the historical evaluation. These are retrospective, known-cohort analyses. Review effects, monetary savings and US borrower performance are not established.</p>
<div class="actions"><a href="#review-strategy">Explore review strategy</a><a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reports/DECISION_MEMO.md">Read the decision memo</a></div>
<nav class="section-nav" aria-label="Evidence sections"><a href="#review-strategy">Review capacity</a><a href="#cost-policy">Cost assumptions</a><a href="#segments">CART segments</a><a href="#model-evidence">Model evidence</a><a href="#us-context">Separate US context</a><a href="#sources">Sources and reproduction</a></nav>

<section class="panel" id="review-strategy" aria-labelledby="review-heading"><div class="number">01 / FIXED REVIEW CAPACITY</div><h2 id="review-heading">A finite queue makes the tradeoff visible.</h2>
<p class="section-copy">Choose the same capacity for all three models. A queue ranks clients by calibrated default probability, then source ID for exact score ties. It describes observed concentration, without assuming that a review prevents default.</p>
<div class="controls"><div><label for="model-select">Model to inspect</label><select id="model-select" disabled><option value="challenger">Boosting</option><option value="scorecard">WoE logistic</option><option value="cart">Shallow CART</option></select><p class="control-note">All three remain visible in the comparisons.</p></div><div><label for="capacity-select">Available review capacity</label><select id="capacity-select" disabled><option value="0.05">5% of clients</option><option value="0.1" selected>10% of clients</option><option value="0.2">20% of clients</option></select><p class="control-note">Exact queue size = floor(capacity × 6,001).</p></div><div><label for="ratio-select">Assumed missed-default cost</label><select id="ratio-select" disabled><option value="1">1 unit per missed default</option><option value="2">2 units per missed default</option><option value="5" selected>5 units per missed default</option><option value="10">10 units per missed default</option><option value="20">20 units per missed default</option></select><p class="control-note">One unit per nondefault client flagged. Used in section 02, independently of queue capacity.</p></div></div>
<h3 id="summary-heading">Boosting · 10% review capacity</h3><div id="capacity-metrics" class="metrics">__CAPACITY_METRICS__</div>
<p id="scenario-status" class="decision-note" role="status" aria-live="polite" aria-atomic="true">__SCENARIO_STATUS__</p>
<div class="table-wrap"><table><caption>Same capacity, same 6,001 historical evaluation clients</caption><thead><tr><th scope="col">Model</th><th scope="col">Clients flagged</th><th scope="col">Defaults captured</th><th scope="col">Queue default rate</th><th scope="col">Defaults outside queue</th><th scope="col">Tied at cutoff</th></tr></thead><tbody id="capacity-rows">__CAPACITY_ROWS__</tbody></table></div>
<p class="help">The default 10% queue contains 600 clients, rather than 600.1. A large tied group can cross the boundary for the shallow tree; source-ID ordering fixes membership without using outcomes. The full tie group is reported above.</p></section>

<section class="panel" id="cost-policy" aria-labelledby="policy-heading"><div class="number">02 / ASSUMED ERROR COSTS</div><h2 id="policy-heading">A lower missed-default tolerance can require many more reviews.</h2>
<p class="section-copy">Each model's threshold was chosen on the separate policy-validation partition for each of five cost assumptions. Inspect its resulting historical evaluation workload here. These thresholds are not constrained by the capacity selector in section 01.</p>
<div id="policy-metrics" class="metrics">__POLICY_METRICS__</div><p id="policy-status" class="decision-note">__POLICY_STATUS__</p>
<div class="table-wrap"><table><caption id="policy-caption">Five units per missed default; one per nondefault client flagged</caption><thead><tr><th scope="col">Policy</th><th scope="col">Threshold</th><th scope="col">Clients flagged</th><th scope="col">Defaults captured</th><th scope="col">Missed defaults</th><th scope="col">Nondefaults flagged</th><th scope="col">Assumed cost units</th></tr></thead><tbody id="policy-rows">__POLICY_ROWS__</tbody></table></div>
<p class="help">Cost = missed-default weight × missed defaults + nondefault clients flagged. Review-none and review-all supply transparent constant benchmarks. Costs from different ratios use different assumptions; they are not estimates of changing bank losses. Lowest threshold wins an exact policy-validation cost tie on the fixed 0.01–0.99 grid.</p></section>

<section class="panel" id="segments" aria-labelledby="segments-heading"><div class="number">03 / READABLE CART SEGMENTS</div><h2 id="segments-heading">Eight training-derived rules, with their observed support.</h2><p class="section-copy">The depth-three tree fits the training partition only, with a minimum training leaf size of 200. Training and evaluation default rates help expose concentration and variation; they do not certify segment stability or causal effects.</p>
<div class="table-wrap"><table><caption>All eight leaves; calibration and policy-validation support remain available in the source CSV</caption><thead><tr><th scope="col">Leaf</th><th scope="col">Training clients</th><th scope="col">Training default rate</th><th scope="col">Evaluation clients</th><th scope="col">Evaluation default rate</th><th scope="col">Exact training-derived rule</th></tr></thead><tbody id="leaf-rows">__LEAF_ROWS__</tbody></table></div>
<p class="help">PAY_0, PAY_2 and PAY_5 are original repayment-status codes, treated numerically. BILL_AMT and PAY_AMT fields retain the source's New Taiwan dollar units. Read the <a href="https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients">UCI codebook</a> before interpreting a split. Age remains an allowed predictor. This Python CART implementation is separate from SAS or CHAID execution.</p></section>

<section class="panel" id="model-evidence" aria-labelledby="model-heading"><div class="number">04 / MODEL EVIDENCE</div><h2 id="model-heading">Ranking, probability quality and workload answer different questions.</h2><p class="section-copy">The boosting model has higher historical ROC AUC; the scorecard has slightly higher average precision. Calibration worsens the recorded Brier scores. The readable CART benchmark has lower ranking performance than both.</p>
<div class="table-wrap"><table><caption>Same evaluation clients; lower Brier scores indicate better probability accuracy</caption><thead><tr><th scope="col">Model</th><th scope="col">ROC AUC</th><th scope="col">Average precision</th><th scope="col">Raw Brier</th><th scope="col">Calibrated Brier</th></tr></thead><tbody id="model-rows">__MODEL_ROWS__</tbody></table></div><p class="help">New CART and sensitivity results are descriptive point estimates on known outcomes. The <a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reports/RESEARCH_REPORT.md">original paired uncertainty analysis</a> concerns the original scorecard/boosting comparison and does not supply confidence intervals for the new CART scenarios. No winning model or operating ratio is selected from this explorer.</p></section>

<section class="panel market" id="us-context" aria-labelledby="market-heading"><div class="number">05 / SEPARATE US MARKET CONTEXT</div><h2 id="market-heading">US aggregates describe a different population.</h2><p class="section-copy">Official Philadelphia Fed large-bank reporting covers 56 quarters, 2012Q3–2026Q2. It informs the US consumer-card discussion and is never merged with Taiwanese customers or used to validate their fitted probabilities.</p><div id="market-metrics" class="metrics">__MARKET_METRICS__</div><p class="decision-note">In 2026Q2, original-score-below-660 borrowers represent <strong>18.52% of new accounts</strong> and <strong>4.19% of new commitments</strong>. Account mix and assigned credit therefore deserve separate investigation.</p><p class="help">Balances are quarter-end stocks; net charge-offs are annualized rates. Published history can be revised. Source release published 7 October 2026. <a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/docs/MARKET_METHODOLOGY.md">Definitions, source rights and the complete market pack</a>.</p></section>

<section class="panel" id="sources" aria-labelledby="sources-heading"><div class="number">06 / REVIEWABLE EVIDENCE</div><h2 id="sources-heading">Follow every finding back to executed research.</h2><p>Strategy source reconciliation and independent software accounting: <strong>PASS</strong>. All 15 cost scenarios, 9 capacity scenarios and 32 leaf/partition rows are included. This is a separate implementation inside the project, without external institutional approval.</p>
<ul class="source-list"><li><a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reports/STRATEGY_REPORT.md">CART and policy-sensitivity report</a> · <a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reference/card_strategy/policy_sensitivity.csv">Scenario CSV</a> · <a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reference/card_strategy/leaf_segments.csv">Leaf CSV</a></li><li><a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reference/card_strategy/independent_review.json">Independent review</a> · <a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/reference/card_strategy/protocol.json">Recorded extension protocol</a></li><li><a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/docs/REPRODUCE.md">Reproduction guide</a> · <a href="https://github.com/Prasanna-K-123/consumer-credit-risk-strategy/blob/main/docs/INTERVIEW_GUIDE.md">Explain and challenge the work</a></li></ul>
<details><summary>Published input identities</summary><div id="identities" class="identities">__IDENTITIES__</div></details>
<noscript><p>This page displays the default executed scenario without JavaScript. The source tables linked above contain every model, cost ratio and capacity.</p></noscript></section>
</main><footer>Prasanna K · Research presentation updated 30 October 2026. Static evidence explorer: no uploaded client data, live model service or newly generated predictions. <a href="portfolio.html#consumer-credit">Return to the portfolio</a>.</footer>
<script id="evidence-data" type="application/json">__DATA__</script>
<script>
'use strict';
(() => {
  const data = JSON.parse(document.getElementById('evidence-data').textContent);
  const labels = {scorecard:'WoE logistic',challenger:'Boosting',cart:'Shallow CART'};
  const models = ['scorecard','challenger','cart'];
  const get = id => document.getElementById(id);
  const integer = number => Number(number).toLocaleString('en-US');
  const pct = number => (100 * number).toFixed(1) + '%';
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const policyFor = (model, ratio) => data.policies.find(r => r.model === model && r.missed_default_cost === Number(ratio));
  const queueFor = (model, capacity) => data.capacities.find(r => r.model === model && r.capacity_fraction === Number(capacity));
  const leafRows = () => data.leaves.filter(r => r.partition === 'train').map(train => ({train, test:data.leaves.find(r => r.leaf_id === train.leaf_id && r.partition === 'test')}));
  const metric = (value, label) => '<div class="metric"><strong>' + esc(value) + '</strong><span>' + esc(label) + '</span></div>';
  const cells = values => values.map(value => '<td>' + value + '</td>').join('');
  function render() {
    const model = get('model-select').value, ratio = Number(get('ratio-select').value), capacity = Number(get('capacity-select').value);
    const q = queueFor(model, capacity), p = policyFor(model, ratio);
    if (!q || !p) throw new Error('Unknown published scenario');
    get('summary-heading').textContent = labels[model] + ' · ' + pct(capacity).replace('.0%', '%') + ' review capacity';
    get('capacity-metrics').innerHTML = metric(integer(q.flagged),'clients in the queue') + metric(pct(q.capture_rate),'observed defaults captured') + metric(pct(q.precision),'queue default rate') + metric(integer(q.defaults_unflagged),'defaults outside the queue');
    get('scenario-status').textContent = labels[model] + ' flags ' + integer(q.flagged) + ' clients: ' + integer(q.defaults_flagged) + ' observed defaults and ' + integer(q.nondefaults_flagged) + ' nondefaults. ' + integer(q.defaults_unflagged) + ' of the 1,295 observed defaults remain outside this queue.';
    get('capacity-rows').innerHTML = models.map(name => {const r=queueFor(name,capacity);return '<tr' + (name===model?' class="selected"':'') + '><th scope="row">'+labels[name]+'</th>'+cells([integer(r.flagged),pct(r.capture_rate)+'<span class="subtle">'+integer(r.defaults_flagged)+' defaults</span><div class="meter" aria-hidden="true"><span style="width:'+Math.max(0,Math.min(100,r.capture_rate*100))+'%"></span></div>',pct(r.precision),integer(r.defaults_unflagged),integer(r.tied_at_cutoff)])+'</tr>';}).join('');
    get('policy-metrics').innerHTML = metric(p.selected_threshold.toFixed(2),'policy-validation-selected threshold')+metric(integer(p.reviewed),'historical clients flagged')+metric(pct(p.default_capture),'observed defaults captured')+metric(integer(p.cost_units),'assumed cost units');
    get('policy-status').textContent = labels[model] + ' uses a ' + p.selected_threshold.toFixed(2) + ' threshold under the ' + ratio + ':1 cost assumption and flags ' + pct(p.review_rate) + ' of evaluation clients.' + (p.reviewed === p.n ? ' This scenario flags every client; its workload equals review-all.' : ' The fixed-capacity queue above answers a separate workload question.');
    get('policy-caption').textContent = ratio + ' cost unit' + (ratio===1?'':'s') + ' per missed default; one per nondefault client flagged';
    get('policy-rows').innerHTML = models.map(name => {const r=policyFor(name,ratio);return '<tr'+(name===model?' class="selected"':'')+'><th scope="row">'+labels[name]+'</th>'+cells([r.selected_threshold.toFixed(2),integer(r.reviewed)+'<span class="subtle">'+pct(r.review_rate)+'</span>',pct(r.default_capture),integer(r.false_negative),integer(r.false_positive),integer(r.cost_units)])+'</tr>';}).join('')+'<tr class="constant"><th scope="row">Review none</th>'+cells(['—','0','0.0%','1,295','0',integer(1295*ratio)])+'</tr><tr class="constant"><th scope="row">Review all</th>'+cells(['—','6,001','100.0%','0','4,706','4,706'])+'</tr>';
    get('leaf-rows').innerHTML = leafRows().map(({train,test})=>'<tr><th scope="row">'+integer(train.leaf_id)+'</th>'+cells([integer(train.n),pct(train.default_rate),integer(test.n),pct(test.default_rate),'<span class="rule">'+esc(train.rule).replaceAll(' AND ','<br>AND ')+'</span>'])+'</tr>').join('');
    get('model-rows').innerHTML=models.map(name=>{const m=data.summary.models[name];return '<tr'+(name===model?' class="selected"':'')+'><th scope="row">'+labels[name]+'</th>'+cells([m.calibrated.auc.toFixed(4),m.calibrated.average_precision.toFixed(4),m.raw.brier.toFixed(6),m.calibrated.brier.toFixed(6)])+'</tr>';}).join('');
    const market=data.market.latest;
    get('market-metrics').innerHTML=metric('$'+market.balances_bn.toFixed(2)+'bn','2026Q2 balances')+metric(market.dpd90_balances_pct.toFixed(2)+'%','90+ DPD by balances')+metric(market.dpd90_accounts_pct.toFixed(2)+'%','90+ DPD by accounts')+metric(market.nco_annualized_pct.toFixed(2)+'%','annualized net charge-off rate');
  }
  ['model-select','ratio-select','capacity-select'].forEach(id=>{get(id).addEventListener('change',render);get(id).disabled=false;});
  window.ConsumerCreditExplorer = {data,policyFor,queueFor,leafRows,render};
  render();
})();
</script></body></html>
'''


def build(source: Path, target: Path) -> str:
    data = evidence(source)
    # Generate static defaults using the same published counts. Native controls
    # replace these fragments after startup; the first screen also works offline
    # with scripting disabled.
    q = next(r for r in data["capacities"] if r["model"] == "challenger" and r["capacity_fraction"] == .1)
    p = next(r for r in data["policies"] if r["model"] == "challenger" and r["missed_default_cost"] == 5)
    pct = lambda value: f"{value * 100:.1f}%"
    metric = lambda value, label: f'<div class="metric"><strong>{html.escape(str(value))}</strong><span>{html.escape(label)}</span></div>'
    default_capacity = ''.join(metric(value, label) for value, label in ((f'{q["flagged"]:,}', 'clients in the queue'), (pct(q['capture_rate']), 'observed defaults captured'), (pct(q['precision']), 'queue default rate'), (f'{q["defaults_unflagged"]:,}', 'defaults outside the queue')))
    default_policy = ''.join(metric(value, label) for value, label in ((f'{p["selected_threshold"]:.2f}', 'policy-validation-selected threshold'), (f'{p["reviewed"]:,}', 'historical clients flagged'), (pct(p['default_capture']), 'observed defaults captured'), (f'{p["cost_units"]:,}', 'assumed cost units')))
    cells = lambda values: ''.join(f'<td>{html.escape(str(value))}</td>' for value in values)
    capacity_rows = ''.join('<tr><th scope="row">'+LABELS[r['model']]+'</th>'+cells([f'{r["flagged"]:,}',pct(r['capture_rate']),pct(r['precision']),f'{r["defaults_unflagged"]:,}',f'{r["tied_at_cutoff"]:,}'])+'</tr>' for r in data['capacities'] if r['capacity_fraction']==.1)
    policy_rows = ''.join('<tr><th scope="row">'+LABELS[r['model']]+'</th>'+cells([f'{r["selected_threshold"]:.2f}',f'{r["reviewed"]:,}',pct(r['default_capture']),f'{r["false_negative"]:,}',f'{r["false_positive"]:,}',f'{r["cost_units"]:,}'])+'</tr>' for r in data['policies'] if r['missed_default_cost']==5)
    policy_rows += '<tr><th scope="row">Review none</th>'+cells(['—','0','0.0%','1,295','0','6,475'])+'</tr><tr><th scope="row">Review all</th>'+cells(['—','6,001','100.0%','0','4,706','4,706'])+'</tr>'
    leaf_rows=''
    for train in (r for r in data['leaves'] if r['partition']=='train'):
        test=next(r for r in data['leaves'] if r['partition']=='test' and r['leaf_id']==train['leaf_id'])
        leaf_rows+='<tr><th scope="row">'+str(train['leaf_id'])+'</th>'+cells([f'{train["n"]:,}',pct(train['default_rate']),f'{test["n"]:,}',pct(test['default_rate'])])+f'<td class="rule">{html.escape(train["rule"])}</td></tr>'
    model_rows=''.join('<tr><th scope="row">'+LABELS[name]+'</th>'+cells([f'{values["calibrated"]["auc"]:.4f}',f'{values["calibrated"]["average_precision"]:.4f}',f'{values["raw"]["brier"]:.6f}',f'{values["calibrated"]["brier"]:.6f}'])+'</tr>' for name,values in data['summary']['models'].items())
    market=data['market']['latest']
    market_metrics=''.join(metric(value,label) for value,label in ((f'${market["balances_bn"]:.2f}bn','2026Q2 balances'),(f'{market["dpd90_balances_pct"]:.2f}%','90+ DPD by balances'),(f'{market["dpd90_accounts_pct"]:.2f}%','90+ DPD by accounts'),(f'{market["nco_annualized_pct"]:.2f}%','annualized net charge-off rate')))
    replacements = {"__DATA__":json.dumps(data,separators=(',',':'),sort_keys=True,allow_nan=False).replace('</','<\\/'),
                    "__CAPACITY_METRICS__":default_capacity,"__POLICY_METRICS__":default_policy,
                    "__CAPACITY_ROWS__":capacity_rows,"__POLICY_ROWS__":policy_rows,"__LEAF_ROWS__":leaf_rows,"__MODEL_ROWS__":model_rows,"__MARKET_METRICS__":market_metrics,
                    "__SCENARIO_STATUS__":"Boosting flags 600 clients: 432 observed defaults and 168 nondefaults. 863 of the 1,295 observed defaults remain outside this queue.",
                    "__POLICY_STATUS__":"Boosting uses a 0.21 threshold under the 5:1 cost assumption and flags 34.2% of evaluation clients. The fixed-capacity queue above answers a separate workload question.",
                    "__IDENTITIES__":html.escape(json.dumps(data['provenance'],indent=2)).replace('\n','<br>')}
    document = TEMPLATE
    for key, value in replacements.items():
        if document.count(key)!=1:
            raise ValueError(f'Unexpected template marker {key}')
        document=document.replace(key,value)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(document,encoding='utf-8')
    return sha(target)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT.parent/'consumer-credit-risk-strategy')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/consumer-credit.html')
    args=parser.parse_args()
    print(json.dumps({'output':str(args.output),'sha256':build(args.source,args.output)}))
