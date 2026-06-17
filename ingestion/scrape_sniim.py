"""
Scrape SNIIM monthly tortilla prices into partitioned parquet
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import httpx
import pandas as pd

BASE_URL = "https://www.economia-sniim.gob.mx/TortillaMesPorDia.asp"
DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "tortilla"

CHANNELS = {"todos": 3, "autoservicios": 2, "tortillerias": 1}

logger = logging.getLogger(__name__)


def build_url(year: int, month: int, channel: str) -> str:
    params = {
        "Cons": "D",
        "prod": CHANNELS[channel],
        "dqMesMes": month,
        "dqAnioMes": year,
        "preEdo": "Ciu",
        "Formato": "Xls",
        "submit": "Ver Resultados",
    }
    return f"{BASE_URL}?" + "&".join(f"{k}={v}" for k, v in params.items())


def download(year: int, month: int, channel: str) -> bytes:
    url = build_url(year, month, channel)
    headers = {"User-Agent": "tortillanomics/0.1 (github.com/yourname/tortillanomics)"}
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        if len(resp.content) < 1000:
            raise ValueError(
                f"Response too small ({len(resp.content)} bytes) — probably empty month"
            )
        return resp.content


def parse(xls_bytes: bytes, year: int, month: int, channel: str) -> pd.DataFrame:
    tables = pd.read_html(BytesIO(xls_bytes), header=None, flavor="lxml")
    if not tables:
        raise ValueError("No tables found in response")

    raw = max(tables, key=lambda t: t.shape[0] * t.shape[1])

    # Find the header row
    header_idx = None
    for i, row in raw.iterrows():
        vals = row.astype(str).str.strip().str.lower().tolist()
        if vals[0] == "estado" and vals[1] == "ciudad":
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Header row 'Estado | Ciudad | ...' not found")

    headers = raw.iloc[header_idx].astype(str).str.strip().tolist()
    df = raw.iloc[header_idx + 1 :].copy().reset_index(drop=True)
    df.columns = ["estado", "ciudad"] + headers[2:]

    # Drop footer/notes rows
    junk = r"Precio PPP|^ND:|^Nota:|^1/|^2/|Promedio"
    df = df[~df["estado"].astype(str).str.contains(junk, na=False, regex=True)]
    df = df.dropna(subset=["ciudad"]).reset_index(drop=True)

    # Source HTML uses rowspan on Estado → forward-fill the NaNs
    df["estado"] = df["estado"].replace("", pd.NA).ffill()

    # Each estado block ends with a state-aggregate row where ciudad == estado.
    # Mark the LAST such row per block and drop them.
    df["_block"] = (df["estado"] != df["estado"].shift()).cumsum()
    df["_self_match"] = df["ciudad"] == df["estado"]
    df["_is_agg"] = False
    for _, grp in df.groupby("_block"):
        matches = grp[grp["_self_match"]]
        if not matches.empty:
            df.loc[matches.index[-1], "_is_agg"] = True
    df = (
        df[~df["_is_agg"]]
        .drop(columns=["_block", "_self_match", "_is_agg"])
        .reset_index(drop=True)
    )

    # Wide → long
    date_cols = [c for c in df.columns if c not in ("estado", "ciudad")]
    long_df = df.melt(
        id_vars=["estado", "ciudad"],
        value_vars=date_cols,
        var_name="dia_label",
        value_name="precio_kg",
    )

    long_df["dia"] = pd.to_numeric(
        long_df["dia_label"].astype(str).str.extract(r"(\d+)", expand=False),
        errors="coerce",
    ).astype("Int64")
    long_df = long_df.dropna(subset=["dia", "ciudad"])

    long_df["fecha"] = pd.to_datetime(
        {"year": year, "month": month, "day": long_df["dia"]},
        errors="coerce",
    )
    long_df = long_df.dropna(subset=["fecha"])
    long_df["precio_kg"] = pd.to_numeric(long_df["precio_kg"], errors="coerce")

    long_df["canal"] = channel
    long_df["anio"] = year
    long_df["mes"] = month
    long_df["source_url"] = build_url(year, month, channel)
    long_df["scraped_at"] = datetime.now(timezone.utc)

    # Average any remaining duplicate observations per (city, date)
    long_df = long_df.groupby(
        ["estado", "ciudad", "fecha", "canal", "anio", "mes", "source_url"],
        as_index=False,
    ).agg(precio_kg=("precio_kg", "mean"), scraped_at=("scraped_at", "max"))

    return long_df[
        [
            "estado",
            "ciudad",
            "fecha",
            "precio_kg",
            "canal",
            "anio",
            "mes",
            "scraped_at",
            "source_url",
        ]
    ]


def write_parquet(df: pd.DataFrame, year: int, month: int, channel: str) -> Path:
    out_dir = DATA_ROOT / f"anio={year}" / f"mes={month:02d}" / f"canal={channel}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def scrape_one(year: int, month: int, channel: str) -> Path:
    logger.info("Scraping %s %d-%02d", channel, year, month)
    df = parse(download(year, month, channel), year, month, channel)
    path = write_parquet(df, year, month, channel)
    logger.info("Wrote %d rows → %s", len(df), path)
    return path


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int)
    p.add_argument("--month", type=int)
    p.add_argument("--channel", choices=list(CHANNELS), default="tortillerias")
    p.add_argument("--backfill", nargs=2, type=int, metavar=("FROM", "TO"))
    p.add_argument("--latest", action="store_true")
    args = p.parse_args()

    channels_to_run = ("tortillerias", "autoservicios")
    now = datetime.now()

    if args.latest:
        for ch in channels_to_run:
            scrape_one(now.year, now.month, ch)
        return 0

    if args.backfill:
        from_y, to_y = args.backfill
        for y in range(from_y, to_y + 1):
            for m in range(1, 13):
                if y == now.year and m > now.month:
                    break
                for ch in channels_to_run:
                    try:
                        scrape_one(y, m, ch)
                    except Exception as e:
                        logger.error("Failed %s %d-%02d: %s", ch, y, m, e)
                    time.sleep(1)  # be polite to the gov server
        return 0

    if args.year and args.month:
        scrape_one(args.year, args.month, args.channel)
        return 0

    p.error("Pass --year/--month, --backfill FROM TO, or --latest")
    return 1


if __name__ == "__main__":
    sys.exit(main())
