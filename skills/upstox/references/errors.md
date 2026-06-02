# Errors & Rate Limits Reference

## Rate Limits

Upstox enforces per-second, per-minute, and per-30-minute limits that vary by
endpoint. Breaching any of them returns HTTP `429 Too Many Requests`. Treat these
as approximate and confirm current values in the
[official rate-limit docs](https://upstox.com/developer/api-documentation/):

| Window | Approx. limit (per endpoint) |
|--------|------------------------------|
| Per second | ~25–50 requests |
| Per minute | ~250–500 requests |
| Per 30 minutes | ~1000–2000 requests |

Order placement is throttled more tightly than read endpoints — batch with
`place_multi_order` and back off on `429`.

---

## Common HTTP Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `400` | Bad request / invalid params | Check request body, required fields |
| `401` | Unauthorized | Token expired or invalid — re-authenticate |
| `403` | Forbidden | API not enabled for your account, or IP not whitelisted |
| `404` | Resource not found | Wrong order_id, instrument key, etc. |
| `429` | Rate limit exceeded | Back off and retry with exponential delay |
| `500` | Upstox server error | Retry after brief wait |
| `503` | Service unavailable | Retry — may be market open/close spike |

---

## Common Error Messages

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `Invalid Credentials` | OAuth params mismatch | Verify `client_id`, `redirect_uri`, `response_type` match app registration |
| `Token Expired` | Access token > 1 day old | Re-run OAuth flow |
| `Invalid instrument key` | Wrong token format | Use `EXCHANGE\|TOKEN` format |
| `Order not modifiable` | Order already executed/cancelled | Check order status first |
| `Margin insufficient` | Not enough funds | Check margin, reduce qty or add funds |
| `Product not allowed` | Wrong product for segment | CNC only for EQ, MIS for intraday |
| `Quantity not multiple of lot size` | F&O qty validation failed | Use multiples of lot size |
| `Outside market hours` | Placing non-AMO order after hours | Set `is_amo=True` |

---

## Retry Pattern with Exponential Backoff

```python
import time, upstox_client
from upstox_client.rest import ApiException

def place_order_with_retry(order_v3, body, max_retries=3):
    for attempt in range(max_retries):
        try:
            return order_v3.place_order(body)      # OrderApiV3 — no api_version
        except ApiException as e:
            if e.status == 429:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"Rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
            elif e.status in (500, 503):
                wait = 2 ** attempt
                print(f"Server error {e.status}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise  # Don't retry 4xx errors other than 429
    raise RuntimeError(f"Failed after {max_retries} retries")
```

---

## Handling Token Expiry

Access tokens expire at end of each trading day. Detect and handle:

```python
def api_call_with_auth_retry(api_func, *args, **kwargs):
    try:
        return api_func(*args, **kwargs)
    except ApiException as e:
        if e.status == 401:
            print("Token expired. Please regenerate your access token.")
            print("Run: python get_token.py")
            raise SystemExit(1)
        raise
```

---

## Debug Mode

Enable verbose logging for troubleshooting:

```python
import upstox_client, logging

upstox_client.Configuration.debug = True
logging.basicConfig(level=logging.DEBUG)
```

---

## Upstox API Status

Check real-time API health: https://status.upstox.com
Community for issue reports: https://community.upstox.com/c/developer-api
