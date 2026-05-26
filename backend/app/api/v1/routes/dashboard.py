from fastapi import APIRouter
from app.services.dashboard_service import get_dashboard_analytics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/analytics/{symbol}")
async def analytics(symbol: str):
    return await get_dashboard_analytics(symbol.upper())
