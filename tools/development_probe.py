"""Inspect development-only requested rows; never load final references."""
import argparse,gzip,json
from pathlib import Path
from finance_lab.documents import Row,Token
from finance_lab.extraction import FIELDS,extract

p=argparse.ArgumentParser();p.add_argument('decoded');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
for meta in json.loads((root/'data/sources.json').read_text()):
 if meta['split']!='development':continue
 data=json.loads(gzip.decompress((Path(a.decoded)/(meta['id']+'.json.gz')).read_bytes()))
 if data['source_sha256']!=meta['sha256']:raise ValueError('Decoded source identity mismatch')
 rows=[Row(**{**r,'tokens':tuple(Token(**t) for t in r['tokens'])}) for r in data['rows']]
 print('\nSOURCE',meta['id'])
 for field in FIELDS:
  for strict in (False,True):
   result=extract(meta,rows,field,strict=strict)
   print(field,'strict' if strict else 'basic',result['value'],result['reason'],
         [(x['locator'],x['row_label']) for x in result['provenance']][:3])
