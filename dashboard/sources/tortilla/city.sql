-- dashboard/sources/tortilla/city.sql
SELECT * FROM read_parquet('https://github.com/jrocha02/tortillanomics/releases/latest/download/dim_city.parquet')
