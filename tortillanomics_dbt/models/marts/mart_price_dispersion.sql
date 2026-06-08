-- models/marts/mart_price_dispersion.sql
{{ config(materialized='table') }}

with monthly_by_city as (
    select
        c.region,
        f.canal,
        date_trunc('month', f.fecha) as mes,
        c.ciudad_canonical,
        avg(f.precio_kg) as precio
    from {{ ref('fct_tortilla_prices_daily') }} f
    inner join {{ ref('dim_city') }} c using (city_id)
    where not c.is_zona_metropolitana   -- exclude ZMs to avoid double-counting
    group by 1, 2, 3, 4
)

select
    canal,
    mes,
    count(distinct ciudad_canonical)              as n_ciudades,
    avg(precio)                                   as precio_promedio,
    min(precio)                                   as precio_minimo,
    max(precio)                                   as precio_maximo,
    max(precio) - min(precio)                     as rango,
    stddev(precio)                                as desviacion_estandar,
    stddev(precio) / nullif(avg(precio), 0)       as coeficiente_variacion,
    arg_min(ciudad_canonical, precio)             as ciudad_mas_barata,
    arg_max(ciudad_canonical, precio)             as ciudad_mas_cara
from monthly_by_city
group by 1, 2
