"""Verify the original freeze and the explicitly documented validation correction.

The original freeze is never rewritten. Only the exact roundoff-guard patch
below is accepted; an unlisted model or extraction change still fails.
"""
from pathlib import Path
import hashlib
import json

OLD = '        if not 0<=self.tax<1 or not 0<self.wacc<=0.50 or self.wacc-self.terminal_growth<0.0001:\n'
NEW = ('        spread_roundoff = 8 * math.ulp(1.0) * max(abs(self.wacc), abs(self.terminal_growth), 0.0001)\n'
       '        if not 0<=self.tax<1 or not 0<self.wacc<=0.50 or self.wacc-self.terminal_growth<0.0001-spread_roundoff:\n')


def verify_method_integrity(root):
    root = Path(root)
    freeze = json.loads((root / 'reports/extractor_freeze.json').read_text())
    revision = json.loads((root / 'reports/python_validation_revision_20261020.json').read_text())
    changed = []
    for name, expected in freeze['source_code_sha256'].items():
        current = (root / name).read_bytes()
        digest = hashlib.sha256(current).hexdigest()
        if digest == expected:
            continue
        if name != 'src/finance_lab/valuation.py':
            raise ValueError('Unlisted frozen-method change: ' + name)
        original = (root / revision['preserved_original']).read_bytes()
        if hashlib.sha256(original).hexdigest() != expected:
            raise ValueError('Preserved original does not match the original freeze')
        text = original.decode('utf-8')
        if text.count(OLD) != 1 or text.replace(OLD, NEW, 1).encode('utf-8') != current:
            raise ValueError('Change exceeds the declared roundoff validation patch')
        if revision['original_sha256'] != expected or revision['revised_sha256'] != digest:
            raise ValueError('Revision receipt does not identify the checked methods')
        changed.append(name)
    if changed != ['src/finance_lab/valuation.py']:
        raise ValueError('Expected the declared validation revision exactly once')
    return {'original_freeze_entries': len(freeze['source_code_sha256']),
            'unchanged_files': len(freeze['source_code_sha256']) - len(changed),
            'documented_validation_revisions': changed,
            'original_method_preserved_and_hash_verified': True}
