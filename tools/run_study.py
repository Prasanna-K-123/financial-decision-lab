"""One command to reconstruct scientific outputs from pinned original reports."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib,time,resource,os
from method_integrity import verify_method_integrity
p=argparse.ArgumentParser();p.add_argument('--sources',required=True);p.add_argument('--output',required=True);p.add_argument('--decoded',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=Path(a.output);out.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
freeze=json.loads((root/'reports/extractor_freeze.json').read_text())
method_check=verify_method_integrity(root)
env={**os.environ,'PYTHONPATH':str(root/'src')};commands=[
 [sys.executable,'tools/predict.py',a.sources,a.decoded,str(out)],
 [sys.executable,'tools/evaluate.py',str(out),str(root/'data/references.json'),str(out)],
 [sys.executable,'tools/finance_cases.py',str(root/'data/references.json'),str(root/'data/financial_aux.json'),str(out)],
 [sys.executable,'tools/verify_independent.py',str(out)]]
for cmd in commands:subprocess.run(cmd,cwd=root,env=env,check=True)
assert verify_method_integrity(root)==method_check,'Method identity changed during reconstruction'
seal=json.loads((root/'reports/prediction_seal.json').read_text())
for name in ['development_predictions.json','final_predictions.json']:
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=seal['files']['reports/'+name]['sha256']:raise ValueError('Prediction seal changed: '+name)
names=['development_predictions.json','final_predictions.json','evaluation_ledger.json','evaluation_summary.json','error_ledger.json','financial_spread.json','valuation_scenarios.json','valuation_sensitivity.json','growth_return_regimes.json','reverse_cases.json','independent_math_verification.json']
manifest={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in names}
(out/'scientific_hashes.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
(out/'runtime_full_study.json').write_text(json.dumps({'wall_seconds':time.perf_counter()-start,'max_child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'scope':'Raw-source decoding, 270 deterministic answers, reference scoring, financial model grids and independent Decimal checks; no network, human-time or paid-provider timing claim.','python':sys.version,'original_report_count':9},indent=2)+'\n')
print(json.dumps({'scientific_outputs':len(names),'hashes':manifest}))
