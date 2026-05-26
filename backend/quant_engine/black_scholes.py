"""
Vectorized Black-Scholes pricing engine.

All functions accept both scalar and NumPy array inputs. Arrays enable
pricing 10,000+ contracts in a single vectorized call — no Python loops.
"""

import numpy as np
from scipy.stats import norm
from typing import Union

ArrayLike = Union[float, np.ndarray]


def _d1_d2(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike,
    sigma: ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute d1 and d2 — the core Black-Scholes intermediate values.

    d1 = [ln(S/K) + (r - q + σ²/2)·T] / (σ·√T)
    d2 = d1 − σ·√T
    """
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    r = np.asarray(r, dtype=float)
    q = np.asarray(q, dtype=float)
    sigma = np.asarray(sigma, dtype=float)

    sqrt_T = np.sqrt(np.maximum(T, 1e-10))
    sigma_safe = np.maximum(sigma, 1e-10)

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma_safe ** 2) * T) / (sigma_safe * sqrt_T)
    d2 = d1 - sigma_safe * sqrt_T
    return d1, d2


def bs_price(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike,
    sigma: ArrayLike,
    option_type: Union[str, np.ndarray],
) -> np.ndarray:
    """
    Black-Scholes European option price.

    Parameters
    ----------
    S            : Underlying spot price
    K            : Strike price
    T            : Time to expiry in years (e.g. 30 days = 30/365)
    r            : Risk-free rate (continuous compounding, e.g. 0.05)
    q            : Continuous dividend yield (0 if none)
    sigma        : Volatility (e.g. 0.30 = 30%)
    option_type  : 'C' for call, 'P' for put (scalar or array of chars)

    Returns
    -------
    Option price(s) as float or ndarray
    """
    S     = np.asarray(S,     dtype=float)
    K     = np.asarray(K,     dtype=float)
    T     = np.asarray(T,     dtype=float)
    r     = np.asarray(r,     dtype=float)
    q     = np.asarray(q,     dtype=float)
    sigma = np.asarray(sigma, dtype=float)

    d1, d2 = _d1_d2(S, K, T, r, q, sigma)

    call = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    put  = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

    if isinstance(option_type, str):
        return call if option_type.upper() == 'C' else put

    opt = np.where(np.array(option_type) == 'C', call, put)
    return np.maximum(opt, 0.0)


def bs_price_with_decomposition(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    option_type: str,
) -> dict:
    """
    Full pricing result including intrinsic value, time value, and d1/d2.
    Always scalar — used for single-contract pricing API endpoint.
    """
    T = max(T, 1e-10)
    d1, d2 = _d1_d2(S, K, T, r, q, sigma)
    d1, d2 = float(d1), float(d2)

    price = float(bs_price(S, K, T, r, q, sigma, option_type))

    if option_type.upper() == 'C':
        intrinsic = max(S - K, 0.0)
    else:
        intrinsic = max(K - S, 0.0)

    time_value = max(price - intrinsic, 0.0)

    return {
        "price":           round(price, 4),
        "intrinsic_value": round(intrinsic, 4),
        "time_value":      round(time_value, 4),
        "d1":              round(d1, 6),
        "d2":              round(d2, 6),
    }


def bs_price_batch(contracts: list[dict]) -> list[float]:
    """
    Vectorized batch pricing for a list of contract dicts.
    Each dict: {S, K, T, r, q, sigma, option_type}
    Handles 10,000+ contracts in under 2 seconds.
    """
    if not contracts:
        return []

    S     = np.array([c["S"]     for c in contracts], dtype=float)
    K     = np.array([c["K"]     for c in contracts], dtype=float)
    T     = np.array([c["T"]     for c in contracts], dtype=float)
    r     = np.array([c["r"]     for c in contracts], dtype=float)
    q     = np.array([c.get("q", 0.0) for c in contracts], dtype=float)
    sigma = np.array([c["sigma"] for c in contracts], dtype=float)
    types = np.array([c["option_type"] for c in contracts])

    prices = bs_price(S, K, T, r, q, sigma, types)
    return prices.tolist()
