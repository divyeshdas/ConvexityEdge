from fastapi import APIRouter, Query, HTTPException
from app.services.options_service import get_option_chain, get_expiries

router = APIRouter(prefix="/options", tags=["options"])


@router.get("/expiries/{symbol}")
async def list_expiries(symbol: str):
    return await get_expiries(symbol.upper())


@router.get("/chain/{symbol}")
async def fetch_chain(
    symbol:  str,
    expiry:  str   = Query(...),
    strikes: int   = Query(30, ge=4, le=100),
):
    chain = await get_option_chain(symbol.upper(), expiry, strikes)
    if not chain:
        raise HTTPException(status_code=404, detail=f"No chain found for {symbol} / {expiry}")
    return chain
