from fastapi import APIRouter
from app.schemas.pricing import BSPricingRequest, BSPricingResult, BatchPricingRequest, BatchPricingResult
from app.services.pricing_service import price_single, price_batch

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/black-scholes", response_model=BSPricingResult)
async def black_scholes(req: BSPricingRequest):
    result = await price_single(req.S, req.K, req.T, req.r, req.q, req.sigma, req.option_type)
    return result


@router.post("/batch", response_model=BatchPricingResult)
async def batch_price(req: BatchPricingRequest):
    contracts = [c.model_dump() for c in req.contracts]
    return await price_batch(contracts)
