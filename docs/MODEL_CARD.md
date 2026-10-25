# BrandScope 2 — model and data label

Independent portfolio research using one licensed historical retailer. No P&G systems, current Swedish FMCG sales, consumer interviews, advertising exposures or randomized treatment labels are present. Predictions do not establish the effect of marketing or guarantee a hiring outcome.

## Intended decisions

1. **Repurchase model:** demonstrate prioritization of likely purchasers, compare with simpler rankers, and make prediction uncertainty visible.
2. **Product discovery:** rank novel product candidates using learned co-purchase factors and compare with broad popularity.
3. **Evidence assistant:** retrieve project source passages without inventing an answer.
4. **Experiment lab:** analyze supplied fixed-horizon randomized outcomes; this is statistical tooling, not an ML treatment-effect model.

These are assistive case-study capabilities, not approved automated customer activation or production models.

## Data and privacy boundary

The original UCI Online Retail data contains 541,909 transaction rows from a UK gift retailer, 1 December 2010 through 9 December 2011. The declared cleaning pipeline retains 530,784 merchandise rows, including recorded returns. Model features and product factors use positive purchases with known customer IDs. No row-level customer identities, contact details, raw source workbook or local SQLite database are published. Exported model trees contain only aggregate probabilities and thresholds; parity examples contain behavior features without identifiers.

Scope filters and deduplication are applied before temporal snapshots. No feature or label threshold is optimized on November. Exact duplicate removal assumes identical repeated lines are accidental duplicates; lack of unique source line IDs remains a limitation.

## Supervised repurchase model

**Target:** at least one positive purchase in the 30 days following a snapshot. This is purchase propensity, not explicit churn, offer responsiveness, customer lifetime value, contribution margin or causal uplift.

**Eligible population:** identified shoppers with at least one positive purchase before the cutoff. A shopper can recur across monthly snapshots, matching repeated scoring of existing accounts; this is temporal evaluation, not customer-disjoint evaluation. Wholesale accounts are not separately identified.

**Features:** days since last purchase; all-history distinct purchase orders; all-history gross positive spend in GBP; days since first purchase; orders in the trailing 30 days; gross spend in the trailing 30 days; distinct products; average order value. Every feature is calculated strictly before its snapshot. No customer identifier, country, future outcome, treatment, or post-cutoff transaction is an input. All features use log(1+x). Logistic regression additionally uses scaling fitted only on training rows.

**Training protocol fixed before final reporting:**

| Role | Cutoffs / observations |
| --- | --- |
| Training | 1 Mar, 1 Apr, 1 May, 1 Jun, 1 Jul, 1 Aug 2011; 15,063 customer-snapshot rows |
| Model selection | 1 Sep 2011, subsequent 30-day label |
| Probability calibration | 1 Oct 2011, subsequent 30-day label |
| Final report | 1 Nov 2011, purchases through 30 Nov; 3,970 eligible shoppers |

Two fixed candidates are compared: logistic regression (C=1, scaled log features) and random forest (120 trees, max depth 7, min leaf 30, 80% feature subsampling). All random seeds are 42. Selection maximizes September average precision, with Brier score as a tie-break. The forest wins narrowly in September (0.59644 vs 0.59478). October fits a sigmoid calibrator to the frozen forest's logit probabilities. The training model is not refitted with calibration/test outcomes.

### Final November results

| Method | Average precision | ROC-AUC | Top-20% precision | Brier score |
| --- | ---: | ---: | ---: | ---: |
| Logistic regression, raw | 0.63715 | 0.73669 | 67.76% | 0.18354 |
| Selected random forest, raw | 0.63671 | 0.73559 | 67.76% | 0.18604 |
| Selected forest + October sigmoid | 0.63671 | 0.73559 | 67.76% | 0.18702 |
| RFM rank | 0.60364 | 0.73046 | 63.35% | Not a probability model |
| Spend-only rank | 0.57705 | 0.70656 | 61.96% | Not a probability model |
| Training prevalence | 0.33678 | 0.50000 | Tie-order artifact; not a targeting result | 0.22805 |

Top 20% contains 794 shoppers. The calibrated forest captures 40.24% of future purchasing shoppers. Average precision is a ranking summary, not classification accuracy. ROC-AUC measures discrimination; top-20% precision is not incremental response.

**Mixed evidence is retained:** logistic regression slightly outperforms the forest on November AP and Brier even though the forest won September selection. Calibration worsens November Brier from 0.18604 to 0.18702 while slightly improving log loss. The app retains the earlier-selected protocol and discloses these results. “Calibration fitted” must not become “well-calibrated production probabilities.”

A paired customer bootstrap (500 replicates, seed 42) gives an AP difference versus RFM of **0.03307**, percentile 95% interval **[0.02212, 0.04404]**. This interval conditions on the fixed fitted model and one test month. It does not account for training uncertainty, longitudinal dependence, model search, retailer variation or future time shifts.

