"""Acquire only the pinned official reports. No retries or source substitution."""
from pathlib import Path
import argparse,json,hashlib,urllib.request
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[1]
for m in json.loads((root/'data/sources.json').read_text()):
 target=out/m['file']
 if target.exists():raw=target.read_bytes()
 else:
  assert m['url'].startswith('https://')
  with urllib.request.urlopen(m['url'],timeout=90) as response:raw=response.read()
 if len(raw)!=m['bytes'] or hashlib.sha256(raw).hexdigest()!=m['sha256']:raise ValueError('Source version changed: '+m['id'])
 if not target.exists():target.write_bytes(raw)
 print(m['id'],'original hash verified')
