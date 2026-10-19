# Corporate Finance Decision Lab — research protocol

Release edition,19October2026. This is an editorial publication of the private
working protocol, retaining the same sample, definitions, methods, assumptions
and evaluation boundary. Original private working protocol SHA256: be2155f41d3626ca329d0d992179a6579b82394dc3d8066b6db808fdfd4c1248.
The original was committed at e5291c624cd33d1e7567e3b32033f76b92bfbdcd before
financial-target extraction/scoring. This is a process record rather than
external preregistration or timestamp certification.

## Research question and sample scope

Turn primary annual reports into a traceable financial spread and assess when
growth creates value after funding its reinvestment. The main product is an
analyst decision model with a checked data layer, not a general chatbot or a
universal extraction claim.

The data route is issuer-hosted annual reports. The earlier inaccessible
27-filing/405-request SEC API proposal is retired and contributes no empirical
results. This study uses nine reports and135 requests. Microsoft, Target and
Infosys provide different presentation/accounting cases; no financial target
or extraction outcome was used to select them.

## Sources and research boundary

Use Microsoft FY2023, FY2024 and FY2025 Form10-K DOCX reports; Target FY2023,
FY2024 and FY2025 annual-report PDFs containing the10-K; and Infosys FY2023,
FY2024 and FY2025 Form20-F PDFs, all linked by their official report sites.
Pin original source bytes, SHA256, URL, retrieval time, publisher/report year,
stated currency/scale, exact financial-statement columns and fiscal dates.
Target's fiscal-year label differs from the calendar year of its period end.
Never infer presentation currency from the exchange or issuer's country.

Questions concern the stated fiscal year in the pinned issuer-hosted version
downloaded on19October2026. No immutable original-filing-time vintage or
point-in-time market backtest is claimed. HTTP Last-Modified is not a filing
date and does not prove a restatement. Cover/form identity, fiscal periods and
statement scope are verified from the actual reports. No SEC API snapshot or
accession-equivalence claim is made for issuer copies without such evidence.

Raw reports/artwork remain in the owner's private source cache. Publish code,
numeric research facts, small common financial row labels and source locators;
do not relicense or republish complete issuer reports or website artwork.
Public source links and exact byte guards support reacquisition. A clean run
must also work from the pinned private cache. Document any inaccessible or
changed public URL rather than accepting different bytes silently.

## Fixed financial targets and chronological check

Nine report cases: three issuers x three fiscal years. FY2023/FY2024 reports
are development cases (six reports). All FY2025 reports form the final fiscal-
year holdout (three reports). Freeze extraction aliases, scope/year/unit rules
and code after development and before revealing or scoring final references.
These are retrospective, already-public reports, not a live prospective test.
There is no unseen-issuer generalisation claim or pseudo-large independent n.

Twelve targets per report: revenue; operating income; consolidated net income;
assets; liabilities; equity; cash and cash equivalents; current assets; current
liabilities; operating cash flow; gross cash purchases of PPE; and depreciation
and amortisation. Three unsupported controls: current share price, customer
count and undisclosed future-year revenue. Total135 requests =108 financial
targets +27 controls. Do not drop difficult requests from the denominator.

Target definitions: annual flows versus fiscal-end balances; consolidated
scope; source's declared presentation currency and million-unit normalisation.
Net income is the consolidated amount including NCI where separately present.
Equity is consolidated equity including NCI. Cash excludes short-term investments
unless the report explicitly combines them, in which case the exact requested
cash-only target must abstain or be separately decomposed with evidence. PPE
purchases are cash outflows normalised to a positive amount; do not substitute
asset acquisitions, net disposals, noncash leases or a combined PPE/intangible
amount without a separate supported PPE figure. A combined 'depreciation,
amortisation and other' figure is not pure D&A. Undisclosed/ambiguous direct
targets remain unsupported; a derived liabilities residual is reported as a
derived control, never relabelled as directly extracted liabilities.

Reference cells are separately annotated from actual source statement tables:
file hash, PDF page or DOCX table/row/column, source row label/year, raw unit,
normalised value, sign treatment and direct/unsupported status. References are
workflow annotations, not a claim of external human review. They cannot be
inference inputs. Both methods get only raw source structure and the audited
document identity/calendar/currency metadata. They share one alias inventory.

Primary baseline: literal row-label/year/currency lookup anywhere in the
document, with no financial-statement-scope protection. Strict method: exact
requested annual/instant column, correct statement and consolidated scope,
declared units, conflict rejection and provenance. All final answers are checked
against source-supported references, including numerical, unit, period and
scope errors. Structural unsupported-control rejection is described as an API
contract check, not a language-model hallucination benchmark.

