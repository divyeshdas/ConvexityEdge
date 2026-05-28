from fastapi import APIRouter
from app.schemas.trade import TradeAnalysisRequest, TradeAnalysisResult
from app.services.trade_service import run_trade_analysis

router = APIRouter(prefix="/trade", tags=["trade"])


@router.post("/analyze", response_model=TradeAnalysisResult)
async def analyze_trade(req: TradeAnalysisRequest):
    return await run_trade_analysis(req.model_dump())
