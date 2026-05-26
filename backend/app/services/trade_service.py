from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trade_result import TradeAnalysisResult
from analytics.trade_analysis import analyze_trade


async def run_trade_analysis(db: AsyncSession, params: dict) -> dict:
    result = analyze_trade(
        entry_price=params["entry_price"],
        implied_vol=params["implied_vol"],
        expiry=params["expiry"],
        preset_levels=params["preset_levels"],
        initial_size=params["initial_size"],
        subsequent_size=params["subsequent_size"],
        vol_floor=params["vol_floor"],
    )

    record = TradeAnalysisResult(
        symbol=params["symbol"],
        params=params,
        results=result,
    )
    db.add(record)
    return result
