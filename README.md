# 🌽 tortillanomics

Tracking the price of tortillas across Mexico, since 2007.

[![Build](https://img.shields.io/badge/build-TODO-lightgrey)](#) [![Data](https://img.shields.io/badge/parquet-download-blue)](#use-the-data) [![Docs](https://img.shields.io/badge/dbt-docs-orange)](#)

*[Versión en español abajo ↓](#-tortillanomics-es)*

---

## What is this?

A small data project that scrapes daily tortilla prices from [SNIIM](https://www.economia-sniim.gob.mx/TortillaMesPorDia.asp) (the Mexican government's market price tracker), models them with dbt, and publishes clean parquet files that anyone can query.

**~250,000 rows. 56 cities. 19 years of history. Two channels: tortillerías and supermarkets.**

If you want to know how much tortillas cost in Culiacán in March 2014, this repo can tell you in one SQL query.

## Why I built it

Tortillas are the canonical Mexican consumer good. SNIIM has been publishing prices since 2007 in clunky HTML tables that pretend to be Excel files, but nobody had turned them into something queryable. I wanted to learn dbt properly, and I wanted to build something useful for my country with public data. This is both.

It's also a step toward something bigger — eventually I want to do the same for the rest of the *canasta básica* (eggs, beans, milk, oil) using the same model structure.

## What the data shows

A few things I found interesting while building this:

- **Tortillas are ~3x more expensive than 16 years ago.** Roughly $9/kg in 2010, ~$28/kg in 2026.
- **The 2011–2012 tortilla crisis is in the data.** Some cities saw 50%+ year-over-year inflation in early 2012 — the result of the US Midwest drought spiking corn prices.
- **Supermarkets are ~40–60% cheaper than tortillerías.** Not because they're more efficient; they sell a different product (industrial brands like Maseca vs. fresh nixtamal). The two channels aren't directly comparable.
- **The most expensive cities tend to be on the northern border** (Ciudad Juárez, Tijuana, Hermosillo). The cheapest tend to be in the south (Tampico, Xalapa, Puebla).

**Stack:** Python 3.13, `uv`, dbt-duckdb, DuckDB, GitHub Actions, GitHub Pages.

## Project structure
```
tortillanomics/
├── ingestion/              # Python scraper (SNIIM HTML → Parquet)
├── data/raw/               # Partitioned Parquet by year / month / channel
├── tortillanomics_dbt/     # dbt project
│   ├── models/
│   │   ├── staging/        # Cleaned source data
│   │   └── marts/          # dim_city, fct_tortilla_prices_daily, 3 analytical marts
│   ├── seeds/cities.csv    # Hand-curated city dimension (INEGI codes, region, etc.)
│   └── packages.yml        # dbt_utils, dbt_expectations
└── .github/workflows/      # CI: scrape → build → publish parquet → deploy docs
```

## Use the data

You don't need to clone this repo to use the data. Each successful run publishes clean Parquet files to the GitHub releases page. Query them directly with DuckDB:

```python
import duckdb

# Top 10 most expensive cities, latest month
duckdb.sql("""
    SELECT ciudad_canonical, precio_mensual
    FROM 'https://github.com//tortillanomics/releases/latest/download/fct_tortilla_prices_daily.parquet'
    WHERE canal = 'tortillerias'
      AND mes = (SELECT max(mes) FROM 'https://...')
    ORDER BY precio_mensual DESC LIMIT 10
""").show()
```

Or in R:
```r
df <- arrow::read_parquet("https://github.com//tortillanomics/releases/latest/download/fct_tortilla_prices_daily.parquet")
```

Or in your terminal:
```bash
duckdb -c "SELECT * FROM 'https://github.com//tortillanomics/releases/latest/download/fct_tortilla_prices_daily.parquet' WHERE ciudad_canonical = 'Culiacán' LIMIT 10"
```

## Run it locally

```bash
git clone https://github.com//tortillanomics
cd tortillanomics
uv sync

# Build the dbt models (uses checked-in Parquet, no scraping needed)
cd tortillanomics_dbt
dbt deps --profiles-dir .
dbt build --profiles-dir .

# Optional: re-scrape the latest month
cd ..
uv run python -m ingestion.scrape_sniim --latest
```

The DuckDB file `dev.duckdb` is created on first build; it's gitignored.

## Data caveats

A few things worth knowing before quoting numbers from this dataset:

- **Tortillerías channel begins 2010.** SNIIM only published autoservicios before that.
- **Coverage varies year to year.** Autoservicios covers ~50–56 cities; tortillerías covers ~41–43.
- **Channel comparisons aren't apples-to-apples.** Supermarkets sell industrial brands (Maseca, Bimbo); tortillerías sell fresh nixtamal. The price gap reflects product type, not market efficiency.
- **2026 is incomplete.** Year-to-date only.
- **SNIIM occasionally revises past months.** A snapshot model tracks revisions if you care.

## Roadmap

- [ ] Fill `population_2020` in the cities seed (INEGI 2020 census)
- [ ] Add a small Evidence.dev / Streamlit dashboard
- [ ] Expand to canasta básica (huevo, frijol, leche, aceite) — same model structure, new sources
- [ ] News geocoding layer that pairs price changes with news mentions

## License

[MIT](LICENSE). Data sourced from SNIIM (public domain) — please attribute when using.

---
