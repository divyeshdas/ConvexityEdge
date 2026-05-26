from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class TradeAnalysisResult(Base):
    __tablename__ = "trade_analysis_results"

    id          = Column(Integer, primary_key=True)
    symbol      = Column(String(20), nullable=False, index=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    params      = Column(JSONB, nullable=False)
    results     = Column(JSONB, nullable=False)
