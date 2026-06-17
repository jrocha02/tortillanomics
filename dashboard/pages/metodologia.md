---
title: Metodología
---

# 🔬 Metodología

Cómo se construye este sitio, de dónde vienen los datos, y qué saber antes de citar los números.

## Fuente de los datos

Todos los precios provienen del **[SNIIM](https://www.economia-sniim.gob.mx/TortillaMesPorDia.asp)** (Sistema Nacional de Información e Integración de Mercados), una iniciativa de la Secretaría de Economía que publica precios de productos básicos desde el 2007.

SNIIM publica precios de tortilla **tres veces por semana** (lunes, miércoles y viernes), por ciudad y por canal de venta. Este sitio raspa esos datos automáticamente, los limpia, los modela, y los republica en formato abierto.

## Arquitectura


El pipeline corre automáticamente vía GitHub Actions tres veces por semana (martes, jueves y sábado a las 2 AM hora del centro de México), un día después de cada publicación de SNIIM.

## Stack técnico

- **Python 3.13** con `uv` para gestión de dependencias y `httpx` + `pandas` para el scraper
- **dbt-duckdb** para modelado de datos con esquema en estrella
- **DuckDB** como motor de almacenamiento local
- **GitHub Actions** para orquestación y CI/CD
- **GitHub Pages** para hospedar este dashboard y la documentación
- **Evidence** para el dashboard que estás viendo ahora mismo

## Modelo de datos

Los datos siguen un esquema en estrella clásico, organizados en tres capas:

- **Staging** (`stg_sniim__tortilla_prices`): datos crudos limpiados — corrección de caracteres invisibles, normalización de tipos, eliminación de duplicados.
- **Dimensiones** (`dim_city`): catálogo canónico de 56 ciudades con código INEGI, región, y población del Censo 2020.
- **Hechos** (`fct_tortilla_prices_daily`): tabla central con un registro por (ciudad, canal, fecha).
- **Marts** (`mart_price_inflation`, `mart_price_dispersion`, `mart_channel_gap`): tablas pre-agregadas para análisis específicos.


## Datos disponibles para descarga

Cada ejecución exitosa del pipeline publica los marts como archivos Parquet a un release público de GitHub. Puedes consultarlos directamente desde DuckDB, Python, R, o cualquier herramienta que lea Parquet por URL.

| Archivo | Grano | Filas aprox. |
|---|---|---|
| `fct_tortilla_prices_daily.parquet` | Ciudad × canal × día | 257,000 |
| `dim_city.parquet` | Ciudad | 56 |
| `mart_price_inflation.parquet` | Ciudad × canal × mes | 20,000 |
| `mart_price_dispersion.parquet` | Canal × mes | 432 |
| `mart_channel_gap.parquet` | Ciudad × mes | 8,100 |

Ejemplo en Python:

```python
import duckdb
df = duckdb.sql("""
    SELECT * 
    FROM 'https://github.com/jrocha02/tortillanomics/releases/latest/download/fct_tortilla_prices_daily.parquet'
    WHERE ciudad_canonical = 'Culiacán'
""").df()
```

[Descargar archivos Parquet →](https://github.com/jrocha02/tortillanomics/releases/latest)

## Advertencias sobre los datos

Antes de citar estos números en cualquier análisis, vale la pena saber:

- **El canal de tortillerías comienza en 2010.** SNIIM solo publicaba autoservicios antes de esa fecha.
- **Cobertura variable año con año.** El canal de autoservicios cubre típicamente 50–56 ciudades; tortillerías cubre alrededor de 41–43. No todas las ciudades aparecen en todos los meses.
- **Los canales no son directamente comparables.** Autoservicios reporta tortilla industrial (Maseca, Bimbo); tortillerías reporta tortilla fresca de nixtamal. La diferencia de precio refleja productos distintos, no solo márgenes.
- **El año 2026 es parcial.** Los datos del año actual están al día pero incompletos.
- **SNIIM revisa ocasionalmente meses pasados.** Las versiones publicadas pueden cambiar; este sitio refleja la versión más reciente.
- **Algunas ciudades aparecen como ZM (Zona Metropolitana).** Por ejemplo "ZM D.F." cubre el Valle de México completo, mientras que "D.F." cubre solo la Ciudad de México. Tratar como duplicado puede sobreestimar el peso del centro del país.

## Código y reproducibilidad

Todo el código es público y reproducible:

- **Repositorio**: [github.com/jrocha02/tortillanomics](https://github.com/jrocha02/tortillanomics)
- **Última actualización**: el sitio se reconstruye automáticamente; revisa los [GitHub Actions](https://github.com/jrocha02/tortillanomics/actions) para timestamps específicos.

Para clonar y construir localmente:

```bash
git clone https://github.com/jrocha02/tortillanomics
cd tortillanomics
uv sync
cd tortillanomics_dbt
uv run dbt deps --profiles-dir .
uv run dbt build --profiles-dir .
```
