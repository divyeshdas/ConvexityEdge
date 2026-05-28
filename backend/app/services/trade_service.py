from analytics.trade_analysis import analyze_trade


async def run_trade_analysis(params: dict) -> dict:
    return analyze_trade(
        entry_price=params["entry_price"],
        implied_vol=params["implied_vol"],
        expiry=params["expiry"],
        preset_levels=params["preset_levels"],
        initial_size=params["initial_size"],
        subsequent_size=params["subsequent_size"],
        vol_floor=params["vol_floor"],
    )
