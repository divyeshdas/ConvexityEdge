from fastapi import APIRouter, Query
from app.schemas.pricing import IVSolveRequest, IVSolveResult
from app.services.iv_service import (
    solve_single_iv, get_iv_smile, get_iv_skew,
    get_iv_term_structure, get_iv_surface,
)

router = APIRouter(prefix="/iv", tags=["iv"])


@router.post("/solve", response_model=IVSolveResult)
async def solve_iv(req: IVSolveRequest):
    return await solve_single_iv(
        req.market_price, req.S, req.K, req.T, req.r, req.q, req.option_type
    )


@router.get("/smile/{symbol}")
async def iv_smile(symbol: str, expiry: str = Query(...)):
    return await get_iv_smile(symbol.upper(), expiry)


@router.get("/skew/{symbol}")
async def iv_skew(symbol: str, expiry: str = Query(...)):
    return await get_iv_skew(symbol.upper(), expiry)


@router.get("/term-structure/{symbol}")
async def iv_term_structure(symbol: str):
    return await get_iv_term_structure(symbol.upper())


@router.get("/surface/{symbol}")
async def iv_surface(symbol: str):
    return await get_iv_surface(symbol.upper())
