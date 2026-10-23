"""Build the offline finance explorer and preserve the current portfolio guide."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = (
    'P7_Technical_Report.pdf',
    'P7_Decision_Memo.pdf',
    'Prasanna_K_Research_Portfolio.pdf',
    'Corporate_Finance_Decision_Lab.xlsx',
)


def build(root: Path = ROOT) -> dict:
    docs = root / 'docs'
    exports = docs / 'exports'
    exports.mkdir(parents=True, exist_ok=True)
    read = lambda name: json.loads((root / name).read_text())
    data = {
        'spread': read('reports/financial_spread.json'),
        'references': read('data/references.json'),
        'cases': read('reports/valuation_scenarios.json'),
        'predictions': read('reports/development_predictions.json') + read('reports/final_predictions.json'),
    }
    template = (root / 'tools/explorer_template.html').read_text()
    script = (root / 'tools/explorer.js').read_text()
    if template.count('__DATA__') != 1 or template.count('__APP__') != 1 or '</script' in script.lower():
        raise ValueError('Invalid explorer template or unsafe inline script terminator.')
    payload = json.dumps(data, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')
    (docs / 'index.html').write_text(template.replace('__DATA__', payload).replace('__APP__', script))
    for name in EXPORTS:
        shutil.copy2(root / 'artifacts' / name, exports / name)
    # Role routes, methods and direct evidence links are authored in this source
    # template. A rebuild must not restore the earlier, simpler seven-card page.
    (docs / 'portfolio.html').write_bytes((root / 'tools/portfolio_template.html').read_bytes())
    return {
        'index_bytes': (docs / 'index.html').stat().st_size,
        'portfolio_studies': len(read('data/portfolio_projects.json')),
        'exports': len(EXPORTS),
    }


if __name__ == '__main__':
    print(json.dumps(build()))
