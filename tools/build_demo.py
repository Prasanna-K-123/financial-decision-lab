"""Build the offline finance explorer and preserve the current portfolio guide."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = (
    'P7_Technical_Report.pdf',
    'P7_Decision_Memo.pdf',
    'Prasanna_K_Research_Portfolio.pdf',
    'Corporate_Finance_Decision_Lab.xlsx',
)


def portfolio(template, projects):
    """Render the same project identities used by the printable guide."""
    if len(projects) != 7 or len({p['key'] for p in projects}) != 7:
        raise ValueError('Expected seven distinct portfolio identities.')
    cards = []
    escape = html.escape
    for number, project in enumerate(projects, 1):
        key, repo = project['key'], project['repo']
        if not re.fullmatch(r'[a-z-]+', key) or not re.fullmatch(r'[a-z-]+', repo):
            raise ValueError('Invalid portfolio identity.')
        repository = 'https://github.com/Prasanna-K-123/' + repo
        links = [(f'https://prasanna-k-123.github.io/{repo}/', 'Explore results')]
        for item in project['evidence']:
            path = item['path']
            if path.startswith('/') or '..' in path.split('/') or ':' in path:
                raise ValueError('Evidence must use a relative repository path.')
            kind = 'tree' if path.endswith('/') else 'blob'
            links.append((repository + '/' + kind + '/main/' + path, item['label']))
        links.append((repository, 'Repository'))
        navigation = ''.join(f'<a href="{escape(url, quote=True)}">{escape(label)}</a>' for url, label in links)
        cards.append(f'<article id="study-{key}"><div class="number">{number:02d}</div>'
                     f'<h2>{escape(project["name"])}</h2><p>{escape(project["description"])}</p>'
                     f'<p class="methods"><strong>Methods</strong> {escape(project["methods"])}</p>'
                     f'<p class="roles">{escape(project["roles"])}</p>'
                     f'<nav class="evidence" aria-label="{escape(project["name"], quote=True)} evidence">{navigation}</nav></article>')
    if template.count('__PROJECT_CARDS__') != 1 or template.count('__STUDY_KEYS__') != 1:
        raise ValueError('Invalid portfolio template placeholders.')
    return template.replace('__PROJECT_CARDS__', ''.join(cards)).replace('__STUDY_KEYS__', json.dumps([p['key'] for p in projects]))


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
        (exports / name).write_bytes((root / 'artifacts' / name).read_bytes())
    # Project identities/descriptions are shared with the printable guide.
    (docs / 'portfolio.html').write_text(portfolio((root / 'tools/portfolio_template.html').read_text(), read('data/portfolio_projects.json')))
    return {
        'index_bytes': (docs / 'index.html').stat().st_size,
        'portfolio_studies': len(read('data/portfolio_projects.json')),
        'exports': len(EXPORTS),
    }


if __name__ == '__main__':
    print(json.dumps(build()))
