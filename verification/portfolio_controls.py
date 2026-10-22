"""Independent mathematical controls for the seven pinned portfolio studies.

No training, model selection, source acquisition or final-outcome tuning occurs.
Synthetic cases are deterministic and separate from published empirical tests.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import time

import numpy as np


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def near(actual, expected, *, absolute=1e-9, relative=1e-10):
    if not math.isfinite(float(actual)) or not math.isclose(float(actual), float(expected), abs_tol=absolute, rel_tol=relative):
        raise AssertionError(f'{actual!r} differs from independent reference {expected!r}')


def verify_sources(root, manifest_path):
    """Verify every pinned public file before importing any study code."""
    manifest = json.loads(manifest_path.read_text())
    checked = 0
    for repo, record in manifest['repositories'].items():
        for name, expected in record['git_blobs'].items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe source manifest path')
            raw = (root/repo/path).read_bytes()
            actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if actual != expected:
                raise ValueError('Pinned public source differs: '+repo+'/'+name)
            checked += 1
    return {'files_verified':checked, 'source_commits':{
        repo:record['commit'] for repo, record in manifest['repositories'].items()}}


def credit_controls(root):
    sys.path.insert(0, str(root/'src'))
    from mortgage_risk.modelling import capacity_bounds
    problems = completions = 0
    for n in range(1, 6):
        for labels in itertools.product((0, 1, None), repeat=n):
            # Recall is well-defined in every completion when one event is known.
            if 1 not in labels:
                continue
            missing = [j for j, x in enumerate(labels) if x is None]
            observed = np.array([np.nan if x is None else x for x in labels])
            for selected in itertools.product((False, True), repeat=n):
                mask = np.array(selected)
                recalls, precision = [], []
                for assignment in itertools.product((0, 1), repeat=len(missing)):
                    completed = np.nan_to_num(observed).astype(int)
                    completed[missing] = assignment
                    captured = sum(int(completed[j]) for j in range(n) if selected[j])
                    recalls.append(captured/sum(completed))
                    if any(selected):
                        precision.append(captured/sum(selected))
                    completions += 1
                bounds = capacity_bounds(observed, mask)
                np.testing.assert_allclose(bounds['capture_bounds'], [min(recalls), max(recalls)], rtol=0, atol=1e-15)
                if precision:
                    np.testing.assert_allclose(bounds['precision_bounds'], [min(precision), max(precision)], rtol=0, atol=1e-15)
                else:
                    assert bounds['precision_bounds'] == [None, None]
                problems += 1
    return {'sharp_bound_problems': problems, 'binary_label_completions': completions,
            'scope': 'All n<=5 binary/missing label vectors with at least one known event and every fixed selection mask; exact enumeration.'}


def insurance_controls(root):
    sys.path.insert(0, str(root/'src'))
    from insurance_risk.reserving import mack
    from insurance_risk.challengers import lognormal_parameters, simulate_remaining_paid
    rng = np.random.default_rng(2026102102)
    checks = 0
    for trial in range(30):
        n = 6
        triangle = np.full((n, n), np.nan)
        for i in range(n):
            triangle[i, :n-i] = rng.uniform(100, 1000)*np.cumprod(rng.uniform(.95, 1.8, n-i))
        base = mack(triangle)
        scale = 10.0**rng.uniform(-3, 3)
        changed = mack(scale*triangle)
        np.testing.assert_allclose(changed['factors'], base['factors'], rtol=2e-13, atol=1e-13)
        near(changed['total_remaining_paid'], scale*base['total_remaining_paid'], relative=1e-12)
        near(changed['total_standard_error'], scale*base['total_standard_error'], relative=1e-12)
        np.testing.assert_allclose(changed['parameter_covariance'], scale**2*base['parameter_covariance'], rtol=1e-12, atol=1e-8)
        permuted = mack(triangle[rng.permutation(n)])
        near(permuted['total_remaining_paid'], base['total_remaining_paid'], relative=1e-12)
        near(permuted['total_standard_error'], base['total_standard_error'], relative=1e-12)
        assert np.linalg.eigvalsh(base['parameter_covariance']).min() >= -1e-7
        checks += 1
    # Reconstruct the transformed distribution's moments, not its implementation.
    for mean, variance in ((.8, 0), (1.2, .01), (20, 150), (1e-3, 2e-6)):
        mu, sd = lognormal_parameters(mean, variance)
        near(math.exp(float(mu)+float(sd)**2/2), mean, relative=1e-12)
        near(math.expm1(float(sd)**2)*math.exp(2*float(mu)+float(sd)**2), variance, relative=1e-12)
    # An exactly deterministic development law must have no simulation noise.
    triangle = np.full((6, 6), np.nan)
    for i in range(6):
        triangle[i, :6-i] = 100*2.0**np.arange(6-i)
    fit = mack(triangle)
    simulation = simulate_remaining_paid(fit, 1000, 20261021)
    np.testing.assert_allclose(simulation, fit['total_remaining_paid'], rtol=1e-12, atol=1e-8)
    return {'currency_scale_and_row_permutation_cases': checks, 'independent_lognormal_moment_pairs': 4,
            'deterministic_simulations': len(simulation), 'scope': 'Mack homogeneity, row exchangeability, covariance PSD and independently reconstructed distribution moments.'}


def causal_controls(root):
    ev = module('control_customer_evaluation', root/'src/customer_policy/evaluation.py')
    rng = np.random.default_rng(2026102103)
    n = 4
    outcomes = rng.uniform(0, 10, (n, 3))
    # Deliberately incorrect fixed nuisance predictions must still be unbiased
    # under all equiprobable randomized treatment assignments.
    means = rng.uniform(-5, 5, (n, 3))
    averages = np.zeros((n, 3))
    assignments = 0
    for labels in itertools.product(range(3), repeat=n):
        arms = np.array(labels)
        y = outcomes[np.arange(n), arms]
        averages += ev.augmented_scores(y, arms, means)
        assignments += 1
    np.testing.assert_allclose(averages/assignments, outcomes, rtol=0, atol=1e-13)
    problems = policies = 0
    for n in range(1, 6):
        for trial in range(8):
            means = rng.uniform(0, 15, (n, 3))
            margin, cost = float(rng.uniform(.1, 1)), float(rng.uniform(0, 3))
            for limit in range(n+1):
                capacity = 1.0 if limit == n else (limit+.25)/n
                action = ev.allocate(means, margin, cost, capacity, np.arange(n))
                realised = sum(margin*means[j, action[j]]-cost*(action[j]!=0) for j in range(n))
                best = -math.inf
                for candidate in itertools.product(range(3), repeat=n):
                    if sum(x!=0 for x in candidate)>limit:
                        continue
                    value = sum(margin*means[j, candidate[j]]-cost*(candidate[j]!=0) for j in range(n))
                    best = max(best, value)
                    policies += 1
                near(realised, best, absolute=1e-10, relative=1e-12)
                problems += 1
    return {'exact_randomization_assignments': assignments, 'globally_enumerated_contact_allocation_cases': problems,
            'feasible_contact_policies': policies, 'scope': 'Finite-population DR unbiasedness with wrong nuisance means; exact optimality under the stated equal-contact-cost/cap model, not arbitrary marketing constraints.'}


def enumerate_hedge(target, covariance, ridge):
    keys = np.array([1., 5., 10., 20., 30.])
    hessian = np.diag(keys)@covariance@np.diag(keys)+ridge*np.eye(5)
    linear = -np.diag(keys)@covariance@target
    best = math.inf
    feasible = 0
    for status in itertools.product((0, 1, 2), repeat=5):
        free = [j for j, x in enumerate(status) if x == 1]
        fixed = [j for j, x in enumerate(status) if x != 1]
        w = np.array([.6 if x == 2 else 0. for x in status])
        if not free:
            continue
        h = hessian[np.ix_(free, free)]
        system = np.block([[h, np.ones((len(free), 1))], [np.ones((1, len(free))), np.zeros((1, 1))]])
        rhs = np.r_[-linear[free]-hessian[np.ix_(free, fixed)]@w[fixed], 1-w.sum()]
        try:
            w[free] = np.linalg.solve(system, rhs)[:-1]
        except np.linalg.LinAlgError:
            continue
        if w.min() < -1e-9 or w.max() > .6+1e-9:
            continue
        error = keys*w-target
        objective = float(error@covariance@error+ridge*(w@w))
        best = min(best, objective)
        feasible += 1
    assert math.isfinite(best)
    return best, feasible


def treasury_controls(root):
    sys.path.insert(0, str(root/'src'))
    sys.path.insert(0, str(root/'extensions/treasury_alm'))
    import current_case as cc
    import hedging
    from retirement_alm.engine import key_weights
    rng = np.random.default_rng(2026102104)
    t = rng.uniform(0, 150, 1000)
    hats = key_weights(t)
    np.testing.assert_allclose(hats.sum(axis=1), 1, rtol=0, atol=2e-16)
    assert hats.min() >= 0 and hats.max() <= 1
    class Flat:
        def __init__(self, rate):self.rate=rate
        def zero(self, t):return self.rate
    risks = runoff_cases = 0
    for j in range(60):
        rate = float(rng.uniform(-.01, .10))
        curve = cc.ScenarioCurve(Flat(rate))
        times = np.arange(1., 61.)
        payments = rng.uniform(1, 10000, len(times))
        present = [float(p)*math.exp(-rate*float(t)) for p,t in zip(payments,times)]
        pv = math.fsum(present)
        expected_duration = math.fsum(float(t)*v for t,v in zip(times,present))/pv
        expected_convexity = math.fsum(float(t)**2*v for t,v in zip(times,present))/pv
        result = cc.risk(times, payments, curve)
        near(result['pv'], pv, absolute=1e-7, relative=2e-14)
        near(result['duration'], expected_duration, relative=2e-14)
        near(result['convexity'], expected_convexity, relative=2e-14)
        near(sum(result['key_duration']), result['duration'], relative=2e-14)
        faces = rng.uniform(1, 10000, 5)
        run = cc.runoff(times, payments, curve, faces, horizon=10, haircut=0, cash_rate_shift=0)
        final = run['final']
        recovered = sum(row['benefits_paid_usd']*math.exp(-rate*row['year']) for row in run['years'])+final['assets_usd']*math.exp(-rate*10)
        near(recovered, run['initial_assets_usd'], absolute=1e-7, relative=1e-12)
        risks += 1;runoff_cases += 1
    mortality = {'male':{j:.02 for j in range(120)}, 'female':{j:.02 for j in range(120)}}
    times, payments, _ = cc.expected_payments(mortality, cohorts=(cc.Cohort('male',60,100),), benefit=1000, force=.8)
    np.testing.assert_allclose(payments, 100000*.98**(.8*times), rtol=2e-14, atol=1e-7)
    # Actual current-study QPs, checked by complete active-face enumeration.
    saved = json.loads((root/'reports/current_case_20261019/current_case.json').read_text())
    target = np.asarray(saved['base_liability_risk']['key_duration'])
    selection = json.loads((root/'reports/treasury_20261019/development_selection.json').read_text())
    assert selection['covariance_train_end'] == '2014-12'
    covariance = np.asarray(selection['covariance'])
    qp = []
    for method, matrix, ridge in [('key_rate',np.eye(5),0.),('covariance',covariance,1e-8)]:
        minimum, faces_checked = enumerate_hedge(target, matrix, ridge)
        w = np.asarray(saved['portfolios'][method]['weights'])
        assert w.shape == (5,) and np.isfinite(w).all()
        assert w.min() >= -1e-8 and w.max() <= .6+1e-8
        near(w.sum(), 1., absolute=1e-8)
        error = hedging.KEYS*w-target
        actual = float(error@matrix@error+ridge*(w@w))
        near(actual, minimum, absolute=1e-12, relative=1e-8)
        qp.append({'method':method,'feasible_faces':faces_checked,'saved_objective':actual,'global_face_minimum':minimum})
    return {'key_partition_rows':len(t),'analytic_flat_curve_risk_cases':risks,'discounted_runoff_conservation_cases':runoff_cases,
            'constant_mortality_payment_terms':len(payments),'current_case_quadratic_programs':qp}


def demand_controls(root):
    sys.path.insert(0, str(root/'src'))
    from demand_inventory import core
    rng = np.random.default_rng(2026102105)
    feature_cases = allocation_cases = runoff_cases = 0
    for n in (1, 3, 10):
        for trial in range(20):
            sales = rng.poisson(2, (n, 150)).astype(float)
            prices = rng.uniform(2, 30, sales.shape)
            dates = np.arange(150)+int(np.datetime64('2010-01-01').astype('datetime64[D]').astype(int))
            meta = np.column_stack([np.arange(n),np.arange(n)%7,np.arange(n)%3])
            origin = 84
            baseline = core.features(sales, prices, dates, meta, origin)
            future_sales=sales.copy();future_prices=prices.copy()
            future_sales[:,origin:]=1e8;future_prices[:,origin:]=1e9
            np.testing.assert_array_equal(core.features(future_sales,future_prices,dates,meta,origin), baseline)
            feature_cases += 1
            desired=rng.uniform(0,50,n);cost=rng.uniform(.5,50,n);penalty=rng.uniform(0,20,n);coverage=rng.uniform(0,3,n)
            budget=float(rng.uniform(0,1000));capacity=float(rng.uniform(0,50))
            orders=core.allocate(desired,cost,penalty,coverage,np.arange(n),budget,capacity)
            assert orders.dtype.kind in 'iu' and orders.min()>=0
            assert orders.sum()<=math.floor(capacity) and float(orders@cost)<=budget+1e-6
            assert np.all(orders<=np.ceil(desired));allocation_cases += 1
            origins=list(range(56,112,7))
            q=core.coherent(rng.uniform(0,50,(len(origins)*n,4))).reshape(len(origins),n,4)
            lead=trial%3+1
            sim=core.simulate(sales,prices,origins,q,np.arange(n),budget_multiplier=.5,lead_weeks=lead)
            ordered=0;arrived=0
            for k,row in enumerate(sim['rows']):
                ordered+=row['ordered_units']
                if k>=lead:arrived+=sim['rows'][k-lead]['ordered_units']
                filled=sum(x['filled_units'] for x in sim['rows'][:k+1])
                near(arrived-filled,row['ending_inventory_units'],absolute=1e-8)
                near(row['demand_proxy_units'],row['filled_units']+row['lost_units'],absolute=1e-8)
                assert row['procurement_spend']<=row['budget']+1e-6
            near(ordered,sim['filled_units']+sim['ending_inventory_units']+sim['ending_pipeline_units'],absolute=1e-8)
            runoff_cases+=1
    return {'future_data_tamper_feature_cases':feature_cases,'integer_budget_capacity_cases':allocation_cases,
            'lead_time_stock_conservation_simulations':runoff_cases,'scope':'Feasibility and physical conservation for the documented heuristic; no claim of globally optimal heterogeneous-cost inventory allocation.'}


def macro_controls(root):
    core=module('control_inflation_core',root/'src/inflation_vintages/core.py')
    base={'reference_month':'2025-01','base':2012,'metric':'headline_yoy_percent','sector':'Combined','value':4.,'published_at':'2025-02-12T16:00:00+05:30'}
    later={**base,'value':5.,'published_at':'2025-03-12T16:00:00+05:30'}
    unrelated={**base,'base':2024,'value':100.}
    store=core.VintageStore([later,unrelated,base])
    assert store.asof('2025-01','2025-02-12T10:30:00+00:00')['value']==4.
    assert store.asof('2025-01','2025-03-12T16:00:00+05:30')['value']==5.
    try:store.asof('2025-01','2025-02-12T15:59:59+05:30')
    except ValueError:pass
    else:raise AssertionError('Pre-release observation escaped as-of guard')
    assert core.shift_month('2025-01',-1)=='2024-12'
    assert core.shift_month('2024-12',1)=='2025-01'
    return {'timezone_release_boundary_and_base_separation_checks':5,
            'public_numeric_reconstruction':'Separate script: scripts/reproduce_numeric_results.py; see numeric_reproduction.json for execution status.'}


def independent_profit_layers(ebit, a):
    # Each permanent profit increment is worth delta_profit/WACC and costs
    # delta_profit/ROIC to fund; terminal increments form a geometric series.
    with localcontext() as context:
        context.prec=60
        d=lambda x:Decimal(str(x))
        w=d(a.wacc);terminal=d(a.terminal_growth);rr=d(a.terminal_roic)
        profit=d(ebit)*(1-d(a.tax));result=profit/w
        for t in range(a.horizon):
            year=t+1
            growth=d(a.growth) if year<=a.high_growth_years else d(a.growth)+(terminal-d(a.growth))*d(year-a.high_growth_years)/d(a.horizon-a.high_growth_years)
            r=d(a.marginal_roic) if t<a.high_growth_years else d(a.marginal_roic)+(rr-d(a.marginal_roic))*d(t-a.high_growth_years+1)/d(a.horizon-a.high_growth_years+1)
            increment=profit*growth
            result+=increment*(1/w-1/r)/(1+w)**t
            profit+=increment
        result+=profit*terminal*(1/w-1/rr)*(1+w)/(w-terminal)/(1+w)**a.horizon
        return float(result)


def finance_controls(root):
    valuation=module('control_finance_valuation',root/'src/finance_lab/valuation.py')
    rng=np.random.default_rng(2026102107)
    maximum_relative=0.
    for trial in range(1000):
        horizon=int(rng.integers(2,51));high=int(rng.integers(1,horizon))
        terminal=float(rng.uniform(0,.08));wacc=float(rng.uniform(terminal+.00011,.5))
        a=valuation.Assumptions(float(rng.uniform(-.25,.5)),float(rng.uniform(.0001,1)),float(rng.uniform(.0001,1)),terminal,wacc,float(rng.uniform(0,.99)),horizon,high)
        ebit=float(10**rng.uniform(-2,6))
        actual=valuation.policy_value(ebit,a)['policy_value'];expected=independent_profit_layers(ebit,a)
        near(actual,expected,absolute=2e-6,relative=2e-10)
        maximum_relative=max(maximum_relative,abs(actual-expected)/max(1,abs(expected)))
    for growth in (-.25,0,.1,.5):
        a=valuation.Assumptions(growth,.1,.1,.02,.1,.25)
        near(valuation.policy_value(100,a)['policy_value'],750.,absolute=1e-9)
    a=valuation.Assumptions(.1,.2,.15,.02,.1,.25)
    target=independent_profit_layers(100,replace(a,growth=.137))
    reverse=valuation.reverse_growth(100,a,target)
    assert reverse['status']=='solved';near(reverse['growth'],.137,absolute=1e-11)
    return {'independent_60_digit_profit_layer_cases':1000,'equal_return_growth_neutrality_cases':4,
            'independent_target_reverse_case':1,'maximum_relative_or_absolute_scaled_difference':maximum_relative}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sources',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--manifest',type=Path);args=parser.parse_args()
    report={'schema':'portfolio-independent-controls-v1','seed_date':'2026-10-21','checks':{},'failures':[],
            'scope':'Deterministic mathematical controls on exact source files; no model fitting, test-set selection or claims of empirical outperformance.'}
    if args.manifest:
        report['source_identity'] = verify_sources(args.sources, args.manifest)
    controls=[('credit-risk-model-validation',credit_controls),('insurance-price-reserve-risk',insurance_controls),('causal-customer-decisions',causal_controls),('treasury-alm',treasury_controls),('demand-inventory',demand_controls),('inflation-vintages',macro_controls),('financial-decision-lab',finance_controls)]
    for repo,function in controls:
        started=time.monotonic()
        try:record={'status':'passed',**function(args.sources/repo)}
        except Exception as error:record={'status':'failed','error':repr(error)};report['failures'].append({'repo':repo,**record})
        record['seconds']=round(time.monotonic()-started,3);report['checks'][repo]=record
        print(json.dumps({'repo':repo,**record}),flush=True)
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    if report['failures']:raise SystemExit(1)


if __name__=='__main__':main()
