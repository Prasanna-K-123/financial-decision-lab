"""Analyst decision pipeline from reviewed reference facts, never unreviewed extraction."""
from pathlib import Path
from dataclasses import replace
import argparse,json,math
from finance_lab.valuation import Assumptions,CASES,policy_value,reverse_growth
p=argparse.ArgumentParser();p.add_argument('references');p.add_argument('auxiliary');p.add_argument('output');a=p.parse_args()
root=Path(__file__).resolve().parents[1];sources=json.loads((root/'data/sources.json').read_text());refs=json.loads(Path(a.references).read_text());aux=json.loads(Path(a.auxiliary).read_text());out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
spreads=[];scenarios=[];sensitivity=[];regimes=[];reverse=[]
for m in sources:
 vals={r['field']:float(r['value']) if r.get('value') is not None else None for r in refs if r['source_id']==m['id'] and r['status']!='control'}
 extra=aux[m['id']];total_liabilities=vals['liabilities'] if vals['liabilities'] is not None else vals['current_liabilities']+extra['noncurrent_liabilities']
 residual=vals['assets']-total_liabilities-vals['equity'];assert abs(residual)<.01
 end_cash=extra['cash_begin']+extra['cash_change']+extra.get('fx_effect',0);assert abs(end_cash-vals['cash'])<.01
 cash_flow_sum=vals['cfo']+extra['cash_investing']+extra['cash_financing']+extra['fx_cash_flow']
 cash_flow_residual=cash_flow_sum-(vals['cash']-extra['cash_begin']);assert abs(cash_flow_residual)<.01
 capex=vals['cash_ppe'];proxy=vals['cfo']-capex if capex is not None else None
 spread={**m,'facts':vals,'cash_generation_cfo_minus_cash_ppe':proxy,'combined_ppe_intangibles_cash_outflow':extra.get('combined_ppe_intangibles'),'cash_generation_after_combined_investment':vals['cfo']-extra['combined_ppe_intangibles'] if extra.get('combined_ppe_intangibles') is not None else None,'reported_operating_margin':vals['operating_income']/vals['revenue'],'current_ratio':vals['current_assets']/vals['current_liabilities'],'cfo_to_consolidated_net_income':vals['cfo']/vals['net_income'],'cash_ppe_to_revenue':capex/vals['revenue'] if capex is not None else None,'balance_check_residual':residual,'total_liabilities_for_control':total_liabilities,'liabilities_control_basis':'direct' if vals['liabilities'] is not None else 'sum of separately reported current/noncurrent liabilities; not A-E','cash_bridge_residual':end_cash-vals['cash'],'cash_bridge_components':extra,'proxy_limit':'Defined historical accounting proxy, not FCFF; IFRS/US-GAAP lease and interest differences retained.'}
 spread['cash_flow_sum_residual']=cash_flow_residual
 if m['issuer']=='INFY':
  spread['cash_tax_bridge_residual']=extra['cash_generated_from_operations_before_tax']-extra['cash_taxes_paid']-vals['cfo']
  assert abs(spread['cash_tax_bridge_residual'])<.01
 previous=next((s for s in spreads if s['issuer']==m['issuer'] and s['fiscal_year']==m['fiscal_year']-1),None)
 spread['revenue_growth']=vals['revenue']/previous['facts']['revenue']-1 if previous else None
 spreads.append(spread)
 if m['split']!='final':continue
 ebit=vals['operating_income'];base=Assumptions(*CASES[m['issuer']]['reference'])
 for case,inputs in CASES[m['issuer']].items():
  result=policy_value(ebit,Assumptions(*inputs));result.update({'issuer':m['issuer'],'source_id':m['id'],'case':case,'unit':'USD millions','initial_investment_to_latest_post_ppe_cash':result['upfront_investment']/proxy if proxy else None,'funding_ratio_limit':'Scale diagnostic only; does not establish cash available to fund this policy.'});scenarios.append(result)
 for w in range(6,17):
  for g in range(0,11):
   result=policy_value(ebit,replace(base,wacc=w/100,terminal_growth=g/200));sensitivity.append({'issuer':m['issuer'],'case':f'w{w}_g{g}','reported_ebit':ebit,'assumptions':result['assumptions'],'policy_value':result['policy_value'],'terminal_share_of_net_value':result['terminal_share_of_net_value']})
 for r in [.05,.08,.10,.12,.15,.20,.30]:
  for g in [0,.01,.02,.03,.04,.05,.06]:
   assumptions=replace(base,growth=g,terminal_growth=g,marginal_roic=r,terminal_roic=r)
   result=policy_value(ebit,assumptions);regimes.append({'issuer':m['issuer'],'reported_ebit':ebit,'assumptions':result['assumptions'],'policy_value':result['policy_value'],'no_growth_reference':result['no_growth_reference'],'value_to_no_growth':result['policy_value']/result['no_growth_reference'],'upfront_investment':result['upfront_investment'],'incremental_policy_value':result['incremental_policy_value']})
 reference=policy_value(ebit,base)
 for factor in [.8,1,1.2]:reverse.append({'issuer':m['issuer'],'reference_fraction':factor,**reverse_growth(ebit,base,reference['policy_value']*factor)})
for name,data in [('financial_spread.json',spreads),('valuation_scenarios.json',scenarios),('valuation_sensitivity.json',sensitivity),('growth_return_regimes.json',regimes),('reverse_cases.json',reverse)]:
 (out/name).write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
print(json.dumps({'spreads':len(spreads),'scenarios':len(scenarios),'sensitivity':len(sensitivity),'regimes':len(regimes),'reverse':len(reverse),'financial_identity_residuals_zero':all(s['balance_check_residual']==0 and s['cash_bridge_residual']==0 for s in spreads)}))