### Inspection and monitoring

The app shows fixed-seed permutation AP drops on the final holdout and raw forest tree-path probability contributions for a supplied profile. Path contributions decompose changes from each tree's root probability to its leaf before calibration. They are not SHAP values, calibrated probability changes, or causal effects. Correlated inputs complicate both permutation and path interpretation.

Reliability bins compare mean probability to actual repurchase in November. Coarse population stability indices compare October and November feature distributions. No automatically validated alarm thresholds are claimed. The profile form flags features outside training min/max ranges, but in-range inputs can still be unrepresentative or internally inconsistent.

Capacity tables compare sums of predictions with observed purchasers at fixed audience fractions. They are historical prioritization diagnostics, not expected offer-induced conversions or permission to spend.

## Product factors and recommendations

Fit a user-product sparse matrix of log(1 + distinct purchase invoices per pair), using each training period's top 500 products by invoice count. TruncatedSVD learns product factors without centering the sparse matrix. Compare ranks 16 and 32 with popularity on September mean recall@5 (hit-rate tie-break); 32-factor SVD wins. Refit the chosen factorization on purchases strictly before 1 Nov 2011 and evaluate subsequent 30-day novel purchases. Its fit uses no November outcomes.

**Evaluation population:** 1,247 known shoppers who purchase at least one previously unbought product in the November window. The model ranks catalog candidates excluding all their prior products. Novel products outside the fitted catalog remain in the denominator and count as misses. Thus this is not an unconditional conversion or recommendation success rate across all shoppers.

| Final November metric | SVD | Popularity |
| --- | ---: | ---: |
| Hit-rate@5 | 27.91% | 14.43% |
| Mean recall@5 | 3.20% | 1.06% |
| Precision@5 | 7.70% | 3.46% |
| MRR@5 | 0.15094 | 0.07994 |
| Recommended catalog coverage | 72.2% | 8.6% |

Only 36.74% of novel target products fall in the top-500 candidate catalog. Low recall and this coverage gap remain visible. Scores are latent ranking scores, not probabilities or sales effects.

**Interactive inference boundary:** the browser takes one or two supplied seed products and sums their product vectors to rank candidates. Offline evaluation uses each shopper's full weighted history. This difference means the reported holdout metrics must not be advertised as measured performance of the two-seed interaction. Popularity is displayed as a cold-start fallback; unknown codes are rejected. No product availability, customer need or suitability is inferred.

## Evidence retrieval NLP

A fitted English TF-IDF index contains curated factual passages and paragraphs from the project’s methods, strategy, model card and experiment documentation. Query vectors and stored passage vectors use cosine similarity. The assistant returns existing passages with source links and abstains below a declared similarity threshold. It does not call an LLM, generate explanations, access the user's LinkedIn account, browse live sources or send queries to an external provider.

Similarity is not confidence in correctness. Retrieval can return a related but unhelpful passage. The checked example questions are smoke tests, not an independently annotated retrieval benchmark. Multilingual understanding is not claimed. No “RAG with an LLM,” semantic foundation-model embedding or generative AI claim should be made.

## Portable inference and reproducibility

The committed JSON contract contains the fitted forest or logistic parameters, sigmoid calibrator, feature ranges, product factors and TF-IDF index. Python and browser JavaScript execute the same contract. Reference cases compare exported predictions to sklearn with tolerance 1e-7. CI executes actual browser-engine code in Node and the Python HTTP integration tests. No pickle/joblib artifact is deserialized in the app.

Rebuild with `python scripts/build_data.py`, `python scripts/train_models.py`, `python scripts/train_recommender.py`, `python scripts/build_experiment_demo.py`, and `python scripts/build_knowledge.py` after installing requirements-ml.txt. The source ZIP fingerprint is attached to the supervised benchmark; model-file SHA-256 is recorded in docs/outputs/ml-benchmark.json.

## Why no uplift or marketing-mix model is claimed

Purchase logs lack randomized offer assignment, exposure, media spend and observed margins. Adding invented columns would not establish a causal treatment effect. EconML and Meta Robyn are research references for a future authorized dataset, not installed/implemented methods in BrandScope. The experiment analyser supplies the next evidence step without manufacturing a campaign result.

## Research sources

- [Scikit-learn probability calibration](https://scikit-learn.org/1.7/modules/calibration.html)
- [Scikit-learn TruncatedSVD](https://scikit-learn.org/1.7/modules/generated/sklearn.decomposition.TruncatedSVD.html)
- [Scikit-learn permutation feature importance](https://scikit-learn.org/1.7/modules/permutation_importance.html)
- [Recommenders project](https://github.com/recommenders-team/recommenders)
- [EconML](https://github.com/py-why/EconML)
- [Meta Robyn](https://github.com/facebookexperimental/Robyn)
