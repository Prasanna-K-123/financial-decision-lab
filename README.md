# Corporate Finance Decision Lab

[![Public research checks](https://github.com/Prasanna-K-123/financial-decision-lab/actions/workflows/verify.yml/badge.svg)](https://github.com/Prasanna-K-123/financial-decision-lab/actions/workflows/verify.yml)

**Annual-report facts, cash-generation analysis and the capital required to fund growth.**

Prasanna K · M.A. Actuarial Economics, Madras School of Economics

Microsoft, Target and Infosys, FY 2023–FY 2025. Nine primary issuer reports feed a
source-linked financial spread, a retrospective extraction check, a ten-year
operating-policy model and an independently reconciled formula workbook.

- Microsoft FY 2025 cash PPE spending rose **45.1%**, versus **14.9%** revenue growth.
  CFO less cash PPE fell from USD 74,071m to USD 71,611m despite higher earnings.
- Target FY 2025 CFO less cash PPE fell **36.7%**, from USD 4,476m to USD 2,835m.
  Its reported operating margin fell from 5.2% to 4.9%.
- Infosys FY 2025 CFO rose USD 1,203m. Lower cash taxes contributed USD 452m
  (**37.6%**) of that increase. The separate combined PPE/intangibles measure
  must not be passed off as pure cash PPE.

These are historical accounting observations. CFO-minus-investment proxies are
not FCFF. Scenario ROIC, tax, growth and WACC are declared assumptions, not market
forecasts. Policy values retain reported EBIT accounting and exclude financing,
nonoperating assets and equity adjustments; no target share price is claimed.

[Interactive evidence browser](https://prasanna-k-123.github.io/financial-decision-lab/)
· [Decision memo](reports/DECISION_MEMO.md)
· [Technical report](reports/TECHNICAL_REPORT.md)
· [Formula workbook](artifacts/Corporate_Finance_Decision_Lab.xlsx)
· [Seven-study portfolio](docs/portfolio.html)

The FY 2025 policy anchors form a fixed retrospective research sample; they are
not a claim to use each issuer's latest available filing. The
[live browser verification](reports/live_browser_verification.json) checks all
nine rendered scenarios, all 363 sensitivity cells and the nine source displays.

The [20 October editorial revision](reports/editorial_revision_20261020.json)
corrects report spacing. All eleven scientific outputs, the frozen method and
the original v1.0.0 research record are unchanged.

The [20 October input-validation revision](reports/input_validation_revision_20261020.json)
accepts decimal percentages, enforces the displayed field bounds and associates
errors with their input. It also handles roundoff at the declared minimum WACC
spread. Saved research outputs are unchanged. The subsequent
[Python validation correction](reports/python_validation_revision_20261020.json)
applies the same roundoff handling to the Python API. The original method file
and freeze are retained; integrity checks permit only this exact validation
patch. No financial formula, saved scenario, prediction or reported score changed.

## Evidence that can be checked

| Check | Result | Interpretation |
| --- | --- | --- |
| Final fiscal-year extraction | Both methods: 33 supported correct / 36 financial targets; three justified abstentions | No final-year accuracy superiority. Nine unsupported controls are separate API-contract tests. |
| Development check | Strict 66/72; literal 64/72; six direct-unavailable targets retained | The two baseline errors used the wrong financial-year column. Development results are not final-test evidence. |
| Financial controls | All nine balance identities, cash-flow sums and ending-cash bridges reconcile | Target liabilities use independently reported current/noncurrent subtotals, not an assets-minus-equity plug. |
| Conditional model | Nine scenarios, 363 sensitivity cases, 147 constant-regime cases and nine reverse cases | Two reverse targets are unreachable in the fixed bracket; they are not extrapolated. |
| Independent mathematics | 519 case evaluations checked by 45-digit Decimal profit-layer valuation | Different formulation from the main cash-flow discounting implementation; no external-review claim. |
| Workbook | 932 numeric reconciliations; all nine cases; editable-input, missing/zero and export/reopen checks | Verified in Artifact Tool; native Excel was not executed. |
| Clean raw-source reconstruction | Eleven scientific outputs identical after repeating all report decoding/OCR | Same environment, pinned cached bytes. Not a fresh-network or cross-platform replication claim. |

Only three final report clusters are available. These are already-public,
retrospective cases, not an unseen-issuer test. Target FY 2025 cover highlights
were incidentally displayed during source identity review; no blind evaluation
claim is made. Valid annual consolidated MD&A duplicates count as correct
baseline provenance. No final-error retuning or artificial scope penalty.

## Reproduce the numeric research from this public checkout

Python 3.12 and the pinned packages. This checks the original freeze, the
documented validation correction and prediction hashes,
rebuilds nine scientific outputs from the published numeric facts and annotations,
and reconciles the valuation through the separate Decimal formulation:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python tools/reproduce_numeric.py
```

This numeric route does not independently re-audit the original PDF/DOCX cells.
The workflow runs it on each push. Source extraction has its own reproduction.

## Reproduce the original source-cell pipeline

The [source manifest](data/sources.json) pins exact issuer URLs, original hashes,
report identities, fiscal dates and USD-million units. Raw issuer reports stay
private and are not relicensed here. Tesseract 5.3.4 with English trained data is
needed for a corrupt native text map in Target FY 2023 and affected other pages.
The pinned trained-data hash and actual clean-run scope are in
[clean reconstruction](reports/clean_reproduction.json).

```bash
python tools/acquire_sources.py --output source_cache
PYTHONPATH=src python tools/run_study.py --sources source_cache --decoded work/decoded --output work/reconstructed
```

Acquisition reuses hash-checked bytes, stops on a source change or denial and
never silently substitutes another version. The full scientific run from a
fresh directory repeated all decoding/OCR and reproduced eleven output hashes
in 565.57 seconds, with maximum child RSS 553,208 KiB. Runtime excludes workbook,
PDF and browser generation and is not a human-time-saving claim. A separate
cached structure run took 8.71 seconds. See the per-source cache flags.

## Research history and boundaries

The [protocol](PROTOCOL.md), [frozen method](reports/extractor_freeze.json),
[prediction seal](reports/prediction_seal.json), [references](data/references.json)
and [complete error ledger](reports/error_ledger.json) expose the evidence chain.
The original working freezes were recorded privately before final annotation;
this repository is a clean import of the completed study, not a claim that its
public import commits predate the research. Private build IDs are process
records rather than external timestamp certification. The old inaccessible
SEC API proposal is retired and contributes no results to this study.

The reports use different fiscal calendars and issuer-hosted versions retrieved
later. They are not one synchronous market date or immutable SEC accession
snapshots. Missing direct D&A, cash PPE and total liabilities are disclosed;
combined/derived controls keep separate labels. IFRS/US-GAAP lease, interest,
expense and tax conventions remain. Code tests, mathematical agreement and a
small retrospective check do not establish universal extraction accuracy,
commercial deployment, investment returns or regulatory compliance.
