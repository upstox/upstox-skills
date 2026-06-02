"""
validate_order.py — Pre-flight order validation with safety guardrails.

Run this BEFORE placing any live order. It builds a human-readable preview and
flags problems. It does not place anything itself.

Checks:
  1. instrument_token format (SEGMENT|IDENTIFIER)
  2. Known product code, with a segment-fit warning
  3. F&O lot-size multiple (looked up from the live instrument master)
  4. LIMIT orders require price > 0; MARKET orders get a caution
  5. Notional-value warning (> ₹50,000)
  6. Quantity > 0
  7. Market-hours check (suggest AMO when closed)
"""

from __future__ import annotations

from datetime import datetime, time as dtime

try:                                   # works both as a module and run directly
    from .resolve_instrument import load_instruments
except ImportError:                    # pragma: no cover
    from resolve_instrument import load_instruments

# Market hours / timezone are optional niceties; degrade gracefully without pytz.
try:
    import pytz
    _IST = pytz.timezone("Asia/Kolkata")
except Exception:                      # pragma: no cover
    _IST = None

MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)
NOTIONAL_WARN_THRESHOLD = 50_000

KNOWN_PRODUCTS = {"I", "D", "CO", "OCO", "MTF"}
# segment prefix -> exchange-level instrument file
_FO_SEGMENTS = {"NSE_FO": "NSE", "BSE_FO": "BSE", "MCX_FO": "MCX", "NCD_FO": "NSE", "BCD_FO": "BSE"}


def validate_order(instrument_token, transaction_type, order_type, product,
                   quantity, price, is_amo=False):
    """Return {'valid', 'errors', 'warnings', 'order_preview'}."""
    errors, warnings = [], []

    # 1. instrument_token format
    if "|" not in instrument_token:
        return _result(False, [f"Invalid instrument_token '{instrument_token}'. "
                               f"Use 'SEGMENT|IDENTIFIER' e.g. 'NSE_EQ|INE002A01018'."], [], {})
    segment, _ = instrument_token.split("|", 1)

    # 2. product
    if product not in KNOWN_PRODUCTS:
        errors.append(f"Unknown product '{product}'. Valid: {sorted(KNOWN_PRODUCTS)}.")
    if segment in _FO_SEGMENTS and product == "MTF":
        warnings.append("MTF is not applicable to F&O — use 'I' or 'D'.")

    # 3. F&O lot-size multiple
    if segment in _FO_SEGMENTS:
        try:
            df = load_instruments(_FO_SEGMENTS[segment])
            row = df[df["instrument_token" if "instrument_token" in df.columns
                     else "instrument_key"] == instrument_token]
            if not row.empty:
                lot = int(row.iloc[0]["lot_size"])
                if quantity % lot != 0:
                    suggested = max(lot, round(quantity / lot) * lot)
                    errors.append(f"Quantity {quantity} is not a multiple of lot size "
                                  f"{lot}. Use {suggested}.")
            else:
                warnings.append("Could not find instrument in master to verify lot size.")
        except Exception as e:                      # network/parse issues shouldn't block
            warnings.append(f"Lot-size check skipped: {e}")

    # 4. price / order type
    if order_type == "LIMIT" and price <= 0:
        errors.append("LIMIT orders require price > 0.")
    if order_type == "MARKET":
        warnings.append("MARKET order: executes at the prevailing price. Prefer LIMIT for control.")

    # 5. notional
    notional = price * quantity if price > 0 else 0
    if notional > NOTIONAL_WARN_THRESHOLD:
        warnings.append(f"High notional ₹{notional:,.2f} (> ₹{NOTIONAL_WARN_THRESHOLD:,}). Confirm with the user.")

    # 6. quantity
    if quantity <= 0:
        errors.append("Quantity must be greater than 0.")

    # 7. market hours
    if _IST is not None and not is_amo:
        now = datetime.now(_IST).time()
        if not (MARKET_OPEN <= now <= MARKET_CLOSE):
            warnings.append(f"Market appears closed (IST {now:%H:%M}). "
                            f"Set is_amo=True to queue an after-market order.")

    preview = {
        "instrument_token": instrument_token,
        "transaction_type": transaction_type,
        "order_type": order_type,
        "product": product,
        "quantity": quantity,
        "price": price,
        "is_amo": is_amo,
        "estimated_notional": f"₹{notional:,.2f}" if notional else "market price",
    }
    return _result(not errors, errors, warnings, preview)


def _result(valid, errors, warnings, preview):
    return {"valid": valid, "errors": errors, "warnings": warnings, "order_preview": preview}


def print_validation_result(result):
    print("\n" + "=" * 52)
    print("ORDER PREVIEW")
    print("=" * 52)
    for k, v in result["order_preview"].items():
        print(f"  {k:<22}: {v}")
    for w in result["warnings"]:
        print(f"  [warn] {w}")
    for e in result["errors"]:
        print(f"  [ERROR] {e}")
    print("-" * 52)
    print("PASSED — confirm with the user before placing." if result["valid"]
          else "FAILED — fix errors before placing.")
    print("=" * 52 + "\n")


if __name__ == "__main__":
    print_validation_result(validate_order(
        instrument_token="NSE_EQ|INE002A01018",
        transaction_type="BUY", order_type="LIMIT", product="D",
        quantity=10, price=2500.0, is_amo=False,
    ))
