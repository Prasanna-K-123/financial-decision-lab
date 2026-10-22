# Independent mathematical controls

These deterministic checks test the mathematical behaviour of all seven studies
against independently enumerated or analytic references. They use synthetic
inputs and the pinned public source files; no private rows, credentials, model
fitting or final-outcome selection is required.

| Study | Independent control |
| --- | --- |
| Credit | 7,966 sharp-bound problems with 28,118 binary label completions, for all sample sizes 1–5 with at least one known event and every selection mask. |
| Insurance | 30 Mack currency-scale/row-permutation cases, covariance PSD, four independently reconstructed lognormal moment pairs and 1,000 deterministic simulation draws. |
| Causal decisions | Exact 81-assignment randomization average with deliberately wrong nuisance means; 160 contact-allocation cases compared with 7,280 feasible policies under equal contact cost and the stated contact cap. |
| Treasury | 1,000 key-rate partition rows, 60 closed-form risk cases, 60 discounted runoff-conservation cases, constant-force mortality cash flows and complete active-face enumeration for both current constrained hedge objectives. |
| Inventory | 60 future-data feature perturbations, 60 integer budget/capacity cases and 60 lead-time stock-conservation simulations. The allocation remains a documented heuristic. |
| Inflation | Release-cutoff timezone equivalence, pre-release exclusion, later revisions, base separation and calendar rollover. Full public numeric reconstruction is a separate study command. |
| Corporate finance | 1,000 synthetic cases against an independent 60-digit Decimal permanent-profit-layer formulation, four ROIC=WACC growth-neutrality cases and an independently valued reverse target. |

## Run

Use Python 3.12 and the pinned packages in `verification/requirements.txt`.
Check out each repository in `sources.json` at its recorded commit under a
directory named for the repository, for example `portfolio-sources/treasury-alm`.
All files can be obtained from those public immutable commits. The seven
checkout steps in the workflow provide a complete, executable example.

```bash
python -m pip install -r verification/requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python verification/portfolio_controls.py \
  --sources portfolio-sources --manifest verification/sources.json \
  --output portfolio-controls-result.json
```

The harness verifies all 476 recorded Git blob identities before importing study
code. Any failed assertion produces a nonzero exit and a per-study failure in
the JSON output. Seeds and case families are fixed in the source.

The inventory module is loaded through its Python package, including its input
contracts. This supports both the original pinned study and the documented
22 October validation revision. The immutable manifest still describes its
original commits; omitting it requires recording the alternative source
identities separately and does not establish a match to that manifest.

[Workflow](../.github/workflows/portfolio-mathematics.yml) ·
[Recorded local result](../reports/portfolio_mathematical_controls_20261021.json)

## Interpretation

This is an independent-formulation implementation check, authored within the
project. It is not an external audit, new empirical evidence, model deployment
approval or a proof of optimal placement outcomes. The contact-allocation
optimality check applies only to the stated equal-cost/cap model; it does not
establish global optimality of the inventory heuristic. The pinned snapshots
predate later publication-status notes, which do not change scientific methods.
Historical raw-source, workbook-application and browser receipts retain their
own dates and execution scopes. These cases are separate from the unit-test
counts quoted in the study READMEs.
