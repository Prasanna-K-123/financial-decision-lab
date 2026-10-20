"""Public-file numeric reproduction. Does not re-audit original source reports."""
from pathlib import Path
import subprocess,sys,json,hashlib,tempfile,os
from method_integrity import verify_method_integrity
root=Path(__file__).resolve().parents[1];seal=json.loads((root/'reports/prediction_seal.json').read_text());freeze=json.loads((root/'reports/extractor_freeze.json').read_text())
method_check=verify_method_integrity(root)
for name in ['development_predictions.json','final_predictions.json']:assert hashlib.sha256((root/'reports'/name).read_bytes()).hexdigest()==seal['files']['reports/'+name]['sha256'],name
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp);env={**os.environ,'PYTHONPATH':str(root/'src')}
 cmds=[['tools/evaluate.py',str(root/'reports'),str(root/'data/references.json'),str(out)],['tools/finance_cases.py',str(root/'data/references.json'),str(root/'data/financial_aux.json'),str(out)],['tools/verify_independent.py',str(out)]]
 for args in cmds:subprocess.run([sys.executable,*args],cwd=root,env=env,check=True,stdout=subprocess.DEVNULL)
 expected=json.loads((root/'reports/scientific_hashes.json').read_text());checked=[]
 for name,h in expected.items():
  if name.endswith('_predictions.json'):continue
  assert hashlib.sha256((out/name).read_bytes()).hexdigest()==h,name;checked.append(name)
 assert verify_method_integrity(root)==method_check,'Method identity changed during numeric reconstruction'
 print(json.dumps({'passed':True,'reconstructed_scientific_outputs':len(checked),'unchanged_prediction_seals':2,'method_integrity':method_check,'scope':'Public numeric facts/references and sealed predictions; source PDF/DOCX audit and OCR are separate raw-source reproduction.'}))
