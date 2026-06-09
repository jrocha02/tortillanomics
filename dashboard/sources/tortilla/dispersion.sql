-- dashboard/sources/tortilla/dispersion.sql
SELECT * FROM read_parquet('https://github.com/jrocha02/tortillanomics/releases/latest/download/mart_price_dispersion.parquet')