Report financial coverage, supported correctness/all targets, conditional
precision, direct unsupported targets, control abstention and provenance errors,
by issuer/report/split. Three final report clusters do not support a dependable
population confidence interval. Show exact paired case differences and error
ledgers; do not present135 correlated requests as independent, tune on final
errors or force a superiority claim.

## Observed cash analysis and conditional decision models

For each firm, spread all three fiscal years and reconcile balance identities,
growth, operating margin, current ratio, cash conversion and cash-PPE intensity.
Report CFO minus cash PPE as a specifically defined historical cash-generation
proxy. It is NOT FCFF, cash available for dividends or a harmonised lease/interest
metric across accounting regimes. Keep currency, consolidation and classification
limits visible. Missing direct D&A does not get manufactured to fill a bridge.

DCF is a separate ten-year, net-reinvestment model anchored to the latest
reported EBIT and an assumed normalised tax rate25%. Marginal ROIC, growth,
terminal return/growth and WACC are explicit scenarios, not estimated market
inputs or forecasts. Model net investment includes the aggregate of net fixed,
intangible and working-capital growth investment after maintenance, rather than
asserting that observed CFO-minus-PPE is unlevered FCFF.

The accounting expense/lease convention of reported EBIT is retained in each
anchor. Marginal-return assumptions apply on that same model operating basis;
there is no harmonised cross-firm ROIC estimate, lease/debt/equity bridge or
target share price. Values are conditional operating-policy values before debt,
cash/nonoperating assets, NCI, pension and option adjustments. Do not sell them
as an observed enterprise valuation or investment recommendation.

### Exact funding timing

Let N0=reportedEBIT*(1-assumedTax). Growth g1..g5 is fixed to the case's initial
growth; g6..g10 fades linearly to terminal growth; g11=terminal growth.
Nt=N(t-1)*(1+gt). New capital paid at time t earns its marginal return in year
t+1. Its return R0..R4 is the initial case ROIC; R5..R10 fades linearly to the
terminal ROIC, reaching it at t10. Net investment It=(N(t+1)-Nt)/Rt.
I0 is paid immediately and deducted from value. End-year cash flow Ft=Nt-It.
Terminal F11=N11*(1-gTerminal/RTerminal); TV10=F11/(WACC-gTerminal).
Policy value V0=-I0+sum(Ft/(1+WACC)^t,t1..10)+TV10/(1+WACC)^10.
This explicit upfront funding convention prevents free first-year growth.
For a constant regime with ROIC=WACC, V0 must equal N0/WACC regardless of
growth. Check it independently. A forced destructive-growth policy can have
negative value; that is not a negative market-equity/limited-liability claim.
The no-growth cash-return reference is N0/WACC, not a rival fitted forecast.

### Fixed scenarios and grids

All cases use WACC10% and tax25% as common illustrative hurdles; not current
market calibrations. Initial growth / marginal ROIC / terminal ROIC / terminal
growth, respectively:

| Firm | Downside | Reference | Expansion |
| --- | --- | --- | --- |
| MSFT | 5%/10%/10%/2% | 10%/18%/12%/2.5% | 15%/25%/15%/3% |
| TGT | 0%/7%/8%/1% | 2%/12%/10%/2% | 4%/18%/12%/2.5% |
| INFY | 2%/10%/10%/2% | 5%/16%/12%/2.5% | 8%/22%/15%/3% |

Primary sensitivity: reference case, WACC6%..16% in1pp steps, terminal growth
0%..5% in0.5pp steps:121 cases per firm. Constant-regime decision grid:
ROIC5%,8%,10%,12%,15%,20%,30% x growth0%,1%,2%,3%,4%,5%,6%, WACC10%:
49 policies per firm. Report value versus no-growth reference and upfront
funding. These grids are scenarios, not probability distributions.

Reverse cases target80%,100%,120% of that firm's reference-case operating
value. Solve initial growth only on[0,25%], holding other reference assumptions
fixed; report unreachable cases and residuals rather than extrapolate. No
market quote, implied market expectation or price target is claimed. Comparing
upfront model investment with historical post-PPE cash is a scale diagnostic,
not a complete funding-capacity assertion.

## Release specification

Audit all nine original reports and the135-request inventory. Preserve source
references separately from inference. Freeze methods after the six development
cases; seal final predictions before reference scoring. Report every error,
abstention and case difference without final-error retuning. Reconstruct all
scientific outputs from pinned source bytes in a clean directory. Reconcile the
formula workbook and alternate valuation formulation, render and inspect the
research documents, and verify the public browser and downloadable artifacts.
