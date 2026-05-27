# ConvexityEdge

**Professional options volatility analytics platform for NSE F&O traders.**

Built on Black-Scholes theory — live implied volatility, Greeks, IV surface, strategy payoff diagrams, and trade analytics, all in one place.

**Live:** [convexity-edge.vercel.app](https://convexity-edge.vercel.app)

---

## Features

**Chain** — Full NSE options chain with real-time IV, Delta, Gamma, Vega, Theta, Rho for every strike. Filter by number of strikes, switch expiries, and view bid/ask spreads alongside Black-Scholes computed Greeks.

**Analytics** — Dashboard view per symbol showing ATM IV, put/call ratio, max pain strike, historical vs implied volatility, and IV percentile rank.

**Strategy** — Build multi-leg options strategies (spreads, straddles, butterflies, etc.) and visualise the payoff diagram at expiry.

**Trade** — Daily trend analysis, historical close prices, and trade result tracking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | SvelteKit 2, Svelte 5, TypeScript, Tailwind CSS |
| Charts | Apache ECharts 5, ECharts-GL |
| Backend | FastAPI, Python 3.12, Uvicorn |
| Quant Engine | NumPy, SciPy — Black-Scholes, Newton-Raphson IV solver, Brent fallback |
| Market Data | Angel One SmartAPI (NSE live data) |
| Database | PostgreSQL (SQLAlchemy async) |
| Cache | Redis |
| Deployment | Vercel (frontend) + Railway (backend, Docker) |

---

## Quant Engine

The IV solver uses a two-stage approach:

1. **Newton-Raphson** with a Brenner-Subrahmanyam (1988) warm-start guess — converges in 3–5 iterations for most options
2. **Brent's method** fallback — guaranteed convergence when vega is near zero or Newton-Raphson diverges

Greeks (Delta, Gamma, Vega, Theta, Rho) are computed in a vectorised NumPy batch across the full chain for performance. The IV surface is built from the enriched chain and can be visualised as a 3D mesh.

---

## Project Structure

```
ConvexityEdge/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route handlers
│   │   ├── core/            # Config, database, Redis
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # Business logic layer
│   ├── data/
│   │   ├── pipeline.py      # Background 60s refresh loop
│   │   └── providers/       # Angel One + yfinance data providers
│   ├── quant_engine/        # Black-Scholes, IV solver, Greeks, IV surface
│   ├── analytics/           # Dashboard analytics, strategy builder
│   └── Dockerfile
└── frontend/
    └── src/
        ├── lib/
        │   ├── api/          # Typed API client
        │   └── components/   # Reusable Svelte components
        └── routes/
            ├── chain/        # Options chain page
            ├── dashboard/    # Analytics dashboard
            ├── strategy/     # Strategy builder
            └── trade/        # Trade analysis
```

---

## Local Development

**Prerequisites:** Python 3.12, Node.js 20+, PostgreSQL, Redis

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in credentials
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173`.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `MARKET_DATA_PROVIDER` | `angel_one` or `yfinance` |
| `ANGEL_ONE_API_KEY` | SmartAPI key from Angel One developer portal |
| `ANGEL_ONE_CLIENT_CODE` | Angel One client ID |
| `ANGEL_ONE_PASSWORD` | 4-digit trading PIN |
| `ANGEL_ONE_TOTP_SECRET` | Base32 TOTP secret for 2FA |
| `RISK_FREE_RATE` | RBI repo rate, e.g. `0.065` |

---

## Deployment

- **Frontend** → Vercel. Set `VITE_API_BASE` to your Railway backend URL.
- **Backend** → Railway with Docker. Set the root directory to `backend/`. Railway injects `DATABASE_URL` and `REDIS_URL` automatically from linked plugins.
