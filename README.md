# Upstox Agent Skills

**Upstox-native agent skill for NSE/BSE equities, F&O, and MCX commodity trading.**

Give your AI agent the ability to place live orders, read portfolio data, stream market feeds, and access the full Indian market universe — all through the [Upstox Developer API v2](https://upstox.com/developer/api-documentation/).

Built for the [Agent Skills open standard](https://agentskills.io) and compatible with **Claude Code**, **Codex**, and any agent that supports SKILL.md.

---

## Installation

### Global install
```bash
npm install -g skills
skills add upstox/upstox-skills --skill upstox
```

### Claude Code or Codex
```bash
npx skills add upstox/upstox-skills --skill upstox
```

> Replace `upstox/upstox-skills` with your fork's `owner/repo` until this is published.

---

## Requirements

- Python 3.8+
- `pip install upstox-python-sdk pandas requests pytz`
- An Upstox developer account with API key + secret ([developer portal](https://account.upstox.com/developer/apps))
- Credentials via environment variables:
  ```bash
  export UPSTOX_ACCESS_TOKEN="your-daily-token"
  export UPSTOX_API_KEY="your-api-key"          # for token generation
  export UPSTOX_API_SECRET="your-api-secret"    # for token generation
  export UPSTOX_REDIRECT_URI="your-redirect"    # for token generation
  ```

---

## What's Included

```
skills/upstox/
├── SKILL.md                          # Entry point — setup, v2/v3 guide, safety, core patterns
│
├── references/                       # Deep-dive docs loaded on demand
│   ├── auth.md                       # OAuth 2.0 flow, daily token generation, TOTP
│   ├── orders.md                     # Place/modify/cancel (v3), multi-order, exit, AMO
│   ├── gtt-orders.md                 # Good-till-triggered single & multi-leg (OrderApiV3)
│   ├── portfolio.md                  # Holdings, positions, conversion, realised P&L
│   ├── market-data.md                # LTP/OHLC/quotes (v3), historical candles, status
│   ├── option-chain.md               # Put-call chain, Greeks, PCR, max pain
│   ├── margins.md                    # Funds, required margin, brokerage charges
│   ├── instruments.md                # Instrument master, symbol resolution, lot sizes
│   ├── websocket.md                  # MarketDataStreamerV3 + PortfolioDataStreamer
│   └── errors.md                     # Error codes, rate limits, retry patterns
│
├── scripts/
│   ├── upstox_helpers.py             # get_client() factory (env / sandbox) + helpers
│   ├── resolve_instrument.py         # Human name → instrument_key resolver
│   └── validate_order.py             # Pre-flight order validation with guardrails
│
└── examples/
    ├── place_equity_order.py          # Equity order with validation + confirmation
    ├── place_gtt_order.py             # Single-leg GTT trigger order
    ├── portfolio_summary.py           # Holdings + positions + funds dashboard
    ├── historical_candles.py          # v3 historical candles + quick stats
    └── option_chain_analysis.py       # ATM options, PCR, max pain for Nifty
```

> **Accuracy note:** every SDK class, method, request model, field, enum, and
> instrument-file URL in this skill is verified against the
> [official upstox-python SDK source](https://github.com/upstox/upstox-python).
> The most important rule is the **v2 vs v3 split** — see `SKILL.md`.

---

## Built-In Safety Guardrails

| Rule | What it does |
|------|-------------|
| **Confirmation required** | Shows full order preview; requires explicit `yes` before placing |
| **Default to LIMIT** | Never places MARKET orders unless user explicitly requests |
| **Default to 1 unit** | Uses 1 share / 1 lot when quantity not specified |
| **Lot size validation** | Rejects F&O orders where quantity isn't a lot-size multiple |
| **Notional value warning** | Warns when order value exceeds ₹50,000 |
| **Product-segment guard** | Validates CNC/MIS/CO against exchange segment |
| **Market hours check** | Warns if market is closed, suggests AMO |
| **No hardcoded secrets** | Always uses environment variables |

---

## Example Prompts

**Orders**
- "Buy 5 shares of TCS at 3900"
- "Place an intraday sell for HDFC Bank at market"
- "Set a GTT to buy Infosys if it drops to 1400"
- "Cancel my pending Reliance order"
- "Exit all my F&O positions"

**Portfolio**
- "Show my holdings and P&L"
- "List my open positions"
- "What's my available margin?"
- "Convert my INFY intraday position to delivery"

**Market Data**
- "Get 30-minute candles for TCS for the past week"
- "What's the current price of Bank Nifty?"
- "Show the full market depth for Reliance"

**Options**
- "Show the Nifty 50 option chain for this Thursday's expiry"
- "What's the PCR for Bank Nifty?"
- "Find the ATM options for Nifty"
- "Calculate max pain for Nifty"

---

## SDK Reference

- **PyPI**: `upstox-python-sdk`
- **Base URL**: `https://api.upstox.com/v2`
- **API Docs**: https://upstox.com/developer/api-documentation/
- **Sandbox**: https://upstox.com/developer/api-documentation/sandbox
- **Community**: https://community.upstox.com/c/developer-api

---

## License

MIT
