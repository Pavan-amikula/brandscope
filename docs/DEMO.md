# Demo walkthrough

The 56-second MP4 is a captioned walkthrough assembled from genuine browser screenshots captured while exercising the running Python application. It uses slow vertical pans through full-page captures and successive live-monitor states. It has no audio and is not a continuous desktop recording. No UI or analytical results are fabricated.

The event screenshots show successful real HTTP requests to the local SQLite-backed API; their purchase amounts are explicitly synthetic. The GitHub Pages preview uses browser storage instead, as labelled in that preview. Scenario outputs are assumptions, not measured profit.

| Time | Screen | Explanation |
| --- | --- | --- |
| 00–08s | 01 / Growth overview | Audit the full dataset. Keep gross sales, returns and net sales visible. |
| 08–15s | 02 / Market context | Sweden: 8 identified shoppers and 34 orders. A small export sample, not a market estimate. |
| 15–24s | 03 / Shopper intelligence | Turn RFM segments, retention and basket associations into hypotheses to test. |
| 24–33s | 04 / Contribution economics | Default assumptions: GBP 255 modelled contribution. Audience is too small for the test. |
| 33–40s | 05 / Stress-test the offer | Raise the discount from 5% to 20%: modelled contribution becomes GBP -825. |
| 40–43s | 06 / Real HTTP ingestion | SQLite-backed event ingestion; explicit synthetic flags; two-second polling. |
| 43–45s | 06 / Event received | A new demonstration order is accepted and the monitor updates. |
| 45–47s | 06 / Events persist | Event IDs deduplicate orders. Demo totals stay separate from historical analysis. |
| 47–56s | 07 / Evidence before claims | Review temporal ranking diagnostics, method boundaries and source references. |

Files: `assets/brandscope-demo.mp4`, `assets/brandscope-preview.gif`, `assets/brandscope-demo.srt`. Full application screenshots and a mobile capture are in the same assets folder.

To reproduce the workflow interactively: use the README's two-minute tour, run `python server.py`, change the discount, save a scenario, download a brief, then send events from Activation monitor. Actual captures are from 25 October 2026.
