# AI/ML upgrade — measured evidence

All model metrics below are on historical November 2011 outcomes. No campaign was run and no retailer or recruitment outcome is claimed.

## Repurchase prediction

Training: March–August snapshots (15,063 rows). September selects between two fixed candidates. October fits a sigmoid probability calibrator. November is the final 30-day holdout (3,970 shoppers). Data after the feature cutoff never enter the features.

| Method | Average precision | ROC-AUC | Top-20% precision | Brier (lower better) |
| --- | ---: | ---: | ---: | ---: |
| Logistic regression (raw) | 0.63715 | 0.73669 | 67.76% | 0.18354 |
| Random forest (raw) | 0.63671 | 0.73559 | 67.76% | 0.18604 |
| Random forest + October calibration | 0.63671 | 0.73559 | 67.76% | 0.18702 |
| RFM rank | 0.60364 | 0.73046 | 63.35% | Not a probability model |
| Spend-only rank | 0.57705 | 0.70656 | 61.96% | Not a probability model |
| Training prevalence | 0.33678 | 0.50000 | 34.89% | 0.22805 |

The constant prevalence model's top-20% precision depends on arbitrary tie order and has no targeting interpretation. The app suppresses that tied ranking result.

Selected forest + October calibration AP improvement vs RFM: 0.03307; 500-resample paired shopper bootstrap interval [0.02212, 0.04404]. Conditional on the fixed model and one month, not independent retailer validation.

Calibration does not improve November Brier score. Logistic regression slightly exceeds the selected forest on final-month AP. Those mixed findings are retained rather than choosing a new model after looking at the test month.

## Novel product recommendation

September selects 32-factor SVD by mean recall@5; the factorization is refit on pre-November purchases. Reported population: 1,247 known shoppers who purchase at least one novel product during the following 30 days. All future novel targets count, including those outside the top-500 candidate catalog.

| Method | Hit-rate@5 | Mean recall@5 | Precision@5 | MRR@5 | Catalog coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| svd | 27.91% | 3.20% | 7.70% | 0.15094 | 72.2% |
| popularity | 14.43% | 1.06% | 3.46% | 0.07994 | 8.6% |

Low recall remains important: only 36.74% of novel target products fall in the candidate catalog. The browser's one/two-seed interaction differs from the full-history evaluation context. Offline recommendation improvements are not measured sales uplift.

## Experiment and retrieval capabilities

The experiment analyser processes CSV outcomes using contribution difference, approximate 95% intervals, conversion difference and 50:50 sample-ratio diagnostics. Its 8,000-participant synthetic example has positive conversion evidence but an inconclusive contribution interval. The evidence assistant retrieves existing passages from a fitted TF-IDF index with source links and abstention; it is not a generative language model.

Full definitions, mixed results and model limitations: [MODEL_CARD.md](../MODEL_CARD.md). Research: [UPGRADE_RESEARCH.md](../UPGRADE_RESEARCH.md).
