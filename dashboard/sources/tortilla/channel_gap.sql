-- dashboard/sources/tortilla/channel_gap.sql
SELECT * FROM read_parquet('https://github.com/jrocha02/tortillanomics/releases/latest/download/mart_channel_gap.parquet')
