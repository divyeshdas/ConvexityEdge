from pydantic import BaseModel, Field
from typing import Literal, Optional


class TradeAnalysisRequest(BaseModel):
    symbol:          str
    entry_price:     float = Field(..., gt=0)
    implied_vol:     float = Field(..., gt=0, le=10.0, description="As decimal, e.g. 0.42")
    expiry:          str
    preset_levels:   int   = Field(..., ge=1, le=100)
    initial_size:    int   = Field(..., ge=1)
    subsequent_size: int   = Field(..., ge=1)
    vol_floor:       Literal["daily", "weekly", "monthly"]


class TradeAnalysisResult(BaseModel):
    floor_value:          float
    max_cash_allocation:  float
    profit_per_level:     float
    all_level_profit:     float
    expected_move:        float
    risk_reward:          float
    floor_pct:            float
    expected_move_pct:    float
