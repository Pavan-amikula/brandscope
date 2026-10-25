# Data and metric dictionary

## Cleaning and audit

1. Download the original UCI Online Retail ZIP and record SHA-256.
2. Read the entire workbook without sampling.
3. Drop exact duplicated rows across all original columns (5,268).
4. Keep merchandise codes matching five digits plus an optional letter, nonmissing description, strictly positive unit price and nonzero quantity. This removes 5,857 rows after deduplication, including non-merchandise charges/adjustments and invalid rows. This is a declared scope filter, not a universal retail cleaning rule.
5. Convert unit price to integer pence with round-to-nearest; multiply by quantity. Positive and negative merchandise quantities are retained (522,121 positive, 8,663 negative).
6. Preserve missing customer IDs in sales totals (131,424 retained rows); omit them from customer analytics.

Audit identity: **541,909 = 5,268 + 5,857 + 530,784**. Duplicate removal assumes identical repeated records are accidental duplicates; the dataset lacks a unique line ID, so that choice could remove legitimate identical line items. Negative merchandise rows are treated as recorded returns, not audited physical returns. Invoice cancellation flags and negative quantities are not independently reconciled to original orders. Outliers are retained; unusually large wholesale orders can dominate averages.

## Metrics

| Metric | Definition | Caution |
| --- | --- | --- |
| Gross merchandise sales | Sum(price × quantity) where quantity > 0 after cleaning | Includes identified and anonymous purchases; excludes scoped-out charges |
| Recorded returns | Absolute negative sum(price × quantity) where quantity < 0 | Date of return record, no original-sale matching |
| Net merchandise sales | Gross sales − recorded returns | Not company revenue under audited accounting policy; no tax/cost assumptions |
| Purchase orders | Distinct InvoiceNo among positive merchandise purchases | Not order lines; returns do not increase purchase order count |
| Average order value | Gross merchandise sales / purchase orders | Wholesale influence; GBP only |
| Identified shoppers | Unique nonmissing CustomerID among positive purchases | Purchasers/accounts, not necessarily individual consumers |
| Repeat shopper rate | Identified shoppers with 2+ purchase invoices / all identified shoppers | Within selected window, not a retention probability |
| Monetary RFM value | Gross positive purchase value for an identified shopper | Returns do not reduce the RFM monetary feature |
| Recency | Days between analysis reference date and last purchase | Reference is 10 Dec 2011, not current date |
| Frequency | Distinct positive purchase invoices per identified shopper | Within selected window |

## Segment precedence

Apply these rules in order so segments are mutually exclusive:

1. Champions: recency ≤ 30 days and frequency ≥ 3.
2. At risk · high value: recency > 90 days and monetary ≥ the 75th percentile within selected market/window.
3. Loyal shoppers: recency ≤ 90 and frequency ≥ 2.
4. New shoppers: recency ≤ 30 and frequency = 1.
5. Reactivation pool: all remaining identified shoppers. This label can include recent moderate-frequency shoppers as well as inactive shoppers; review row-level eligibility before activation.

These are business rules, not learned clusters or calibrated churn scores. Market/window selection recomputes segment membership and high-value thresholds. The last-90-days view cannot observe earlier purchases, so “new” means new within that window and cohort acquisition may be left-truncated.

## Cohorts and baskets

First observed purchase month in selected data defines cohort. M0 is 100%; Mk is unique purchasing shoppers at calendar month k / cohort size. Future months are null; incomplete observed months remain observed and can depress retention. No censoring correction is applied.

Product pairs are counted once per invoice among the 35 most frequently ordered products. The support denominator is all positive purchase invoices in the selected market/window, including invoices containing none of those top products. Joint-basket minimum = five. Both directions are considered; report the eight highest association-lift rules. Support = joint baskets / all purchase orders; confidence A→B = joint baskets / baskets containing A; association lift = joint baskets × all purchase orders / (baskets containing A × baskets containing B). No Apriori efficiency claim, no hypothesis-testing correction and no causal interpretation.

## Historical evaluation

At 1 Aug, 1 Sep and 1 Oct 2011, compute customer features strictly before the cutoff. Rank by mean(percentile frequency, percentile monetary, 1 − percentile recency); resolve ties by CustomerID. Select floor(20% × eligible) customers. Label whether each purchased in the following 30 days. Compare precision to the overall repurchase prevalence and the top-20% monetary-only ranker. Features never include post-cutoff records. Cleaning happens before splitting; exact duplicate removal uses all source rows but does not tune features or labels.

The same customers can appear across windows. There are only three descriptive checks, without confidence intervals or an external dataset. No threshold was optimized using these results, but future performance and causal response remain unestablished. “Ranking lift” is precision / overall repurchase rate; it is not incremental conversion, profit uplift, model accuracy, or a randomized treatment effect.

## Campaign economics

All inputs are assumptions. Let N = rollout audience, b = baseline conversion, l = absolute conversion gain, A = pre-discount order value, m = contribution margin before discount, d = discount fraction on all treatment orders, C = additional campaign cost.

Baseline contribution = N b A m. Campaign contribution = N (b+l) A (m−d) − C. Their difference = N A [l m − (b+l)d] − C.

Break-even l = [C + N A b d] / [N A(m−d)] when denominator > 0. No finite positive break-even is shown when margin ≤ discount. Inputs must satisfy b+l ≤ 1. Break-even above the feasible conversion gain should also be treated as commercially unattainable.

Conversion sample size uses an equal-arm, two-proportion normal approximation with 80% power and two-sided alpha .05. It is a planning approximation; extreme rates/small samples, clustering, attrition and repeated testing require a different design. It **does not power contribution**, whose variance is unavailable. No test results or significance claims are fabricated.

## Runtime boundary

The static app uses bundled aggregate JSON and browser localStorage for simulated events/scenarios. The Python app uses SQLite for actual HTTP ingestion and scenario persistence. The monitor polls every two seconds; it is near-real-time polling, not an SSE/WebSocket implementation. Events carry explicit synthetic flags and never mutate historical analyses. The server is a loopback demonstration service, not a production multi-user system.
