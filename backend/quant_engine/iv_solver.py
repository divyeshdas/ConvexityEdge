"""
Implied Volatility solver.

Primary method  : Newton-Raphson (quadratic convergence, 3-5 iterations)
Fallback method : Brent's method (guaranteed convergence, ~20 iterations)

The fallback triggers when:
  - Vega is too small (near-zero denominator in Newton-Raphson)
  - Newton-Raphson diverges or exceeds max iterations
  - Market price is outside arbitrage bounds

Initial volatility guess uses the Brenner-Subrahmanyam (1988) approximation
which is close enough for Newton-Raphson to converge rapidly.
"""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm
from typing import Union
from quant_engine.black_scholes import bs_price, _d1_d2

MAX_ITER    = 100
TOLERANCE   = 1e-6
VEGA_FLOOR  = 1e-10
SIGMA_MIN   = 1e-6
SIGMA_MAX   = 10.0   # 1000% vol — hard ceiling


def _brenner_subrahmanyam_guess(market_price: float, S: float, T: float) -> float:
    """
    Approximation: σ ≈ √(2π/T) · (price/S)
    Accurate for near-ATM options. Gives Newton-Raphson a warm start.
    """
    T_safe = max(T, 1e-10)
    S_safe = max(S, 1e-10)
    return max(np.sqrt(2 * np.pi / T_safe) * (market_price / S_safe), 0.01)


def _bs_vega_raw(S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
    """Raw Vega (not divided by 100) — needed for Newton-Raphson denominator."""
    T_safe = max(T, 1e-10)
    sqrt_T = np.sqrt(T_safe)
    d1, _ = _d1_d2(S, K, T_safe, r, q, sigma)
    return float(S * np.exp(-q * T_safe) * norm.pdf(float(d1)) * sqrt_T)


def solve_iv_newton(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    option_type: str,
    max_iter: int = MAX_ITER,
    tol: float = TOLERANCE,
) -> dict:
    """
    Newton-Raphson IV solver.

    σ_{n+1} = σ_n − [BS(σ_n) − market_price] / Vega(σ_n)

    Returns dict with: iv, converged, iterations, method
    """
    T = max(T, 1e-10)

    # Arbitrage bounds check
    if option_type.upper() == 'C':
        lower = max(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0)
    else:
        lower = max(K * np.exp(-r * T) - S * np.exp(-q * T), 0.0)

    if market_price < lower - TOLERANCE:
        return {"iv": None, "converged": False, "iterations": 0, "method": "none",
                "error": "price below arbitrage lower bound"}

    sigma = _brenner_subrahmanyam_guess(market_price, S, T)
    sigma = max(min(sigma, SIGMA_MAX), SIGMA_MIN)

    for i in range(max_iter):
        price = float(bs_price(S, K, T, r, q, sigma, option_type))
        diff  = price - market_price

        if abs(diff) < tol:
            return {"iv": round(sigma, 8), "converged": True,
                    "iterations": i + 1, "method": "newton_raphson"}

        vega = _bs_vega_raw(S, K, T, r, q, sigma)

        if abs(vega) < VEGA_FLOOR:
            # Vega too small → fall through to Brent
            break

        sigma -= diff / vega
        sigma  = max(min(sigma, SIGMA_MAX), SIGMA_MIN)

    # Newton-Raphson did not converge → try Brent
    return _solve_brent(market_price, S, K, T, r, q, option_type, i + 1)


def _solve_brent(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    option_type: str,
    prior_iterations: int,
) -> dict:
    """Brent's method fallback — bracketed root-finding, always converges."""
    def objective(sigma: float) -> float:
        return float(bs_price(S, K, T, r, q, sigma, option_type)) - market_price

    try:
        # Check bracket validity
        f_lo = objective(SIGMA_MIN)
        f_hi = objective(SIGMA_MAX)

        if f_lo * f_hi > 0:
            return {"iv": None, "converged": False,
                    "iterations": prior_iterations, "method": "brent",
                    "error": "no bracket found"}

        iv = brentq(objective, SIGMA_MIN, SIGMA_MAX, xtol=TOLERANCE, maxiter=100)
        return {"iv": round(iv, 8), "converged": True,
                "iterations": prior_iterations, "method": "brent"}

    except Exception as e:
        return {"iv": None, "converged": False,
                "iterations": prior_iterations, "method": "brent",
                "error": str(e)}


def solve_iv(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    option_type: str,
) -> dict:
    """
    Public entry point. Always tries Newton-Raphson first, falls back to Brent.
    """
    return solve_iv_newton(market_price, S, K, T, r, q, option_type)


def solve_iv_batch(contracts: list[dict]) -> list[dict]:
    """
    Solve IV for a list of contracts. Cannot be fully vectorized because each
    Newton-Raphson iteration depends on the previous sigma estimate, so we
    use a fast Python loop — still hits performance targets for chain sizes.

    Each contract dict: {market_price, S, K, T, r, q, option_type}
    """
    return [
        solve_iv(
            c["market_price"],
            c["S"],
            c["K"],
            c["T"],
            c["r"],
            c.get("q", 0.0),
            c["option_type"],
        )
        for c in contracts
    ]
