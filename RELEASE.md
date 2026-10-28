# Release a reviewed revision

Use `.github/workflows/release.yml` after reviewing the exact commit and creating
its immutable version tag through the authorized account workflow. Do not move
an existing tag to reuse its name.

The workflow is manually dispatched from `main` with an existing version tag
and the complete reviewed 40-character commit SHA. Dispatch SHA, checkout,
current main and the tag's resolved commit must all agree. Annotated tags are
resolved; missing or different tags fail without a tag-creation/movement call.
The verification job has read-only contents access. A separate publication job
gets contents-write access only after verification, rechecks the refs and either
creates the release for that existing tag or accepts an exactly matching prior
release. Different existing release notes are not overwritten. Concurrent
external writers are outside the workflow lock, so refs are checked immediately
before and after the release request; this is not a platform-wide atomic lock.

No data, model or duplicate build artifacts are uploaded, no cache is created by
the release workflow, and no quota or paid infrastructure is increased. The
release does not automatically replace the account's latest-release designation.
Local mock-API tests cover mismatched identities, missing/moved tags, moved main,
annotated tags, cycles and idempotent publication. They are not evidence that a
remote release has been executed.

Verification includes the 25 research and seven guard tests, fresh acquisition
of the nine exact issuer reports, clean decoding/OCR, all 270 responses, original
prediction and scientific-output checks, independent Decimal valuation, and the
finance and seven-project role explorers. The job requires Tesseract5.3.4 and
the pinned English trained-data hash; an incompatible runner fails closed rather
than adopting changed extraction output. Native browser and workbook-application
checks retain their own dated evidence. The separate historical mathematical
workflow still validates its immutable21October snapshots.

The original release records below are historical, not assertions that every
current release has already been published or checked in a native browser.

# v1.0.1 — report typography and public verification

Corrects spacing in the technical report, decision memo and Markdown alternative.
Adds pinned, read-only public verification. Scientific outputs, original method
hashes, sealed predictions, workbook and source annotations remain unchanged.
The original v1.0.0 research record is preserved. The editorial revision receipt
records original and revised document hashes.

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
