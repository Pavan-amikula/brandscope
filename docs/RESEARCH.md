# Research and implementation decisions

Research reviewed on 25 October 2026. The open ACM Digital Library tab was used to search “RFM customer segmentation” and inspect the article page for **Fast RFM Model for Customer Segmentation**. The BTH library tab was not used to claim institutional access. No paywall was bypassed and no papers are redistributed.

| Source | What was reviewed | Decision in BrandScope | Boundary |
| --- | --- | --- | --- |
| [Chen (2015), Online Retail, UCI](https://doi.org/10.24432/C5BW33) | Dataset description, variable definitions, source workbook and CC BY 4.0 license | Rebuild analytics from all 541,909 source rows; preserve returns and missing-ID sales | A 2010–2011 UK gift retailer with wholesale buyers; not current Swedish FMCG data |
| [Chen, Sain & Guo (2012), Data mining for the online retail industry](https://doi.org/10.1057/dbm.2012.17) | Author-copy abstract and source dataset's introductory-paper reference | RFM behavior translated into marketing audiences and actions | Paper uses clustering and decision trees; this implementation deliberately uses explainable rules, not a reproduction |
| [Wan, Chen, Qi, Gan & Tang (2022), Fast RFM Model for Customer Segmentation](https://dl.acm.org/doi/10.1145/3487553.3524707) | ACM article metadata and abstract in the user's open side-panel browser | Reinforced separating recency, frequency and monetary thresholds and documenting the rules | The paper proposes efficient RFM pattern mining. BrandScope does not implement or benchmark its compact-list/pruning algorithm |
| [Kohavi, Henne & Sommerfield (2007), Practical Guide to Controlled Experiments on the Web, ACM KDD](https://exp-platform.com/practical-guide/) | Author-hosted practical guide and abstract | Randomized control, explicit outcome window, power check and no causal claim from observational history | Actual campaign evaluation still needs assignment, exposure, consent and outcomes |
| [Microsoft Retail Analysis sample](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-retail-analysis) | Retail dashboard tour and example information hierarchy | KPI → trend → segment → decision flow | No copied Power BI assets or implied Power BI implementation |
| [akmalariq/ecommerce-data-analysis](https://github.com/akmalariq/ecommerce-data-analysis) | Public project structure and README | Reproducible pipeline and clear cleaning/scoring definitions | No copied source code; its cleaning policy differs, so headline totals need not match |
| [Mohamed-gaal/online-retail-customer-analytics-dashboard](https://github.com/Mohamed-gaal/online-retail-customer-analytics-dashboard) | Public README feature and workflow descriptions | Compared expected sales, products, cohorts and data-quality views | BrandScope adds contribution economics, campaign briefs, and a durable event API; no performance claim versus that project |

## Why this approach fits a brand management role

The role centers on translating consumer, shopper and customer understanding into marketing choices and profitable growth. The technical implementation is a means to support that decision. It deliberately avoids an unnecessary “AI predicts everything” claim. Transaction data provides shopper evidence; it cannot reveal consumer motivations or retailer negotiation constraints.

No freely available source reviewed here supplies authentic P&G brand-level Swedish sales, media exposure and margin data together. Using historical retail data with clearly declared limitations is more defensible than manufacturing those fields. The Swedish subset contains eight identified customers and 34 purchase invoices; use it to test localization and filtering, not estimate Swedish market size or campaign performance.

## Design references translated into an original interface

An editorial serif headline, warm paper background, burgundy decision panels, restrained tables and quiet status indicators distinguish the workspace from a generic SaaS template. Microsoft’s retail hierarchy informed the progression, while comparable GitHub projects helped define the baseline analytics expected in a reproducible portfolio. Every screen focuses on a brand manager's next decision. Optional Google Fonts enhance presentation; system fallbacks work without font access.

## Further work requiring new evidence

1. Consumer research: consented interviews about needs, category entry points and barriers. Do not invent quotes or personas.
2. Retailer research: authorized sell-out, distribution, availability and promotional calendar data.
3. Brand strategy: real category/brand mapping and legal approval for claims and creative.
4. Incrementality: randomized assignment and margin outcomes; pilot profit variance before powering the primary outcome.
5. External validation: evaluate on another authorized retailer and recent time period before operational use.
