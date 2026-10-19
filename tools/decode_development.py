"""Cache transient source structure for development; never publish decoded text."""
from pathlib import Path
import argparse,json,gzip,hashlib,time
from dataclasses import asdict
from finance_lab.documents import read_document

p=argparse.ArgumentParser();p.add_argument('source_cache');p.add_argument('output');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
sources=json.loads((root/'data/sources.json').read_text())
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
for meta in sources:
 if meta['split']!='development':continue
 target=out/(meta['id']+'.json.gz')
 if target.exists():
  print(meta['id'],'already cached',flush=True);continue
 t=time.perf_counter();print('Decoding',meta['id'],flush=True)
 rows=read_document(Path(a.source_cache)/meta['file'],meta['sha256'])
 data={'source_sha256':meta['sha256'],'rows':[asdict(r) for r in rows]}
 raw=json.dumps(data,separators=(',',':'),ensure_ascii=False).encode()
 target.write_bytes(gzip.compress(raw,mtime=0))
 print(json.dumps({'source':meta['id'],'rows':len(rows),'ocr_rows':sum(':ocr:' in r.locator for r in rows),
  'seconds':time.perf_counter()-t,'decoded_sha256':hashlib.sha256(raw).hexdigest(),
  'scoped_groups':sorted(set((r.group,r.section) for r in rows if r.section))}),flush=True)
