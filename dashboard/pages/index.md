---
title: Tortillanomics
---

# 🌽 El precio de la tortilla en México

Desde 2007. Datos del SNIIM, modelados con dbt, actualizados cada semana.


<BigValue 
    data={precio_actual.filter(d => d.canal === 'tortillerias')}
    value=precio
    title="Precio actual (tortillerías)"
    fmt="$#,##0.00"
/>

<BigValue 
    data={precio_actual.filter(d => d.canal === 'tortillerias')}
    value=inflacion_yoy
    title="Inflación últimos 12 meses"
    fmt=pct1
/>

```sql precio_nacional_mensual
SELECT
    mes,
    canal,
    AVG(precio_mensual) AS precio
FROM tortilla.inflation
WHERE ciudad_canonical IS NOT NULL
GROUP BY mes, canal
ORDER BY mes
```

<LineChart 
    data={precio_nacional_mensual}
    x=mes
    y=precio
    series=canal
    title="Precio promedio nacional por canal"
    yAxisTitle="MXN / kg"
/>

```sql precio_actual
SELECT 
    ciudad_canonical as ciudad,
    estado_canonical as estado,
    region,
    canal,
    precio_mensual AS precio,
    inflacion_yoy
FROM tortilla.inflation
WHERE mes = (SELECT MAX(mes) FROM tortilla.inflation)
  AND ciudad_canonical IS NOT NULL
  AND canal = 'tortillerias'
ORDER BY precio_mensual DESC
LIMIT 15
```
