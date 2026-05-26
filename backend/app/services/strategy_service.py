from analytics.strategy_builder import (
    STRATEGY_TEMPLATES, build_strategy_legs, calculate_payoff
)


async def get_templates() -> list[dict]:
    return [{"name": k, "description": v["description"]} for k, v in STRATEGY_TEMPLATES.items()]


async def build_strategy(strategy_name: str, symbol: str, expiry: str, underlying_price: float) -> dict:
    legs = build_strategy_legs(strategy_name, underlying_price, expiry)
    return {"legs": legs}


async def compute_payoff(legs: list[dict], price_range=None) -> dict:
    return calculate_payoff(legs, price_range)
