# NYC 311 Operations: Resolution Risk and Triage

A real-world operations analytics case study using **884,765 NYC 311 service requests created in Q1 2025**.

> **Portfolio question:** Where should an operations team focus triage and staffing attention to reduce long-running service requests?

## Headline findings

- **23.7%** of valid closed requests exceeded the transparent 72-hour triage threshold.
- Median resolution time was **12.6 hours**, but the 90th percentile was **437.5 hours**.
- HPD handled **246,365 closed requests** with a **46.0%** 72-hour breach rate.
- `UNSANITARY CONDITION` had **25,931 requests** and an **85.2%** breach rate.
- A temporal intake-risk model achieved **ROC-AUC 0.946** and **average precision 0.833** on March 2025 holdout data.

## Contents

- [`portfolio.md`](portfolio.md) — full recruiter-facing case study
- [`src/download_data.py`](src/download_data.py) — reproducible official API download
- [`src/analyze.py`](src/analyze.py) — cleaning, KPIs, priority queue, model, and charts
- [`analysis/`](analysis/) — summary metrics and evidence tables
- [`charts/`](charts/) — five visualizations
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — source fields and derived metrics
- [`docs/methodology.md`](docs/methodology.md) — definitions, assumptions, and limitations
- [`sql/operations_queries.sql`](sql/operations_queries.sql) — SQL translation of core metrics

## Data source

[NYC OpenData: 311 Service Requests from 2020 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9), dataset ID `erm2-nwe9`. The source is updated daily and contains service-request information without personally identifying customer data, according to the dataset description.

## Reproduce

```bash
pip install -r requirements.txt
python src/download_data.py
python src/analyze.py
```

The complete Q1 extract is approximately 213 MB and is intentionally not committed to GitHub. The download script recreates it directly from the official source.

## Important interpretation note

The 72-hour threshold is an analytical triage assumption, **not an official NYC SLA**. Findings are observational and should be validated with agency operations teams before implementation.

## Skills demonstrated

Python/pandas · scikit-learn · SQL · large public API ingestion · operational KPI design · queue prioritisation · temporal validation · interpretable predictive triage · data storytelling
