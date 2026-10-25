# Dataset attribution

Chen, D. (2015). **Online Retail** [Dataset]. UCI Machine Learning Repository.
DOI: https://doi.org/10.24432/C5BW33
Source: https://archive.ics.uci.edu/dataset/352/online%2Bretail
License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

The included `web/data.json`, `docs/results.json` and generated aggregate CSVs are derived from this dataset. Changes include exact deduplication, scoped merchandise filters, currency conversion to integer pence for arithmetic, segmentation and aggregation. Details: `docs/METHODS.md`. Raw customer identifiers are not included in the published aggregate bundle. The original raw dataset and generated row-level SQLite database are not committed; the rebuild script downloads the source directly.

No endorsement by the dataset creator, UCI, P&G or the research authors is implied.

The second version also includes source-derived benchmark tables, product metadata and fitted model artifacts under `web/models/` and `docs/outputs/`. The same source attribution and declared transformations apply. Training/inference source code is MIT licensed. `synthetic-experiment.csv` is separately generated demonstration data, prominently labelled synthetic; it does not contain real campaign participants.
