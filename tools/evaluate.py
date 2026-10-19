"""Score sealed predictions against separately source-annotated references."""
from pathlib import Path
from decimal import Decimal
from collections import Counter,defaultdict
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('predictions');p.add_argument('references');p.add_argument('output');a=p.parse_args()
pred_dir=Path(a.predictions);refs=json.loads(Path(a.references).read_text());ref={x['request_id']:x for x in refs};ledger=[]
for split in ['development','final']:
 for x in json.loads((pred_dir/(split+'_predictions.json')).read_text()):
  gold=ref[x['request_id']];answer=x['value'] is not None;support=gold['status']=='direct';control=gold['status']=='control'
  numeric=bool(answer and support and Decimal(x['value'])==Decimal(str(gold['value'])))
  locs=gold.get('accepted_answer_locators',[gold.get('locator')])
  provenance=bool(answer and all(y['source_sha256']==gold['source_sha256'] and y['currency']==gold['currency'] and y['unit']=='millions' and y['locator'] in locs and y['display_column_year']==gold.get('display_column_year') for y in x['provenance']))
  correct=bool(numeric and provenance)
  outcome='correct_supported' if correct else 'correct_control_abstention' if control and not answer else 'correct_direct_unavailable_abstention' if not support and not control and not answer else 'missed_supported_target' if support and not answer else 'incorrect_numeric_or_context'
  ledger.append({**x,'reference_status':gold['status'],'reference_value':gold.get('value'),'reference_locator':gold.get('locator'),'answered':answer,'numeric_correct':numeric,'provenance_correct':provenance,'supported_correct':correct,'outcome':outcome,'materiality':'No unreviewed extractor result feeds the decision model. Any unsupported/wrong/missed financial answer requires source review; no dollar materiality threshold excuses a wrong year, unit or combined metric.' if outcome in ['missed_supported_target','incorrect_numeric_or_context'] else None})
summary=[]
for split in ['development','final']:
 for method in ['literal','strict']:
  for case in ['ALL']+sorted({x['source_id'] for x in ledger if x['split']==split}):
   rows=[x for x in ledger if x['split']==split and x['method']==method and (case=='ALL' or x['source_id']==case)]
   fin=[x for x in rows if x['reference_status']!='control'];answers=sum(x['answered'] for x in fin);correct=sum(x['supported_correct'] for x in fin);controls=[x for x in rows if x['reference_status']=='control']
   summary.append({'split':split,'method':method,'case':case,'financial_targets':len(fin),'directly_supported_targets':sum(x['reference_status']=='direct' for x in fin),'answered_financial_targets':answers,'correct_supported_answers':correct,'financial_coverage':answers/len(fin),'supported_correctness_all_targets':correct/len(fin),'conditional_precision':correct/answers if answers else None,'controls':len(controls),'control_abstentions':sum(not x['answered'] for x in controls),'direct_unavailable':sum(x['reference_status']=='unsupported' for x in fin),'missed_supported':sum(x['outcome']=='missed_supported_target' for x in fin),'incorrect_answers':sum(x['outcome']=='incorrect_numeric_or_context' for x in fin)})
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
for name,data in [('evaluation_ledger.json',ledger),('evaluation_summary.json',summary),('error_ledger.json',[x for x in ledger if x['outcome'] in ['incorrect_numeric_or_context','missed_supported_target']])]:
 (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
print(json.dumps([x for x in summary if x['case']=='ALL'],indent=2))
