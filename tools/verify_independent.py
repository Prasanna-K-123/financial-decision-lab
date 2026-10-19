"""Independent Decimal excess-return decomposition of policy values.

The main implementation discounts cash flows. Here each increment of NOPAT
is a perpetual profit layer; its investment has NPV dN*(1/WACC-1/ROIC).
The infinite terminal increment stream is summed analytically. No import of
finance_lab.valuation or its year ledger is used.
"""
from decimal import Decimal,localcontext
from pathlib import Path
import argparse,json
D=lambda x:Decimal(str(x))
def independent_value(ebit,a):
 with localcontext() as c:
  c.prec=45;n=D(ebit)*(1-D(a['tax']));w=D(a['wacc']);gt=D(a['terminal_growth']);r0=D(a['marginal_roic']);rt=D(a['terminal_roic']);h=a['horizon'];k=a['high_growth_years'];initial=n;growth=D(a['growth']);value=n/w
  for t in range(h):
   # Profit layer earned next year, funded at current time t.
   next_year=t+1;g=growth if next_year<=k else growth+(gt-growth)*D(next_year-k)/D(h-k)
   dn=n*g;r=r0 if t<k else r0+(rt-r0)*D(t-k+1)/D(h-k+1)
   value+=dn*(1/w-1/r)/(1+w)**t;n+=dn
  value+=n*gt*(1/w-1/rt)*(1+w)/(w-gt)/(1+w)**h
  return value
p=argparse.ArgumentParser();p.add_argument('reports');a=p.parse_args();root=Path(a.reports);cases=[]
for file in ['valuation_scenarios.json','valuation_sensitivity.json','growth_return_regimes.json']:
 for row in json.loads((root/file).read_text()):
  expected=independent_value(row['reported_ebit'],row['assumptions']);actual=D(row['policy_value']);error=abs(actual-expected);limit=D('0.000001')+abs(expected)*D('0.000000000002');assert error<=limit,(file,row['issuer'],error,limit)
  cases.append({'file':file,'issuer':row['issuer'],'absolute_error_usd_millions':float(error),'tolerance_usd_millions':float(limit)})
report={'method':'45-digit Decimal incremental-profit-layer/excess-return decomposition; separate from discounted cash-flow implementation','cases_checked':len(cases),'all_passed':True,'max_absolute_error_usd_millions':max(x['absolute_error_usd_millions'] for x in cases),'absolute_tolerance_usd_millions':.000001,'relative_tolerance':2e-12,'units':'USD millions; absolute tolerance 0.000001 million = USD 1','external_independent_reviewer':False,'checks':cases}
(root/'independent_math_verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print({k:v for k,v in report.items() if k!='checks'})
