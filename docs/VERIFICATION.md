# Verification record

Verified locally on 25 October 2026. GitHub Actions verification is separately visible in the repository's Actions tab.

## Automated checks

`python -m unittest discover -s tests -v`: **50 tests passed** on Windows / Python 3.13. Runtime approximately 3 seconds on the development machine; this is not a performance benchmark.

- Contribution matches an independently computed treatment/control ledger.
- Zero-lift discounts still reduce baseline contribution.
- Break-even conversion gain solves the contribution equation.
- Unsupported margins, zero spend and invalid/nonfinite inputs are handled.
- RFM segment precedence and boundaries are checked.
- All eight market/window combinations reconcile net sales, monthly gross sales, identified sales and shopper segment totals.
- Source row counts reconcile and positive/negative row counts balance.
- Swedish subset and holdout ranking sizes/probability bounds match the snapshot.
- Local HTTP service reports readiness.
- Event validation rejects invalid events.
- Duplicate order IDs persist only once in SQLite.
- Cross-origin writes are rejected.
- Campaign calculation works through the HTTP API.
- Scenarios save and can be read back through the API.

`node --check web/app.js`: **passed**.

The SQLite connection context closes connections explicitly after transaction completion, including on exception. This resolved a Windows file-lock failure observed during initial integration-test cleanup.

## Browser verification

Exercised the actual application in the in-app browser:

| Action | Observed result |
| --- | --- |
| Load Growth overview | 19,771 purchase orders, 4,334 identified shoppers, £9.75m net sales |
| Select Sweden | 34 purchase orders, eight identified shoppers, £35.2k displayed net sales; scope caveat visible |
| Change to last 90 days | Segments and repeat rate update; scope truncation caveat included |
| Search products for WHITE | Product table narrows to matching product |
| Open Campaign studio | £255 modelled contribution and 1,059 sample per arm; audience insufficiency shown |
| Raise discount to 20% | −£825 modelled contribution |
| Save a scenario | SQLite save succeeds; saved count/name displayed |
| Export decision brief | Markdown file downloads; copied into docs/EXPORTED_DECISION_BRIEF.md |
| Send demo order | Event stored and displayed as SYNTHETIC |
| Start and pause demo stream | Repeated API events arrive and persist; stream paused after verification |
| Restart local service | Previously saved plan/events remain available |
| Open evidence | Audit, three ranking holdouts and source references render |
| Narrow responsive layout | 375 CSS-pixel content width; document scrollWidth 375 (no page-wide horizontal overflow) |
| Desktop responsive layout | 1,425 CSS-pixel content width; document scrollWidth 1,425 |

No console warnings/errors were present in the inspected local application log. These checks do not constitute a formal accessibility audit, cross-browser certification, load test or production security assessment.

## Media verification

The MP4 uses actual captured application states with captions and slow pans. It is a screenshot-based walkthrough, not a continuous recording. Generated event amounts are synthetic and labelled. The encoding is H.264, yuv420p, 1,280 × 800 at 12 frames/second. The GIF provides an inline README preview. Screenshots cover desktop, mobile, Sweden, shoppers, campaign assumptions and evidence.

## Reproducibility boundary

The original source ZIP fingerprint is recorded in results.json. The pipeline was run on all rows. Row-level source/database files are local only and ignored by Git; aggregate data, metric outputs and rebuild source are committed. The default project does not need a database download to run. Rebuilding requires network access and pandas/openpyxl. Test input databases are isolated temporary files.

## Remaining limitations

The hosted preview is static with browser persistence. The real ingestion API runs locally. There is no production login, advertising connector, customer contact delivery, live retailer feed or completed field experiment. Consumer research, current FMCG data and business-language proficiency are not inferred.


## Version 2 AI/ML verification

Full Python run: 50 passing tests with optional ML libraries installed. Node executes web/ml-engine.js against 12 sklearn reference profiles at tolerance 1e-7, verifies recommendation seed exclusion and evidence abstention, and checks the synthetic experiment contribution arithmetic. Feature fixture tests confirm future transactions cannot change snapshot features, future customers are not prematurely eligible, label windows are subsequent and incomplete windows are rejected.

Additional API checks exercise /api/predict, /api/recommend, /api/ask and /api/experiment. Profile contracts reject inconsistent trailing history, unsupported cold starts, fractional counts and nonfinite values. Forest path contributions reconcile to raw probability. CSV tests reject duplicate participants, detect assignment imbalance and retain the inconclusive synthetic contribution result.

Browser checks exercise changed profile scoring, invalid histories, capacity selection, one/two-product ranking, source retrieval, unsupported-query abstention, synthetic experiment loading and duplicate rejection. The experiment screen guards against late responses after navigation. Desktop and mobile checks, captures and deployment are recorded in the final handoff. Model training results and mixed outcomes are in MODEL_CARD.md and docs/outputs/ML_RESULTS.md.

Final narrow-screen checks for prediction and recommendation views measured 375 CSS-pixel width with document scrollWidth 375; desktop measured 1425/1425. The actual CSV file chooser was exercised with the synthetic fixture, then analysed successfully through the local API. Its uploaded provenance remains labelled unverified rather than claiming a real campaign. A fresh local test log contained no browser warnings/errors. The refreshed 55-second H.264 walkthrough was decoded at representative frames and visually inspected.

Portable forest traversal also matches sklearn's float32 feature conversion at split boundaries. A boundary case where float64 and float32 would choose different leaves is checked independently in Python and JavaScript, alongside the exported sklearn reference profiles.
