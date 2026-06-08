{{ config(materialized='view') }}

with source as (
    select * from {{ source('sniim', 'tortilla_prices') }}
),

cleaned as (
    select
        -- Replace non-breaking spaces (U+00A0) with regular spaces, then trim
        trim(replace(estado, chr(160), ' '))      as estado_raw,
        trim(replace(ciudad, chr(160), ' '))      as ciudad_raw,
        cast(fecha as date)                        as fecha,
        cast(precio_kg as double)                  as precio_kg,
        canal,
        cast(anio as integer)                      as anio,
        cast(mes as integer)                       as mes,
        case
            when ciudad like 'ZM %' then true
            else false
        end                                        as is_zona_metropolitana,
        scraped_at,
        source_url
    from source
    where precio_kg is not null
      and precio_kg between 1 and 100
)

select
    {{ dbt_utils.generate_surrogate_key(['estado_raw', 'ciudad_raw', 'fecha', 'canal']) }} as price_id,
    *
from cleaned
