# BrandScope 2 — current AI/ML upgrade for the resume

This section supersedes the earlier version's feature and test counts. The rest of this document retains the complete business context and original descriptive analytics. Tailor the resume to P&G Brand Management; do not imply that more algorithms alone establish suitability or a hiring guarantee.

## New implemented capabilities

- **Supervised purchase propensity:** compared logistic regression and random forest using eight past-only behavioral features. Trained on six March–August 2011 snapshots (15,063 customer-date rows); September selects the candidate, October fits sigmoid calibration, November is the final 30-day report. No final-month tuning.
- **Explainable portable inference:** exported forest parameters and calibrator to JSON; Python and browser JavaScript execute the same model. Includes tree-path contributions, permutation importance, reliability bins, extrapolation warnings, feature-drift diagnostics and historical capacity planning. No SHAP or causal interpretation is claimed.
- **Product recommendation:** fitted 32-factor TruncatedSVD to a sparse purchase matrix, selected against rank-16 and popularity alternatives on September recall@5, then evaluated on November novel-product outcomes.
- **Evidence retrieval NLP:** fitted an English TF-IDF index over 80 factual/method passages, returning existing text with source links and abstaining for unsupported queries. This is not a generative LLM or foundation-model RAG implementation.
- **Experiment-results analyser:** accepts uploaded/pasted participant CSVs, rejects duplicates, computes contribution and conversion differences with approximate 95% intervals, and flags 50:50 sample-ratio mismatches. The example is explicitly synthetic; no real campaign was run.
- **Verification:** 50 Python tests plus executable Node checks compare browser inference with sklearn reference cases and validate recommendation, retrieval and experiment outputs. CI installs optional model-rebuild libraries and checks feature-time boundaries.

## Verified new results

On the same November holdout of **3,970 shoppers**, the selected forest has **average precision 0.6367**, **ROC-AUC 0.7356**, and **67.76% precision in the top 20%**, compared with **RFM AP 0.6036 / top-20% precision 63.35%** and **spend-only AP 0.5770**. Paired customer bootstrap AP difference vs RFM is **0.0331**, percentile interval **[0.0221, 0.0440]**, 500 replicates. This conditions on one fixed model and one historical month; it is not causal lift or a future-performance guarantee.

Keep mixed results explicit: logistic regression slightly exceeds the selected forest on final-month AP and Brier. October calibration worsens November Brier from **0.1860 to 0.1870**. Do not claim consistently superior probability calibration or production accuracy.

Recommendation **hit-rate@5 is 27.91% vs 14.43% popularity**, **mean recall@5 3.20% vs 1.06%**, and catalog coverage **72.2% vs 8.6%**. Evaluation covers **1,247 known shoppers with a novel future purchase**, not all shoppers. Only 36.74% of future novel targets are inside the top-500 candidate catalog. The browser uses one/two seed products, whereas offline evaluation uses full weighted histories; do not equate those contexts or call these metrics sales uplift.

The 8,000-participant synthetic experiment has a positive secondary conversion difference of **2.75 pp**, but its primary contribution difference of **£0.229 per participant** has an approximate interval **[−£0.006, £0.464]**. The tool correctly reports inconclusive contribution rather than declaring a campaign win. Synthetic results are demonstration outputs, not personal business achievements.

## Updated resume bullet options

Choose 2–3, prioritize business relevance, and use only claims the applicant can explain:

1. Built a brand growth workspace on **541,909 retail transaction rows**, connecting shopper segmentation, predictive purchase ranking, product discovery and campaign contribution analysis to testable marketing decisions.
2. Benchmarked logistic regression and random forest with separate temporal selection, calibration and holdout periods; achieved **67.8% top-quintile repurchase precision versus 63.4% for RFM** across **3,970 November holdout shoppers**.
3. Developed a **32-factor SVD recommendation model**, achieving **27.9% historical hit-rate@5 versus 14.4% for popularity** among eligible novel-product purchasers, with recall and catalog-coverage limitations documented.
4. Implemented a source-linked **TF-IDF evidence assistant** and a CSV-based experiment analyser that evaluates contribution uncertainty and assignment imbalance, supported by **50 automated tests** and Python/browser inference parity checks.

