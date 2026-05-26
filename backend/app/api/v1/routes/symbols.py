from fastapi import APIRouter, Query
from data.pipeline import get_provider

router = APIRouter(prefix="/symbols", tags=["symbols"])


@router.get("/search")
async def search_symbols(q: str = Query(..., min_length=1)):
    provider = get_provider()
    return await provider.search_symbols(q)
