# Instruments Reference

> Verified against the live instrument files. There are **no per-segment files**
> like `NSE_EQ.json.gz` — Upstox publishes **per-exchange** files (`NSE`, `BSE`,
> `MCX`) plus `complete`. Filter by the `segment` column. Columns are
> `trading_symbol`, `strike_price`, `instrument_type` (CE/PE/FUT/EQ/INDEX),
> and `expiry` is **epoch milliseconds**, not a date string.

## instrument_key format

```
SEGMENT|IDENTIFIER
"NSE_EQ|INE002A01018"     # equity → ISIN
"NSE_INDEX|Nifty 50"      # index  → name
"NSE_FO|43919"            # F&O    → numeric exchange token
"MCX_FO|434855"           # commodity future
```

Always use `instrument_key` (unique, persistent) in API calls — not `exchange_token`.

---

## Instrument master files (daily, gzipped JSON)

```
https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz   # everything
https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz        # all NSE segments
https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz
https://assets.upstox.com/market-quote/instruments/exchange/MCX.json.gz
```

Other files: `mf-instruments.json.gz`, `MTF.json.gz`, `suspended-instrument.json.gz`.
(CSV equivalents exist with `.csv.gz` but JSON is recommended.)

### Columns (verified from NSE.json.gz)

`segment` (e.g. `NSE_EQ`, `NSE_FO`, `NSE_INDEX`, `NCD_FO`), `exchange` (`NSE`),
`name`, `trading_symbol`, `instrument_key`, `exchange_token`, `isin` (equity),
`instrument_type` (`EQ`/`CE`/`PE`/`FUT`/`INDEX`/...), `strike_price`, `expiry`
(epoch ms), `lot_size`, `tick_size`, `freeze_quantity`, `qty_multiplier`,
`asset_symbol`, `underlying_symbol`, `minimum_lot`, `weekly`.

---

## Load & search

```python
import requests, gzip, io, pandas as pd

EXCH_URL = "https://assets.upstox.com/market-quote/instruments/exchange/{}.json.gz"

def load_instruments(exchange="NSE"):     # exchange ∈ NSE, BSE, MCX, complete
    raw = requests.get(EXCH_URL.format(exchange), timeout=60).content
    return pd.read_json(io.BytesIO(gzip.decompress(raw)))

df = load_instruments("NSE")

# Equity by name/symbol — filter the NSE_EQ segment
eq = df[df["segment"] == "NSE_EQ"]
hits = eq[eq["name"].str.contains("Reliance", case=False, na=False) |
          eq["trading_symbol"].str.contains("RELIANCE", case=False, na=False)]
print(hits[["instrument_key", "trading_symbol", "name", "isin"]].head())
```

### F&O options for an underlying + expiry

`expiry` is epoch ms — convert the target date to compare:

```python
import pandas as pd

def find_options(df, underlying="NIFTY", expiry="2025-01-30", option_type="CE"):
    expiry_ms = int(pd.Timestamp(expiry, tz="Asia/Kolkata").timestamp() * 1000)
    fo = df[df["segment"] == "NSE_FO"]
    mask = (fo["asset_symbol"].str.upper() == underlying.upper()) & \
           (fo["instrument_type"] == option_type) & \
           (fo["expiry"].between(expiry_ms, expiry_ms + 86_400_000 - 1))
    return fo[mask].sort_values("strike_price")[
        ["instrument_key", "trading_symbol", "strike_price", "lot_size"]]
```

### Lot size for an F&O underlying

```python
def lot_size(df, underlying="NIFTY"):
    fo = df[(df["segment"] == "NSE_FO") &
            (df["asset_symbol"].str.upper() == underlying.upper())]
    if fo.empty:
        raise ValueError(f"No F&O instruments for {underlying}")
    return int(fo.iloc[0]["lot_size"])
```

> `scripts/resolve_instrument.py` wraps these helpers with caching and a CLI.
