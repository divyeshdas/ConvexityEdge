"""
Vectorized Black-Scholes Greeks engine.

All five Greeks calculated analytically (no finite-difference approximations).
Accepts scalar or NumPy array inputs for batch processing.
"""

import numpy as np
from scipy.stats import norm
from typing import Union
from quant_engine.black_scholes import _d1_d2

ArrayLike = Union[float, np.ndarray]

DAYS_IN_YEAR = 365.0


def calculate_greeks(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike,
    sigma: ArrayLike,
    option_type: Union[str, np.ndarray],
) -> dict:
    """
    Calculate all five Greeks for one or many option contracts.

    Returns a dict of arrays (or scalars if all inputs were scalar).

    Greeks conventions:
    - Delta  : rate of price change per $1 move in underlying
    - Gamma  : rate of delta change per $1 move in underlying
    - Vega   : price change per 1% move in vol (divided by 100)
    - Theta  : price decay per calendar day (divided by 365)
    - Rho    : price change per 1% move in risk-free rate (divided by 100)
    """
    S     = np.asarray(S,     dtype=float)
    K     = np.asarray(K,     dtype=float)
    T     = np.asarray(T,     dtype=float)
    r     = np.asarray(r,     dtype=float)
    q     = np.asarray(q,     dtype=float)
    sigma = np.asarray(sigma, dtype=float)

    T_safe = np.maximum(T, 1e-10)
    sqrt_T = np.sqrt(T_safe)

    d1, d2 = _d1_d2(S, K, T_safe, r, q, sigma)

    # Standard normal PDF at d1 — appears in Gamma, Vega, Theta
    nd1_pdf = norm.pdf(d1)

    exp_qT = np.exp(-q * T_safe)
    exp_rT = np.exp(-r * T_safe)

    # ── Delta ──────────────────────────────────────────────────────────────
    delta_call = exp_qT * norm.cdf(d1)
    delta_put  = exp_qT * (norm.cdf(d1) - 1.0)

    # ── Gamma (identical for calls and puts) ───────────────────────────────
    gamma = exp_qT * nd1_pdf / (S * np.maximum(sigma, 1e-10) * sqrt_T)

    # ── Vega (per 1% change in vol → divide raw vega by 100) ──────────────
    vega = S * exp_qT * nd1_pdf * sqrt_T / 100.0

    # ── Theta (per calendar day → divide by 365) ──────────────────────────
    sigma_safe = np.maximum(sigma, 1e-10)
    common_theta = -(S * sigma_safe * exp_qT * nd1_pdf) / (2.0 * sqrt_T)

    theta_call = (
        common_theta
        - r * K * exp_rT * norm.cdf(d2)
        + q * S * exp_qT * norm.cdf(d1)
    ) / DAYS_IN_YEAR

    theta_put = (
        common_theta
        + r * K * exp_rT * norm.cdf(-d2)
        - q * S * exp_qT * norm.cdf(-d1)
    ) / DAYS_IN_YEAR

    # ── Rho (per 1% change in rate → divide by 100) ───────────────────────
    rho_call =  K * T_safe * exp_rT * norm.cdf(d2)  / 100.0
    rho_put  = -K * T_safe * exp_rT * norm.cdf(-d2) / 100.0

    # ── Select call vs put ─────────────────────────────────────────────────
    if isinstance(option_type, str):
        is_call = option_type.upper() == 'C'
        delta = delta_call if is_call else delta_put
        theta = theta_call if is_call else theta_put
        rho   = rho_call   if is_call else rho_put
    else:
        mask  = np.array(option_type) == 'C'
        delta = np.where(mask, delta_call, delta_put)
        theta = np.where(mask, theta_call, theta_put)
        rho   = np.where(mask, rho_call,   rho_put)

    return {
        "delta": delta,
        "gamma": gamma,
        "vega":  vega,
        "theta": theta,
        "rho":   rho,
    }


def greeks_scalar(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    option_type: str,
) -> dict:
    """
    Return Greeks as plain Python floats (for single-contract API responses).
    Values rounded to match display precision of a trading terminal.
    """
    g = calculate_greeks(S, K, T, r, q, sigma, option_type)
    return {
        "delta": round(float(g["delta"]), 4),
        "gamma": round(float(g["gamma"]), 6),
        "vega":  round(float(g["vega"]),  4),
        "theta": round(float(g["theta"]), 4),
        "rho":   round(float(g["rho"]),   4),
    }


def greeks_batch(contracts: list[dict]) -> list[dict]:
    """
    Vectorized Greeks for a list of contract dicts.
    Each dict: {S, K, T, r, q, sigma, option_type}
    Returns list of {delta, gamma, vega, theta, rho} dicts.
    """
    if not contracts:
        return []

    S     = np.array([c["S"]            for c in contracts], dtype=float)
    K     = np.array([c["K"]            for c in contracts], dtype=float)
    T     = np.array([c["T"]            for c in contracts], dtype=float)
    r     = np.array([c["r"]            for c in contracts], dtype=float)
    q     = np.array([c.get("q", 0.0)  for c in contracts], dtype=float)
    sigma = np.array([c["sigma"]        for c in contracts], dtype=float)
    types = np.array([c["option_type"]  for c in contracts])

    g = calculate_greeks(S, K, T, r, q, sigma, types)

    return [
        {
            "delta": round(float(g["delta"][i]), 4),
            "gamma": round(float(g["gamma"][i]), 6),
            "vega":  round(float(g["vega"][i]),  4),
            "theta": round(float(g["theta"][i]), 4),
            "rho":   round(float(g["rho"][i]),   4),
        }
        for i in range(len(contracts))
    ]
