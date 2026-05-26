# ConvexityEdge — Architecture Reference

## Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Frontend      | SvelteKit + TypeScript + Tailwind   |
| Charts        | Apache ECharts                      |
| Backend       | FastAPI (async Python)              |
| Quant Engine  | NumPy + SciPy + pandas              |
| Database      | PostgreSQL 16                       |
| Cache         | Redis 7                             |
| Data Source   | yfinance (pluggable)                |
| Infrastructure| Docker + Docker Compose             |

## Key Design Decisions

- **Quant engine is pure Python** — no web framework imports. Fully unit-testable in isolation.
- **Abstract data provider** — swap yfinance for live broker API by implementing `MarketDataProvider`.
- **Redis TTL = 60s** — matches market data refresh interval. Prevents re-computing identical BS calls.
- **PostgreSQL for history only** — live pricing is always computed fresh, not read from DB.
- **IST-aware theme** — frontend switches dark/light at 09:00 and 15:30 IST automatically.

## Performance Targets

| Metric                              | Target      |
|-------------------------------------|-------------|
| Price 10,000 contracts              | < 2 seconds |
| Calculate Greeks for full chain     | < 2 seconds |
| IV solver convergence               | < 10 iters  |
| Redis cache latency reduction       | > 70%       |
| Dashboard refresh after data loaded | < 1 second  |
| Market data refresh interval        | 60 seconds  |
