{{ config(materialized='table') }}

with prices as (
    select distinct estado_raw, ciudad_raw
    from {{ ref('stg_sniim__tortilla_prices') }}
),

seed as (
    select * from {{ ref('cities') }}
),

joined as (
    select
        {{ dbt_utils.generate_surrogate_key(['p.estado_raw', 'p.ciudad_raw']) }} as city_id,
        p.estado_raw,
        p.ciudad_raw,
        s.estado_canonical,
        s.ciudad_canonical,
        s.inegi_state_code,
        s.region,
        s.population_2020,
        s.is_zona_metropolitana
    from prices p
    left join seed s
        on p.estado_raw = s.estado_raw
       and p.ciudad_raw = s.ciudad_raw
)

select * from joined