## Additional supported keywords

Supervised machine learning; purchase propensity; random forest; logistic regression; temporal validation; probability calibration; model evaluation; average precision; explainable model inspection; permutation importance; bootstrap uncertainty; collaborative filtering; matrix factorization; TruncatedSVD; recommendation evaluation; NLP; TF-IDF; evidence retrieval; experiment analysis; sample-ratio mismatch; confidence intervals; commercial decision support; model governance; data quality; consumer-first analytics.

These extend the marketing keywords below. Do not claim deep learning, generative AI, an LLM integration, causal uplift modeling, marketing mix modeling, randomized fieldwork, real P&G data or Swedish business proficiency. Public P&G LinkedIn posts and portfolio examples were reviewed for positioning; no one was messaged, no private account was accessed and no third-party code/metrics were copied.

Model card: https://github.com/Pavan-amikula/brandscope/blob/main/docs/MODEL_CARD.md
New results: https://github.com/Pavan-amikula/brandscope/blob/main/docs/outputs/ML_RESULTS.md
Research: https://github.com/Pavan-amikula/brandscope/blob/main/docs/UPGRADE_RESEARCH.md

---

# BrandScope — complete project context for resume writing

## Instructions for the resume-writing conversation

Use this as factual project context. Tailor wording to the supplied P&G Brand Management Summer Internship 2027 role in Stockholm. Keep the distinction between measured historical analytics, implemented software and assumed future campaign outcomes. Do not invent employment, consumer research, stakeholder collaboration, Swedish fluency, business results, team leadership or real P&G access. Personal education, language proficiency and availability must come from the applicant. Do not infer them from the project.

Applicant: **Amikula Pavan Kumar Goud**. GitHub: **Pavan-amikula**.

Project: **BrandScope — Shopper Insights & Profitable Growth Workspace**.

Repository: https://github.com/Pavan-amikula/brandscope

Interactive static preview: https://pavan-amikula.github.io/brandscope/

Video: https://github.com/Pavan-amikula/brandscope/raw/refs/heads/main/docs/assets/brandscope-demo.mp4

Type: independent portfolio project, October 2026. It is not a P&G internship, client engagement or commercial deployment.

## Project description — ready to reuse

BrandScope is a working brand management decision workspace that turns historical retail transaction data into shopper segments, retention insights, product-pairing hypotheses and testable marketing plans. It combines a reproducible Python analytics pipeline with an original responsive web interface, a campaign contribution simulator, an exportable decision brief and a near-real-time SQLite-backed event ingestion API. It is designed around the marketing decisions emphasized in the P&G Stockholm Brand Management internship: understanding consumers, shoppers and customers; identifying marketing tactics; planning profitable growth; analyzing evidence; and communicating recommendations clearly.

The project uses the full UCI Online Retail dataset, with 541,909 historical transaction rows from a UK gift retailer. A documented audit removes exact duplicates and scoped invalid/non-merchandise records while retaining negative merchandise transactions as recorded returns. Sales include records without customer IDs; customer-level analysis excludes those records. Currency calculations use integer pence before presentation in GBP. Sweden and Nordic filters show the actual relevant export orders without relabelling the dataset as Swedish FMCG data.

The original analytics workflow remains alongside four new intelligent workspaces. Growth overview shows reconciled sales and opportunities. Shopper intelligence provides explainable RFM segmentation, cohort retention, product search and basket associations. Campaign studio models incremental contribution, discounts paid on baseline purchases, break-even conversion gain and approximate conversion test sample size; it saves scenarios and exports a complete Markdown brief. Activation monitor accepts validated HTTP events, deduplicates event IDs, stores records in SQLite and updates through two-second polling. Evidence & methods shows source lineage, cleaning checks, historical ranking evaluation and research references.

The app runs locally with Python's standard library and no API keys. The hosted GitHub Pages preview uses committed aggregate data and browser storage for demo events/scenarios; it does not host the Python API. It is explicit about that distinction. Demo events carry a synthetic flag and are isolated from historical analytics.

## Verified metrics and how to phrase them

