from fastapi import APIRouter
from app.schemas.strategy import (
    StrategyBuildRequest, StrategyPayoffRequest, StrategyResult, StrategyTemplate
)
from app.services.strategy_service import get_templates, build_strategy, compute_payoff

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/templates", response_model=list[StrategyTemplate])
async def list_templates():
    return await get_templates()


@router.post("/build")
async def build(req: StrategyBuildRequest):
    return await build_strategy(req.strategy_name, req.symbol, req.expiry, req.underlying_price)


@router.post("/payoff", response_model=StrategyResult)
async def payoff(req: StrategyPayoffRequest):
    legs = [leg.model_dump() for leg in req.legs]
    return await compute_payoff(legs, req.price_range)
