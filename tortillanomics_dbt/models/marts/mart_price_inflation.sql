{{ config(materialized='table') }}

with daily as (
    select
        f.city_id,
        c.ciudad_canonical,
        c.estado_canonical,
        c.region,
        f.canal,
        f.fecha,
        f.precio_kg
    from {{ ref('fct_tortilla_prices_daily') }} f
    inner join {{ ref('dim_city') }} c using (city_id)
),

monthly as (
    -- Average price per city/channel/month — the natural grain for inflation
    select
        city_id,
        ciudad_canonical,
        estado_canonical,
        region,
        canal,
        date_trunc('month', fecha) as mes,
        avg(precio_kg) as precio_mensual
    from daily
    group by 1, 2, 3, 4, 5, 6
),

with_lags as (
    select
        *,
        lag(precio_mensual, 1)  over w as precio_mes_anterior,
        lag(precio_mensual, 12) over w as precio_ano_anterior,
        avg(precio_mensual) over (
            partition by city_id, canal
            order by mes
            rows between 11 preceding and current row
        ) as precio_promedio_12m
    from monthly
    window w as (partition by city_id, canal order by mes)
)

select
    city_id,
    ciudad_canonical,
    estado_canonical,
    region,
    canal,
    mes,
    precio_mensual,
    precio_mes_anterior,
    precio_ano_anterior,
    precio_promedio_12m,
    case
        when precio_mes_anterior is not null and precio_mes_anterior > 0
        then (precio_mensual - precio_mes_anterior) / precio_mes_anterior
    end as inflacion_mom,
    case
        when precio_ano_anterior is not null and precio_ano_anterior > 0
        then (precio_mensual - precio_ano_anterior) / precio_ano_anterior
    end as inflacion_yoy
from with_lags
