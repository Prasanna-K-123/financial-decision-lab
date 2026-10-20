# Version 1.0.0 research release

Corporate Finance Decision Lab · Prasanna K

The fixed research sample contains Microsoft, Target and Infosys FY 2023–FY 2025
issuer reports. The code, numeric evidence, formula workbook, reports and browser
are available together. Issuer originals retain their owners' rights and are not
redistributed in the repository.

## Verified evidence

- Nine source reports, 108 financial targets and 27 separate unsupported controls.
- Final extraction: both methods support 33/36 financial targets, with three
  justified abstentions. No final-year accuracy improvement is claimed.
- Eleven scientific outputs reproduced identically from pinned originals in the
  recorded clean run; 519 independent Decimal valuation case evaluations.
- Formula workbook: 932 numeric reconciliations, editable-input and export/reopen
  checks. Verification used Artifact Tool; native Excel was not executed.
- Actual live desktop browser: nine scenarios, 99 annual-ledger rows, all 363
  sensitivity cells and 108 source-case target rows reconciled to frozen evidence.
  Blank inputs, invalid terminal spreads and keyboard activation were checked.
- All four public PDF/XLSX downloads match the committed artifacts through a
  separate HTTPS byte comparison. Browser download controls also completed;
  their downloaded files did not synchronize to the host for an additional hash.

Detailed records are in `reports/clean_reproduction.json`,
`reports/independent_math_verification.json`,
`reports/workbook_verification.json` and
`reports/live_browser_verification.json`. The workflow checks the published
numeric reconstruction, unit tests and exact embedded explorer script.

The original private method/prediction freezes and the later clean public import
are distinguished in `RESEARCH_HISTORY.md` and `reports/research_chronology.json`.
These are retrospective, small-sample research results with explicit accounting
and scenario limits, rather than a market price target or deployed investment
system.
