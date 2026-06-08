{{ config(materialized='table') }}

with prices as (
    select * from {{ ref('stg_sniim__tortilla_prices') }}
),

cities as (
    select city_id, estado_raw, ciudad_raw
    from {{ ref('dim_city') }}
)

select
    p.price_id,
    c.city_id,
    p.fecha,
    p.canal,
    p.precio_kg,
    p.is_zona_metropolitana,
    p.anio,
    p.mes,
    extract(quarter from p.fecha)                    as trimestre,
    extract(dayofweek from p.fecha)                  as dia_semana,
    p.scraped_at,
    p.source_url
from prices p
inner join cities c
    on p.estado_raw = c.estado_raw
   and p.ciudad_raw = c.ciudad_raw
