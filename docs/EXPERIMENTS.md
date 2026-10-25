# Experiment lab

## Purpose and input contract

Analyze a predeclared, fixed-horizon, two-arm test with expected allocation 50:50. Upload a CSV or paste records with columns `participant_id,arm,converted,contribution`. Use one row per originally assigned eligible participant, including nonconverters. Arm must be `control` or `treatment`; converted must be 0 or 1; contribution is finite signed GBP after variable costs, incentives, refunds and allocated campaign costs. Duplicate/missing IDs and malformed values are rejected. Maximum 20,000 rows and 2 MB. At least 30 participants in each arm are required for this demonstration's large-sample calculation; this threshold does not guarantee accurate monetary intervals.

The public preview calculates in-browser and does not send CSV content to a server or save it in localStorage. Local mode posts records to the loopback Python API. The demonstration code does not retain participant records in its event database.

## Calculations

Primary outcome: difference in mean contribution per assigned participant, treatment minus control. Standard error is the square root of treatment sample variance / treatment n + control sample variance / control n. Report difference ± 1.959964 × standard error as a large-sample approximate 95% interval.

Secondary outcome: conversion-rate difference with an unpooled normal-approximation interval. Rare event/non-event counts below ten are flagged. Conversion is not a substitute for profitable contribution.

Sample-ratio mismatch: Pearson chi-squared statistic against a 50:50 expected split, one degree of freedom; two-sided imbalance tail computed via erfc(sqrt(chi-squared/2)). p < 0.01 flags an assignment investigation. Passing this check does not prove randomization validity.

Decision text first prioritizes a sample-ratio warning. Otherwise, an entirely positive contribution interval suggests positive evidence subject to guardrails, an entirely negative interval flags harm, and an interval crossing zero is inconclusive. This is an analytic aid, not an automatic launch decision.

## Explicitly synthetic example

`web/models/synthetic-experiment.csv` contains 8,000 simulated participants (4,000 per arm), generated with seed 42. It is prominently labelled synthetic in the app. There was no real campaign.

Control has 295 conversions (7.375%); treatment has 405 (10.125%). Secondary conversion difference is +2.75 percentage points, approximate interval [1.51, 3.99] pp. However contribution difference is only **£0.2291 per participant**, approximate interval **[−£0.0059, £0.4641]**, so the primary outcome is inconclusive. This is a deliberate example of conversion evidence not being sufficient to declare profitable growth.

## Operational limitations

Independent-participant, large-sample intervals are not suitable for all heavy-tailed monetary outcomes. There is no cluster adjustment, repeated-look/optional-stopping correction, multiplicity adjustment, missing-outcome correction, return-window enforcement or automatic guardrail validation. Obtain appropriate design and statistical review for a real campaign. Include original assignment rather than only reached/converting people, and resolve identity, consent, complete windows and cost definitions upstream.

## Reproduce

`python scripts/build_experiment_demo.py` regenerates the synthetic CSV. `experiments.py` provides the Python analyser; `web/ml-engine.js` provides the browser equivalent. CI checks the same reference contribution difference and interval decision in both environments.
