"""Raw-source predictions only. This module never opens reference annotations."""
import argparse,json,gzip,hashlib,time
from dataclasses import asdict
from pathlib import Path
from finance_lab.documents import read_document,Row,Token,checked_bytes
from finance_lab.extraction import FIELDS,CONTROLS,extract

p=argparse.ArgumentParser();p.add_argument('source_cache');p.add_argument('decoded');p.add_argument('output');a=p.parse_args()
root=Path(__file__).resolve().parents[1];sources=json.loads((root/'data/sources.json').read_text())
decoded=Path(a.decoded);decoded.mkdir(parents=True,exist_ok=True);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
results=[];runtime=[]
for m in sources:
 checked_bytes(Path(a.source_cache)/m['file'],m['sha256'])
 cache=decoded/(m['id']+'.json.gz');t=time.perf_counter();cache_hit=cache.exists()
 if cache_hit:
  d=json.loads(gzip.decompress(cache.read_bytes()));assert d['source_sha256']==m['sha256']
  rows=[Row(**{**r,'tokens':tuple(Token(**t) for t in r['tokens'])}) for r in d['rows']]
 else:
  rows=read_document(Path(a.source_cache)/m['file'],m['sha256']);cache.write_bytes(gzip.compress(json.dumps({'source_sha256':m['sha256'],'rows':[asdict(r) for r in rows]},ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
 for field in list(FIELDS)+list(CONTROLS):
  for method in ['literal','strict']:
   results.append({'request_id':m['id']+'__'+field,'source_id':m['id'],'split':m['split'],'method':method,'field':field,**extract(m,rows,field,strict=method=='strict')})
 runtime.append({'source':m['id'],'source_decode_cache_hit':cache_hit,'rows':len(rows),'ocr_rows':sum(':ocr:' in r.locator for r in rows),'decode_and_30_requests_seconds':time.perf_counter()-t})
 print(m['id'],'predicted',flush=True)
for split in ['development','final']:
 payload=[x for x in results if x['split']==split];(out/(split+'_predictions.json')).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
(out/'runtime_prediction.json').write_text(json.dumps(runtime,indent=2)+'\n')
print(json.dumps({'predictions':len(results),'final_prediction_sha256':hashlib.sha256((out/'final_predictions.json').read_bytes()).hexdigest(),'reference_input':False}))
