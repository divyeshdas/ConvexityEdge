"""
Trade analysis calculator — Grid/Scale order style.

Computes floor value, max cash allocation, profit per level,
and all-level profit based on volatility-driven price levels.
"""

import numpy as np
import datetime

VOL_FLOOR_PERIODS = {
    "daily":   1 / 252,
    "weekly":  5 / 252,
    "monthly": 21 / 252,
}


def compute_expected_move(
    price: float,
    iv: float,
    T_days: float,
) -> float:
    """
    Expected 1-standard-deviation move over T_days calendar days.
    Formula: S × IV × √(T/365)
    """
    return price * iv * np.sqrt(max(T_days, 1) / 365.0)


def analyze_trade(
    entry_price:     float,
    implied_vol:     float,
    expiry:          str,
    preset_levels:   int,
    initial_size:    int,
    subsequent_size: int,
    vol_floor:       str,
) -> dict:
    """
    Scale/grid trade analysis.

    Floor value    : entry_price × (1 - IV × √period)
                    The expected lower bound for the period based on 1 SD move.

    Max allocation : entry_price × total_contracts
                    total_contracts = initial_size + subsequent_size × (levels - 1)

    Profit/level   : (entry - floor) × subsequent_size
    All-level      : profit_per_level × levels
    """
    today = datetime.date.today()
    try:
        exp_date = datetime.date.fromisoformat(expiry)
        dte = max((exp_date - today).days, 1)
    except Exception:
        dte = 30

    period_fraction = VOL_FLOOR_PERIODS.get(vol_floor, VOL_FLOOR_PERIODS["monthly"])

    # Floor value: 1 SD downside move over the volatility period
    floor_value = entry_price * (1 - implied_vol * np.sqrt(period_fraction))
    floor_value = max(floor_value, 0.01)

    # Total contracts in the scale
    total_contracts = initial_size + subsequent_size * (preset_levels - 1)
    max_cash_allocation = entry_price * total_contracts

    # Profit per level if price recovers from floor to entry
    profit_per_level = (entry_price - floor_value) * subsequent_size
    all_level_profit  = profit_per_level * preset_levels

    # Expected move over full expiry DTE
    expected_move = compute_expected_move(entry_price, implied_vol, dte)

    # Risk/reward: expected profit vs max draw to floor
    max_draw = (entry_price - floor_value) * total_contracts
    risk_reward = round(all_level_profit / max_draw, 2) if max_draw > 0 else 0.0

    return {
        "floor_value":          round(float(floor_value), 2),
        "max_cash_allocation":  round(float(max_cash_allocation), 2),
        "profit_per_level":     round(float(profit_per_level), 2),
        "all_level_profit":     round(float(all_level_profit), 2),
        "expected_move":        round(float(expected_move), 2),
        "risk_reward":          risk_reward,
        "floor_pct":            round((1 - floor_value / entry_price) * 100, 2),
        "expected_move_pct":    round(expected_move / entry_price * 100, 2),
    }
