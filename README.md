# Yahoo Finance ELT Pipeline

![CI/CD](https://github.com/ozama13/Yahoo_Finance_ETL_Platform/actions/workflows/dbt_ci.yml/badge.svg)

A production-grade ELT pipeline that ingests real stock market data from Yahoo Finance, loads it into Snowflake, transforms it with dbt, and orchestrates everything with Apache Airflow.

👉 [View the live dashboard](https://yahoofinanceetlplatform-jxzyft9sggrd8hy9zrfq2x.streamlit.app)

---

## Overview

This project demonstrates a modern data engineering stack built end to end — from raw data ingestion to a live analytics dashboard. It mirrors how data teams at mid-to-large companies build and maintain data pipelines in production.

The pipeline runs automatically every weekday at 6am, pulling fresh stock price data for 5 major NASDAQ tickers, transforming it through a layered dbt architecture, and serving it to a Streamlit dashboard backed by Snowflake.

---

## Architecture

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Data Warehouse | Snowflake | Storage & compute |
| Transformation | dbt Core | Modular SQL transformations |
| Orchestration | Apache Airflow | Pipeline scheduling |
| Ingestion | Python + yfinance | Raw data extraction |
| Dashboard | Streamlit + Plotly | Data visualization |
| CI/CD | GitHub Actions | Automated testing |
| Version Control | Git + GitHub | Source control |

---

## Data Models

### Staging
- `stg_stock_prices` — cleaned and renamed OHLCV data, filtered for valid records

### Intermediate
- `int_stock_metrics` — enriched with financial metrics:
  - 7, 30, and 90-day moving averages
  - Daily return %
  - Cumulative return % since January 2020
  - 30-day rolling average volume
  - Price vs MA30 momentum signal

### Marts
- `fct_stock_prices` — daily stock price fact table with surrogate keys, momentum signals, and return categories
- `dim_tickers` — one row per ticker with all-time statistics, company metadata, and sector classification

---

## Tickers Tracked

| Ticker | Company | Sector |
|--------|---------|--------|
| AAPL | Apple Inc. | Technology |
| MSFT | Microsoft Corporation | Technology |
| GOOGL | Alphabet Inc. | Communication Services |
| AMZN | Amazon.com Inc. | Consumer Discretionary |
| META | Meta Platforms Inc. | Communication Services |

---

## Snowflake Architecture

The warehouse follows a least-privilege RBAC model with purpose-separated roles and warehouses:

- **Databases:** `RAW` → `STAGING` → `ANALYTICS` — strict layer separation
- **Roles:** `LOADER`, `TRANSFORMER`, `REPORTER`, `ANALYST`, `DBT_CI` — each with minimum required permissions
- **Warehouses:** Separate compute for ingestion, transformation, and querying — all with auto-suspend
- **Resource monitors:** Credit quotas and alerts at the account and warehouse level

---

## Data Quality

All models include dbt tests covering:
- `not_null` on all key columns
- `unique` on all primary keys
- `accepted_values` on categorical columns (ticker symbols, momentum signals, return categories)
- Source freshness checks — warns after 24 hours, errors after 48 hours

---

## CI/CD Pipeline

Every push to `main` triggers a GitHub Actions workflow that:

1. Spins up a clean Ubuntu environment
2. Installs dbt-snowflake
3. Injects Snowflake credentials from repository secrets
4. Runs `dbt compile` — validates all SQL
5. Runs `dbt run` — rebuilds all models
6. Runs `dbt test` — validates all data quality checks
7. Uploads dbt docs as a build artifact

---

## Airflow DAG

The `yahoo_finance_elt` DAG runs Monday–Friday at 6am UTC:

- Task 1 pulls the latest prices from Yahoo Finance into `RAW.YAHOO_FINANCE.STOCK_PRICES`
- Task 2 rebuilds all dbt models in dependency order
- Task 3 runs all data quality tests — fails the DAG if any test fails
- Task 4 regenerates dbt documentation

---

## Project Structure
---

## Setup

### Prerequisites
- Python 3.11+
- Snowflake account
- dbt Core

### Installation

```bash
git clone https://github.com/ozama13/Yahoo_Finance_ETL_Platform.git
cd Yahoo_Finance_ETL_Platform
pip install dbt-snowflake
dbt deps
```

### Configuration

Create `~/.dbt/profiles.yml`:

```yaml
analytics_platform:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: YOUR_ACCOUNT
      user: YOUR_USER
      password: YOUR_PASSWORD
      role: TRANSFORMER
      warehouse: DBT_WH
      database: STAGING
      schema: dbt_dev
      threads: 4
```

### Running the Pipeline

```bash
# Load raw data
python ingestion/load_yahoo_finance.py

# Run dbt models
dbt run

# Run tests
dbt test

# Generate docs
dbt docs generate
dbt docs serve
```

---

## Key Concepts Demonstrated

- **ELT architecture** — raw data lands untouched, transformations happen in the warehouse
- **Dimensional modeling** — star schema with fact and dimension tables
- **Incremental loading** — truncate and reload for daily stock data
- **Data quality** — automated testing on every model and source
- **RBAC** — least-privilege role hierarchy in Snowflake
- **CI/CD** — automated testing on every push to main
- **Orchestration** — Airflow DAG with linear task dependencies
- **Cost controls** — auto-suspend warehouses and resource monitors

---
---

## Lessons Learned

**Multi-Python environments are messy**
My machine had both Anaconda (Python 3.9) and Python 3.13 installed, which caused package conflicts throughout the project. `yfinance` and `snowflake-connector-python` installed into different interpreters depending on which `pip` was called. The fix was to always use `python3.13 -m pip install` and `python3.13 script.py` explicitly. In production, this is solved with Docker or a single managed virtual environment.

**Snowflake RBAC requires upfront planning**
Setting up roles after the fact is painful — grants need to be applied at the database, schema, and future table level separately. Designing the role hierarchy before creating any objects would have saved significant debugging time.

**dbt ephemeral models can't be run directly**
Ephemeral models are compiled inline into downstream models rather than materialized as objects. Trying to `dbt run --select` an ephemeral model returns 0 results with no error, which was confusing. The fix was switching intermediate models to views during development.

**CI/CD YAML is unforgiving**
A single indentation error or nested quote in the GitHub Actions workflow file caused multiple failed runs. Editing YAML directly in the GitHub UI is more reliable than writing it in the terminal where shell escaping adds hidden complexity.

**Separate compute for separate workloads**
Snowflake charges by compute time, not data volume. Having dedicated warehouses for ingestion, transformation, and querying — all with auto-suspend — keeps costs predictable and prevents workloads from competing for resources.

**Version pinning matters**
Using `dbt=1.11.0-b3` (a beta) caused minor syntax differences from the stable API, particularly around `accepted_values` test syntax. Pinning to a stable release in `requirements.txt` is always safer for production pipelines.
