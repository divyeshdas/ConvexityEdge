"""
Options strategy payoff calculator.

For each strategy, defines legs (action, option_type, relative strike)
and then calculates payoff curve, break-evens, max P&L, and risk/reward.
"""

import numpy as np
import datetime
from typing import Optional

STRATEGY_TEMPLATES = {
    "Long Call":        {"description": "Buy a call. Bullish, limited risk, unlimited upside."},
    "Long Put":         {"description": "Buy a put. Bearish, limited risk."},
    "Covered Call":     {"description": "Hold stock, sell OTM call. Income strategy."},
    "Protective Put":   {"description": "Hold stock, buy OTM put. Downside insurance."},
    "Bull Call Spread": {"description": "Buy lower-strike call, sell higher-strike call."},
    "Bear Put Spread":  {"description": "Buy higher-strike put, sell lower-strike put."},
    "Straddle":         {"description": "Buy ATM call and put. Pure volatility play."},
    "Strangle":         {"description": "Buy OTM call and OTM put. Cheaper vol play."},
    "Iron Condor":      {"description": "Sell OTM strangle, buy further OTM strangle."},
}


def build_strategy_legs(
    strategy_name: str,
    underlying_price: float,
    expiry: str,
    atm_iv: float = 0.30,
) -> list[dict]:
    """
    Generate suggested leg parameters for a named strategy.
    Strikes are chosen relative to ATM based on standard conventions.
    Premiums are approximated using ATM IV (actual values come from chain).
    """
    S = underlying_price
    step = round(S * 0.025, 0)  # ~2.5% OTM increment
    step = max(step, 1.0)

    ATM = round(S / step) * step  # nearest round strike

    legs_map = {
        "Long Call": [
            {"option_type": "C", "strike": ATM, "action": "BUY", "quantity": 1},
        ],
        "Long Put": [
            {"option_type": "P", "strike": ATM, "action": "BUY", "quantity": 1},
        ],
        "Covered Call": [
            {"option_type": "C", "strike": ATM + step, "action": "SELL", "quantity": 1},
        ],
        "Protective Put": [
            {"option_type": "P", "strike": ATM - step, "action": "BUY", "quantity": 1},
        ],
        "Bull Call Spread": [
            {"option_type": "C", "strike": ATM,        "action": "BUY",  "quantity": 1},
            {"option_type": "C", "strike": ATM + step, "action": "SELL", "quantity": 1},
        ],
        "Bear Put Spread": [
            {"option_type": "P", "strike": ATM,        "action": "BUY",  "quantity": 1},
            {"option_type": "P", "strike": ATM - step, "action": "SELL", "quantity": 1},
        ],
        "Straddle": [
            {"option_type": "C", "strike": ATM, "action": "BUY", "quantity": 1},
            {"option_type": "P", "strike": ATM, "action": "BUY", "quantity": 1},
        ],
        "Strangle": [
            {"option_type": "C", "strike": ATM + step, "action": "BUY", "quantity": 1},
            {"option_type": "P", "strike": ATM - step, "action": "BUY", "quantity": 1},
        ],
        "Iron Condor": [
            {"option_type": "P", "strike": ATM - step*2, "action": "BUY",  "quantity": 1},
            {"option_type": "P", "strike": ATM - step,   "action": "SELL", "quantity": 1},
            {"option_type": "C", "strike": ATM + step,   "action": "SELL", "quantity": 1},
            {"option_type": "C", "strike": ATM + step*2, "action": "BUY",  "quantity": 1},
        ],
    }

    raw_legs = legs_map.get(strategy_name, legs_map["Long Call"])
    return [
        {**leg, "expiry": expiry, "premium": 0.0}  # premiums filled from chain
        for leg in raw_legs
    ]


def calculate_payoff(
    legs: list[dict],
    price_range: Optional[list[float]] = None,
    num_points: int = 200,
) -> dict:
    """
    Calculate strategy payoff curve and key metrics.

    legs: [{option_type, strike, expiry, action, quantity, premium}]
    price_range: [low, high] underlying price range for the curve
    """
    if not legs:
        return {}

    strikes = [leg["strike"] for leg in legs]
    premiums = [leg["premium"] for leg in legs]

    # Net premium: negative = debit, positive = credit
    net_premium = 0.0
    for leg in legs:
        sign = 1 if leg["action"] == "SELL" else -1
        net_premium += sign * leg["premium"] * leg["quantity"]

    # Price range: ±40% around median strike
    mid = np.median(strikes)
    if price_range and len(price_range) == 2:
        low, high = price_range
    else:
        low  = mid * 0.60
        high = mid * 1.40

    prices = np.linspace(low, high, num_points)

    # Payoff at expiry for each price
    pnl_arr = np.zeros(num_points)
    for leg in legs:
        K      = leg["strike"]
        prem   = leg["premium"]
        qty    = leg["quantity"]
        sign   = 1 if leg["action"] == "BUY" else -1
        otype  = leg["option_type"].upper()

        if otype == "C":
            intrinsic = np.maximum(prices - K, 0)
        else:
            intrinsic = np.maximum(K - prices, 0)

        pnl_arr += sign * (intrinsic - prem) * qty

    # Max profit / loss
    max_profit = float(np.max(pnl_arr))
    min_pnl    = float(np.min(pnl_arr))
    max_loss   = min_pnl if min_pnl < 0 else None

    # Break-even points: sign changes in pnl_arr
    break_evens = []
    for i in range(len(pnl_arr) - 1):
        if pnl_arr[i] * pnl_arr[i + 1] < 0:
            # Linear interpolation
            be = prices[i] + (prices[i + 1] - prices[i]) * (-pnl_arr[i]) / (pnl_arr[i + 1] - pnl_arr[i])
            break_evens.append(round(float(be), 2))

    # Risk/reward
    risk_reward = None
    if max_loss and max_loss < 0 and max_profit > 0:
        risk_reward = round(max_profit / abs(max_loss), 2)

    # Expected move approximation (1 SD move = IV * S * sqrt(T))
    # Use the lowest-DTE leg for T
    today = datetime.date.today()
    min_dte = 30  # fallback
    for leg in legs:
        try:
            exp = datetime.date.fromisoformat(leg["expiry"])
            dte = (exp - today).days
            min_dte = min(min_dte, max(dte, 1))
        except Exception:
            pass

    T = min_dte / 365.0
    avg_iv = 0.30  # placeholder — caller should pass IV from chain
    if "iv" in legs[0]:
        ivs = [leg["iv"] for leg in legs if "iv" in leg and leg["iv"]]
        avg_iv = float(np.mean(ivs)) if ivs else 0.30

    expected_move = round(mid * avg_iv * np.sqrt(T), 2)

    return {
        "net_premium":   round(net_premium, 4),
        "max_profit":    round(max_profit, 4) if max_profit < 1e9 else None,
        "max_loss":      round(max_loss, 4) if max_loss is not None else None,
        "break_evens":   break_evens,
        "risk_reward":   risk_reward,
        "expected_move": expected_move,
        "payoff_curve":  [
            {"price": round(float(prices[i]), 2), "pnl": round(float(pnl_arr[i]), 4)}
            for i in range(len(prices))
        ],
    }
