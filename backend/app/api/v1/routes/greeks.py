from fastapi import APIRouter
from app.schemas.pricing import BSPricingRequest, GreeksOut
from quant_engine.greeks import greeks_scalar, greeks_batch

router = APIRouter(prefix="/greeks", tags=["greeks"])


@router.post("/calculate", response_model=GreeksOut)
async def calculate_greeks(req: BSPricingRequest):
    return greeks_scalar(req.S, req.K, req.T, req.r, req.q, req.sigma, req.option_type)


@router.post("/batch")
async def batch_greeks(contracts: list[BSPricingRequest]):
    return greeks_batch([c.model_dump() for c in contracts])