| Fact | Value | Correct interpretation |
| --- | --- | --- |
| Source rows processed | 541,909 | Dataset scale processed, not users served |
| Merchandise rows retained | 530,784 | Audited cleaning output |
| Exact duplicates removed | 5,268 | Chosen duplicate policy; no unique source line ID |
| Other scoped exclusions | 5,857 | Invalid/non-merchandise rows after deduplication |
| Purchase invoices analyzed | 19,771 | Historical positive purchase orders |
| Identified shoppers analyzed | 4,334 | Historical customer accounts, including wholesalers |
| Historical net merchandise sales | £9,754,656.49 | Revenue in the dataset, not revenue generated by the project |
| Mutually exclusive shopper segments | 5 | Transparent RFM business rules, not ML clusters |
| Historical ranking checks | 3 | Cutoffs 1 Aug, 1 Sep, 1 Oct 2011; future 30-day purchase label |
| RFM precision in top 20% | 55.80%, 59.37%, 51.11% | Future repurchase concentration in historical holdouts |
| Overall repurchase rate | 23.75%, 28.97%, 26.99% | Expected random-targeting baseline for those eligible populations |
| RFM ranking lift | 2.35×, 2.05×, 1.89× | Precision / overall repurchase rate; not campaign uplift |
| Spend-only precision | 51.35%, 56.95%, 50.42% | An explicit alternative baseline |
| High-value inactive shoppers | 96 | A hypothesis-generating group under stated thresholds |
| Their historical gross purchases | About £428k | Past spend, not recoverable revenue or CLV |
| Automated tests | 50 passing | Commercial math, data reconciliations and HTTP/SQLite integration |
| Event update interval | 2 seconds | Near-real-time polling, not a WebSocket latency benchmark |

The RFM ranking is the mean of percentile frequency, percentile gross monetary spend and inverse percentile recency. Features are computed only before each cutoff. The top 20% are then evaluated for repurchase within the following 30 days. No model was tuned, and no causal or statistical significance claim is made. The same customers can appear across checks, so these are not independent field experiments.

## Commercial reasoning demonstrated

Under one explicitly assumed scenario—2,000 eligible shoppers, 5% baseline conversion, a 3 percentage-point gain, £45 pre-discount order value, 45% contribution margin, 5% discount on all treatment purchases, £600 campaign cost—the modelled incremental contribution is **£255**. Raising only the discount to 20% changes it to **−£825**. The approximate conversion sample requirement is **1,059 per arm**, exceeding the 2,000-person total audience. These calculations demonstrate a decision to redesign or gather evidence before scaling; they are not realized campaign outcomes. A monetary primary outcome requires a separate power design based on observed variance.

The 2,000-person planning audience is independent of the observed 96-person at-risk group. It must not be described as an observed audience from that segment.

## Business deliverables

- Executive growth dashboard with four markets and full/90-day windows.
- Auditable consumer/shopper/customer evidence distinctions.
- Five RFM segments with marketing hypotheses and explicit precedence rules.
- Retention cohort heatmap with unobserved future cells and partial-month caveats.
- Directional co-purchase rules with support, confidence, lift and minimum basket counts.
- Marketing strategy brief covering audience, proposition, product, price, place, promotion, measurement and scale/stop decisions.
- Campaign economics and conversion-sample planning workspace.
- Downloadable decision brief and saved scenarios.
- Functional local event ingestion and monitor, plus static preview fallback.
- English stakeholder summary, Swedish draft and proposed 10-week action plan.
- README, captioned demonstration, screenshots, CSV outputs and CI workflows.

## Technology

Python, pandas, SQLite, SQL, standard-library HTTP server, HTML, CSS, vanilla JavaScript, SVG charts, REST-style JSON endpoints, Git, GitHub Actions, GitHub Pages. openpyxl reads the original workbook. The application runtime executes committed model contracts without third-party packages. Model rebuilding and the full feature-construction tests use pandas, numpy, scipy and scikit-learn; openpyxl reads the source workbook.

Do not add React, Power BI, Tableau, FastAPI, WebSockets, cloud databases, causal ML, marketing mix modeling or production authentication as implemented technologies. The Microsoft Power BI example was a design reference only.

## Research grounding

