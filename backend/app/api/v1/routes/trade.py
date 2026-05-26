from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.trade import TradeAnalysisRequest, TradeAnalysisResult
from app.services.trade_service import run_trade_analysis
from app.core.database import get_db

router = APIRouter(prefix="/trade", tags=["trade"])


@router.post("/analyze", response_model=TradeAnalysisResult)
async def analyze_trade(req: TradeAnalysisRequest, db: AsyncSession = Depends(get_db)):
    return await run_trade_analysis(db, req.model_dump())
