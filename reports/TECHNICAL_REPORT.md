# Corporate Finance Decision Lab — technical report

Prasanna K · M.A. Actuarial Economics, MSE · Revised 28 October 2026

The [five-page PDF](../artifacts/P7_Technical_Report.pdf) documents the source
audit, chronological workflow, complete evaluation, financial controls, growth
funding, independent model reconciliation and reproduction boundaries.

## Data and fixed comparison

Microsoft, Target and Infosys FY 2023/24 form six development reports; FY 2025
forms three final report cases. Nine original issuer reports, 108 financial
targets and 27 unsupported controls. All 270 two-method responses are retained.
Report calendars differ and every main monetary unit is USD millions. References
are source transcriptions, not external human review, and are not inference inputs.

Final results: both methods 33 supported correct /36 financial targets, three
direct-unavailable abstentions, nine control rejections. Development: strict 66/72,
literal 64/72; six unavailable targets for each. Valid consolidated annual MD&A
duplicates count as correct baseline provenance. The two development errors are
Infosys D&A prior-year cells. No final superiority or universal extraction claim.

Original method code was frozen after development and predictions were committed
before final annotation/scoring. Documented validation and alias-conflict revisions
preserve that original code and freeze; current reconstruction checks the exact
declared revisions. Conflicting supported aliases now abstain before preference. The reports are already public: Target FY 2025 cover
highlights were incidentally displayed in source review. This is not a blind,
prospective or unseen-issuer evaluation. Three final clusters do not justify a
population confidence interval. The public repository is a clean completed-study
import; private build IDs are process records, not external timestamp certification.

## Finance and mathematical checks

All nine balance identities, cash-flow sums and cash bridges reconcile. Target
liabilities use current+noncurrent source subtotals, not an A-E plug. Microsoft
D&A+other is unavailable as pure D&A; Infosys PPE+intangibles is unavailable as
pure cash PPE. Separate combined/derived controls do not replace those targets.
CFO-minus-cash-PPE is a named historical accounting proxy, not FCFF.

Ten-year growth policy: N0=EBIT*(1-tax), It=(N(t+1)-Nt)/Rt and Ft=Nt-It.
V0=-I0+sum(Ft/(1+w)^t,t=1..10)+TV10/(1+w)^10, with
F11=N11*(1-gTerminal/RTerminal) and TV10=F11/(w-gTerminal).
Funding date 0 is real: no free first-year growth. Constant ROIC=WACC makes
growth value-neutral. Assumed ROIC/growth/WACC/tax are scenarios; reported EBIT
expense/lease basis is retained and no equity/market-price bridge is asserted.

Nine scenarios, 363 sensitivity cases, 147 constant-regime evaluations and nine
reverse cases are fixed in the protocol. 519 case evaluations match a separately
implemented 45-digit Decimal incremental-profit-layer formulation. The normalized
49-regime grid repeats at three profit scales; these are not independent data.
Seven reverse targets solve; two 80% targets are unreachable in [0%, 25%] growth.

The formula workbook has 932 numeric reconciliations across all nine cases,
input-change and missing/zero boundaries, independent profit-layer checks and
export/reopen recalculation. Artifact Tool was used; native Excel was not executed.

## Reproduction

A fresh source/code directory repeated all original report decoding/OCR and
reproduced eleven scientific outputs byte for byte in 565.57 seconds. Maximum
child RSS 553,208 KiB; Python 3.12.14, PyMuPDF 1.26.6, Tesseract 5.3.4 and a pinned
English trained-data hash. No source cache of decoded rows was reused.
An 8.71-second run with all nine decoded structures cached is reported separately.
Those are historical runs. On 28 October 2026, the corrected alias-conflict
method freshly reacquired all nine exact source versions and repeated decoding/OCR
with no decoded cache. All 270 responses and eleven scientific outputs remain
byte-identical. Actual compute wall time was 579.83 seconds and maximum child
RSS 561,684 KiB, using PyMuPDF 1.26.7 and the same Tesseract/trained-data identity.
Network acquisition and document/workbook/browser generation are outside that
timing. No cross-platform, external-review or human-time-saving claim.

The public numeric route rebuilds nine outputs from published facts/sealed
predictions and checks the two prediction hashes. It is not a fresh original
PDF/DOCX audit. See README, source/prediction manifests, complete error ledger,
independent_math_verification.json, workbook_verification.json and
clean_reproduction.json for historical scope and
alias_conflict_verification_20261026.json for the completed 28 October revision.

Primary originals are linked in data/sources.json and per-field locators in
data/references.json. Raw copyrighted issuer reports remain private. Growth and
reinvestment background: [Damodaran, NYU Stern](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/growth.htm).
