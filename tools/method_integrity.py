"""Verify the retained original freeze and the exact documented revision bytes.

The original freeze is not rewritten. A preserved original and a readable
patch expose the post-freeze correction; all other frozen files must match.
"""
from pathlib import Path
import hashlib
import json

REVISED_VALUATION_SHA256 = '4fb068ce802a9622f2223139190bfb047e0af5b0504881e26abcf448964eba6e'
REVISION_PATCH_SHA256 = 'bbc071c33d3316e3e8e5e68eae4136367241012620082b82e63545851acc7753'


def verify_method_integrity(root):
    root = Path(root)
    freeze = json.loads((root / 'reports/extractor_freeze.json').read_text())
    revision = json.loads((root / 'reports/python_validation_revision_20261020.json').read_text())
    changed = []
    for name, expected in freeze['source_code_sha256'].items():
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if digest == expected:
            continue
        if name != 'src/finance_lab/valuation.py' or digest != REVISED_VALUATION_SHA256:
            raise ValueError('Unlisted frozen-method change: ' + name)
        original = root / 'reproducibility/original_valuation.py'
        if hashlib.sha256(original.read_bytes()).hexdigest() != expected:
            raise ValueError('Preserved original does not match the original freeze')
        patch = root / 'reproducibility/validation_revision_20261020.patch'
        if hashlib.sha256(patch.read_bytes()).hexdigest() != REVISION_PATCH_SHA256:
            raise ValueError('Documented revision patch changed')
        if (revision['original_sha256'] != expected or revision['revised_sha256'] != digest
                or revision['revision_patch_sha256'] != REVISION_PATCH_SHA256):
            raise ValueError('Revision receipt does not identify the checked methods')
        changed.append(name)
    if changed != ['src/finance_lab/valuation.py']:
        raise ValueError('Expected the documented valuation revision exactly once')
    return {'original_freeze_entries': len(freeze['source_code_sha256']),
            'unchanged_files': len(freeze['source_code_sha256']) - len(changed),
            'documented_validation_revisions': changed,
            'original_method_preserved_and_hash_verified': True,
            'exact_revised_method_and_patch_hash_verified': True}
