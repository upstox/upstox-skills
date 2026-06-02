"""
resolve_instrument.py — Resolve human names / symbols to Upstox instrument_keys.

Upstox publishes per-EXCHANGE instrument files (NSE, BSE, MCX) plus `complete`.
There are no per-segment files; filter the `segment` column instead. Verified
columns include: segment, name, trading_symbol, instrument_key, isin,
instrument_type (EQ/CE/PE/FUT/INDEX), strike_price, expiry (epoch ms), lot_size.

Usage:
    python resolve_instrument.py "Reliance"
    python resolve_instrument.py "NIFTY" --options --expiry 2025-01-30 --type CE
    python resolve_instrument.py --lot-size NIFTY
"""

from __future__ import annotations

import argparse
import gzip
import io
import sys

import pandas as pd
import requests

EXCH_URL = "https://assets.upstox.com/market-quote/instruments/exchange/{}.json.gz"
VALID_EXCHANGES = ("NSE", "BSE", "MCX", "complete")

_cache: dict[str, pd.DataFrame] = {}


def load_instruments(exchange: str = "NSE") -> pd.DataFrame:
    """Download and cache an instrument master file (exchange-level)."""
    if exchange not in VALID_EXCHANGES:
        raise ValueError(f"exchange must be one of {VALID_EXCHANGES}, got {exchange!r}")
    if exchange not in _cache:
        raw = requests.get(EXCH_URL.format(exchange), timeout=60).content
        _cache[exchange] = pd.read_json(io.BytesIO(gzip.decompress(raw)))
    return _cache[exchange]


def search_equity(query: str, exchange: str = "NSE", limit: int = 10) -> pd.DataFrame:
    """Search equities by company name or trading symbol."""
    df = load_instruments(exchange)
    eq = df[df["segment"] == f"{exchange}_EQ"]
    q = query.upper()
    mask = eq["name"].str.upper().str.contains(q, na=False) | \
        eq["trading_symbol"].str.upper().str.contains(q, na=False)
    cols = [c for c in ("instrument_key", "trading_symbol", "name", "isin") if c in eq.columns]
    return eq[mask][cols].head(limit).reset_index(drop=True)


def resolve_isin(isin: str, exchange: str = "NSE") -> str | None:
    """Return the instrument_key for an ISIN, or None."""
    df = load_instruments(exchange)
    row = df[df.get("isin") == isin]
    return None if row.empty else row.iloc[0]["instrument_key"]


def search_options(symbol: str, expiry: str, option_type: str | None = None,
                   exchange: str = "NSE") -> pd.DataFrame:
    """Search F&O options by underlying symbol and expiry (YYYY-MM-DD)."""
    df = load_instruments(exchange)
    fo = df[df["segment"] == f"{exchange}_FO"]
    expiry_ms = int(pd.Timestamp(expiry, tz="Asia/Kolkata").timestamp() * 1000)
    mask = (fo["asset_symbol"].str.upper() == symbol.upper()) & \
           (fo["expiry"].between(expiry_ms, expiry_ms + 86_400_000 - 1))
    if option_type:
        mask &= fo["instrument_type"].str.upper() == option_type.upper()
    cols = ["instrument_key", "trading_symbol", "strike_price", "instrument_type", "lot_size"]
    cols = [c for c in cols if c in fo.columns]
    return fo[mask][cols].sort_values("strike_price").reset_index(drop=True)


def get_lot_size(symbol: str, exchange: str = "NSE") -> int:
    """Return the F&O lot size for an underlying symbol."""
    df = load_instruments(exchange)
    fo = df[(df["segment"] == f"{exchange}_FO") &
            (df["asset_symbol"].str.upper() == symbol.upper())]
    if fo.empty:
        raise ValueError(f"No F&O instruments found for {symbol}")
    return int(fo.iloc[0]["lot_size"])


def main() -> None:
    p = argparse.ArgumentParser(description="Resolve Upstox instrument_keys")
    p.add_argument("query", nargs="?", help="Company name, symbol, or underlying")
    p.add_argument("--exchange", default="NSE", choices=VALID_EXCHANGES)
    p.add_argument("--options", action="store_true", help="Search F&O options")
    p.add_argument("--expiry", help="Option expiry YYYY-MM-DD (with --options)")
    p.add_argument("--type", choices=["CE", "PE"], help="Option type")
    p.add_argument("--lot-size", metavar="SYMBOL", help="Print lot size and exit")
    args = p.parse_args()

    if args.lot_size:
        print(get_lot_size(args.lot_size, args.exchange))
        return

    if not args.query:
        p.error("query is required unless --lot-size is used")

    if args.options:
        if not args.expiry:
            p.error("--options requires --expiry")
        results = search_options(args.query, args.expiry, args.type, args.exchange)
    else:
        results = search_equity(args.query, args.exchange)

    if results.empty:
        print(f"No instruments found for: {args.query}")
        sys.exit(1)
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
