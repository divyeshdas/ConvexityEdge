"""
Dashboard aggregation: IV rank, PCR, top strikes, Greeks exposure.
"""

import numpy as np
from typing import Optional


def compute_dashboard_analytics(
    contracts: list[dict],
    underlying: float,
    iv_history: Optional[list[float]] = None,
    hist_vol: Optional[float] = None,
) -> dict:
    """
    Aggregate a full enriched option chain into dashboard metrics.

    contracts: list of enriched contract dicts from pipeline.enrich_chain()
    """
    calls = [c for c in contracts if c["option_type"] == "C"]
    puts  = [c for c in contracts if c["option_type"] == "P"]

    # ── Volume & OI ────────────────────────────────────────────────────────
    total_call_vol = sum(c["volume"] or 0 for c in calls)
    total_put_vol  = sum(c["volume"] or 0 for c in puts)
    total_call_oi  = sum(c["open_interest"] or 0 for c in calls)
    total_put_oi   = sum(c["open_interest"] or 0 for c in puts)

    pcr_volume = round(total_put_vol / total_call_vol, 4) if total_call_vol else 0.0
    pcr_oi     = round(total_put_oi  / total_call_oi,  4) if total_call_oi  else 0.0

    # ── ATM IV ─────────────────────────────────────────────────────────────
    valid_ivs = [(c["strike"], c["implied_vol"]) for c in contracts if c["implied_vol"]]
    atm_iv = None
    if valid_ivs:
        atm_strike, atm_iv_val = min(valid_ivs, key=lambda x: abs(x[0] - underlying))
        atm_iv = round(atm_iv_val, 6)

    # ── IV Rank ────────────────────────────────────────────────────────────
    iv_rank = None
    if atm_iv and iv_history:
        hist = [v for v in iv_history if v and v > 0]
        if len(hist) >= 5:
            iv_min, iv_max = min(hist), max(hist)
            if iv_max > iv_min:
                iv_rank = round((atm_iv - iv_min) / (iv_max - iv_min) * 100, 1)

    # ── Top volume strikes ─────────────────────────────────────────────────
    top_vol_calls = sorted(calls, key=lambda x: x["volume"] or 0, reverse=True)[:5]
    top_vol_puts  = sorted(puts,  key=lambda x: x["volume"] or 0, reverse=True)[:5]
    top_oi_calls  = sorted(calls, key=lambda x: x["open_interest"] or 0, reverse=True)[:5]
    top_oi_puts   = sorted(puts,  key=lambda x: x["open_interest"] or 0, reverse=True)[:5]

    # ── Greeks exposure (net across all contracts with OI > 0) ─────────────
    def net_greek(cs, key):
        vals = []
        for c in cs:
            if c.get("greeks") and (c["open_interest"] or 0) > 0:
                v = c["greeks"].get(key, 0) or 0
                sign = 1 if c["option_type"] == "C" else 1
                vals.append(v * (c["open_interest"] or 0) * sign)
        return round(sum(vals), 4) if vals else 0.0

    return {
        "atm_iv":       atm_iv,
        "iv_rank":      iv_rank,
        "hist_vol_30d": round(hist_vol, 6) if hist_vol else None,
        "iv_hv_spread": round(atm_iv - hist_vol, 6) if (atm_iv and hist_vol) else None,
        "pcr_volume":   pcr_volume,
        "pcr_oi":       pcr_oi,
        "total_volume": total_call_vol + total_put_vol,
        "top_volume_calls": [{"strike": c["strike"], "volume": c["volume"]} for c in top_vol_calls],
        "top_volume_puts":  [{"strike": c["strike"], "volume": c["volume"]} for c in top_vol_puts],
        "top_oi_calls":     [{"strike": c["strike"], "oi": c["open_interest"]} for c in top_oi_calls],
        "top_oi_puts":      [{"strike": c["strike"], "oi": c["open_interest"]} for c in top_oi_puts],
        "greeks_exposure": {
            "net_delta": net_greek(contracts, "delta"),
            "net_gamma": net_greek(contracts, "gamma"),
            "net_vega":  net_greek(contracts, "vega"),
            "net_theta": net_greek(contracts, "theta"),
        },
    }
