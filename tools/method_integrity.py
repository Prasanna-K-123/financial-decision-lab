"""Verify the retained original freeze and the exact documented revision bytes.

The original freeze is not rewritten. A preserved original and a readable
patch expose the post-freeze correction; all other frozen files must match.
"""
from pathlib import Path
import hashlib
import json

REVISED_VALUATION_SHA256 = '4fb068ce802a9622f2223139190bfb047e0af5b0504881e26abcf448964eba6e'
REVISION_PATCH_SHA256 = 'bbc071c33d3316e3e8e5e68eae4136367241012620082b82e63545851acc7753'
ALIAS_EXTRACTION_SHA256 = 'e0530729300ee399da356b6162e5a90a337d73edfe7bacdab04be73b74f4450d'
ALIAS_PATCH_SHA256 = 'ecce0a7de05cb9e7a81a5603b460ad5f87b655d20119a8e4424e05553d6dd848'


def verify_method_integrity(root):
    root = Path(root)
    freeze = json.loads((root / 'reports/extractor_freeze.json').read_text())
    revisions = {
        'src/finance_lab/valuation.py': (REVISED_VALUATION_SHA256, REVISION_PATCH_SHA256,
            'reproducibility/original_valuation.py', 'reproducibility/validation_revision_20261020.patch',
            'reports/python_validation_revision_20261020.json'),
        'src/finance_lab/extraction.py': (ALIAS_EXTRACTION_SHA256, ALIAS_PATCH_SHA256,
            'reproducibility/original_extraction.py', 'reproducibility/alias_conflict_revision_20261026.patch',
            'reports/alias_conflict_revision_20261026.json'),
    }
    changed = []
    for name, expected in freeze['source_code_sha256'].items():
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if digest == expected:
            continue
        if name not in revisions or digest != revisions[name][0]:
            raise ValueError('Unlisted frozen-method change: ' + name)
        _, patch_digest, original_name, patch_name, receipt_name = revisions[name]
        revision = json.loads((root / receipt_name).read_text())
        original = root / original_name
        if hashlib.sha256(original.read_bytes()).hexdigest() != expected:
            raise ValueError('Preserved original does not match the original freeze')
        patch = root / patch_name
        if hashlib.sha256(patch.read_bytes()).hexdigest() != patch_digest:
            raise ValueError('Documented revision patch changed')
        if (revision['original_sha256'] != expected or revision['revised_sha256'] != digest
                or revision['revision_patch_sha256'] != patch_digest):
            raise ValueError('Revision receipt does not identify the checked methods')
        changed.append(name)
    if set(changed) != set(revisions):
        raise ValueError('Expected each documented revision exactly once')
    return {'original_freeze_entries': len(freeze['source_code_sha256']),
            'unchanged_files': len(freeze['source_code_sha256']) - len(changed),
            'documented_validation_revisions': changed,
            'original_method_preserved_and_hash_verified': True,
            'exact_revised_method_and_patch_hash_verified': True}
