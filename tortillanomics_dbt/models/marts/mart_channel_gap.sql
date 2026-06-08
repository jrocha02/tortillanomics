-- models/marts/mart_channel_gap.sql
{{ config(materialized='table') }}

with monthly as (
    select
        f.city_id,
        c.ciudad_canonical,
        c.estado_canonical,
        c.region,
        date_trunc('month', f.fecha) as mes,
        f.canal,
        avg(f.precio_kg) as precio
    from {{ ref('fct_tortilla_prices_daily') }} f
    inner join {{ ref('dim_city') }} c using (city_id)
    group by 1, 2, 3, 4, 5, 6
),

pivoted as (
    select
        city_id,
        ciudad_canonical,
        estado_canonical,
        region,
        mes,
        max(case when canal = 'tortillerias'  then precio end) as precio_tortilleria,
        max(case when canal = 'autoservicios' then precio end) as precio_autoservicio
    from monthly
    group by 1, 2, 3, 4, 5
)

select
    *,
    precio_tortilleria - precio_autoservicio          as gap_absoluto,
    case
        when precio_autoservicio > 0
        then (precio_tortilleria - precio_autoservicio) / precio_autoservicio
    end                                                as gap_relativo
from pivoted
where precio_tortilleria is not null
  and precio_autoservicio is not null
