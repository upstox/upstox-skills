# Authentication Reference

## OAuth 2.0 Flow

Upstox uses OAuth 2.0. Access tokens are valid for **one trading day** and must be regenerated each day before market opens.

### Step 1: Open Login URL

```
https://api.upstox.com/v2/login/authorization/dialog
  ?response_type=code
  &client_id=<YOUR_API_KEY>
  &redirect_uri=<YOUR_REDIRECT_URI>
  &state=<OPTIONAL_STATE>
```

Parameters:
- `client_id` — your API Key (not UCC/client id)
- `redirect_uri` — must exactly match what's registered in your app
- `response_type` — always `code`
- `state` — optional, returned as-is for CSRF protection

### Step 2: Receive Auth Code

After login, Upstox redirects to:
```
https://your-redirect-uri?code=<AUTH_CODE>&state=<STATE>
```

The auth code is **single-use** — if token generation fails, restart from Step 1.

### Step 3: Exchange Code for Access Token

```bash
curl -X POST https://api.upstox.com/v2/login/authorization/token \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'code=<AUTH_CODE>&client_id=<API_KEY>&client_secret=<API_SECRET>&redirect_uri=<REDIRECT_URI>&grant_type=authorization_code'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### Python SDK Auth

```python
import upstox_client, os

configuration = upstox_client.Configuration()
configuration.access_token = os.environ["UPSTOX_ACCESS_TOKEN"]
api_client = upstox_client.ApiClient(configuration)
```

---

## Semi-Automated Daily Token Script

For algo trading where you need a fresh token each morning:

```python
import os, requests, webbrowser
from urllib.parse import urlparse, parse_qs

API_KEY     = os.environ["UPSTOX_API_KEY"]
API_SECRET  = os.environ["UPSTOX_API_SECRET"]
REDIRECT_URI = os.environ["UPSTOX_REDIRECT_URI"]

def get_access_token():
    # Step 1: Open browser for user login
    login_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    )
    webbrowser.open(login_url)
    
    # Step 2: Paste redirect URL after login
    redirect_url = input("Paste the full redirect URL here: ").strip()
    code = parse_qs(urlparse(redirect_url).query)["code"][0]
    
    # Step 3: Exchange for token
    resp = requests.post(
        "https://api.upstox.com/v2/login/authorization/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code": code,
            "client_id": API_KEY,
            "client_secret": API_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    
    # Save for use
    os.environ["UPSTOX_ACCESS_TOKEN"] = token
    print(f"Token obtained: {token[:20]}...")
    return token
```

---

## TOTP (2FA)

Upstox supports TOTP for secure 2FA instead of SMS OTP. Enable it via Upstox app settings. With TOTP, you can automate daily login without SMS dependency.

---

## Important Notes

- `client_id` in OAuth = your **API Key** (not your Upstox UCC/client ID)
- `client_secret` = your **API Secret** — never expose in frontend code
- Redirect URIs with `.php` or script extensions may be blocked — use clean paths
- `Invalid Credentials` error = mismatch in `client_id`, `redirect_uri`, or `response_type` vs what's registered in the app
