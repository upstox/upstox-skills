"""
place_equity_order.py — Place an equity order with validation + confirmation.

Usage:
    UPSTOX_ACCESS_TOKEN=xxx python place_equity_order.py
    # paper trade:
    UPSTOX_SANDBOX_ACCESS_TOKEN=xxx SANDBOX=1 python place_equity_order.py
"""

import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import upstox_client
from upstox_client.rest import ApiException
from scripts.upstox_helpers import get_client
from scripts.validate_order import validate_order, print_validation_result

# ── Order parameters ────────────────────────────────────────────────────────
INSTRUMENT_TOKEN = "NSE_EQ|INE002A01018"   # Reliance Industries
TRANSACTION_TYPE = "BUY"
ORDER_TYPE = "LIMIT"
PRODUCT = "D"                              # D = delivery / CNC
QUANTITY = 1
PRICE = 2500.0
SANDBOX = bool(os.environ.get("SANDBOX"))
# ────────────────────────────────────────────────────────────────────────────


def main():
    result = validate_order(
        instrument_token=INSTRUMENT_TOKEN, transaction_type=TRANSACTION_TYPE,
        order_type=ORDER_TYPE, product=PRODUCT, quantity=QUANTITY, price=PRICE,
    )
    print_validation_result(result)
    if not result["valid"]:
        return

    if input("Place this order? (yes/no): ").strip().lower() != "yes":
        print("Cancelled.")
        return

    order_api = upstox_client.OrderApiV3(get_client(sandbox=SANDBOX))
    body = upstox_client.PlaceOrderV3Request(
        quantity=QUANTITY, product=PRODUCT, validity="DAY", price=PRICE,
        tag="upstox-skill", instrument_token=INSTRUMENT_TOKEN,
        order_type=ORDER_TYPE, transaction_type=TRANSACTION_TYPE,
        disclosed_quantity=0, trigger_price=0.0, is_amo=False,
    )
    try:
        resp = order_api.place_order(body)          # v3: no api_version
        print("\nOrder placed. Order ID(s):", resp.data.order_ids)
    except ApiException as e:
        print("\nOrder failed:", e.body)


if __name__ == "__main__":
    main()