The source data is Chen (2015), UCI Online Retail, CC BY 4.0, DOI 10.24432/C5BW33. Chen, Sain & Guo (2012) informed customer-centric RFM reasoning; this project does not reproduce its clustering model. Wan et al. (2022), “Fast RFM Model for Customer Segmentation,” was reviewed through the ACM side-panel article abstract for RFM pattern context; its efficient algorithm is not implemented here. Kohavi, Henne & Sommerfield (ACM KDD 2007) informed controlled-test design and causal boundaries. Comparable public GitHub projects were reviewed for analytics structure, and Microsoft's retail sample informed KPI hierarchy. No third-party code or paper text is copied into the project.

## Role-relevant keywords supported by the project

Brand management; marketing strategy; shopper insights; customer analytics; consumer-centric marketing; market segmentation; RFM analysis; cohort retention; customer relationship management; marketing tactics; campaign planning; profitable growth; contribution margin; commercial acumen; break-even analysis; experiment design; A/B test planning; analytical capability; data-driven decision-making; KPI reporting; executive communication; data visualization; project ownership; reproducible analytics; retail analytics; cross-sell hypotheses; localization workflow.

Use “consumer insights” carefully: the project distinguishes a consumer-insight hypothesis from observed shopper behavior. “Cross-functional” describes the prospective work plan, not meetings or teamwork that already happened. Use leadership keywords only with the applicant's actual examples.

## Resume bullet options

Choose two or three, then adapt to the applicant's own understanding and verified contributions:

1. Built a brand growth decision workspace analyzing **541,909 retail transaction rows** across **19,771 purchase orders and 4,334 identified shoppers**, translating RFM segments, retention cohorts and basket evidence into testable marketing hypotheses.
2. Evaluated past-only RFM ranking across **three 30-day historical holdouts**, identifying repeat purchasers at **1.89–2.35× the overall repurchase rate** while comparing against a spend-only baseline.
3. Developed a campaign contribution planner incorporating baseline discount cannibalization, break-even conversion and sample-size checks, with exportable decision briefs and explicit scale/stop criteria.
4. Implemented a **SQLite-backed event ingestion API** with schema validation, idempotent order IDs and **two-second dashboard polling**, supported by **50 automated checks** and GitHub Actions.

For a marketing application, lead with bullets 1 and 3. Keep technical details secondary unless the role rewards them. Do not say “increased retention by 135%,” “generated £9.75m revenue,” “delivered £255 profit,” or “optimized P&G's campaign”; none was measured.

## Interview explanation — 60 seconds

“I built BrandScope to connect shopper analysis to a marketing decision. I started with a public retail dataset and audited the full 541,909 rows rather than relying on a cleaned sample. I used RFM segments and retention cohorts to identify audiences worth investigating, then evaluated a simple ranking on future purchases using only past features. The top-ranked group had about 1.9 to 2.35 times the overall repurchase rate, although that does not prove a campaign would change behavior. The commercial studio then asks whether a proposed action could create contribution after incentives and campaign cost. A key learning was that a campaign can look promising on conversion but become unprofitable after discounting—or be too small to test reliably. I would validate consumer needs, consent, wholesale status and Swedish market fit before any real activation.”

## Interview questions to prepare

1. Why keep missing-ID sales in total sales but remove them from RFM?
2. Why is the Swedish subset not a Swedish market study?
3. What makes ranking lift different from incremental conversion?
4. Why do discounts on baseline purchases affect profitability?
5. Why does the default positive scenario still fail its conversion sample check?
6. How would you power the monetary primary outcome?
7. What data would you need to connect this to an actual P&G brand and retailer?
8. How would you distinguish shoppers, product users and retail customers?
9. Why might wholesale accounts distort segments, averages and basket rules?
10. What would you do differently after talking to consumers and retailer partners?

## Mandatory boundaries for the resume

No guarantee of recruitment. No invented business impact. No claim of P&G employment or collaboration. No claim of completed consumer interviews, campaigns or stakeholder sessions. No invented Swedish/English proficiency, graduation date, work authorization, relocation readiness or availability. Use real personal details provided separately. BrandScope is a completed independent software and analysis project with a prospective business activation plan.
