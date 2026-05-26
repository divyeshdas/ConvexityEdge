from pydantic import BaseModel, Field
from typing import Optional, Literal


class StrategyLegIn(BaseModel):
    option_type: Literal["C", "P"]
    strike:      float = Field(..., gt=0)
    expiry:      str
    action:      Literal["BUY", "SELL"]
    quantity:    int   = Field(1, ge=1)
    premium:     float = Field(..., ge=0)


class PayoffPoint(BaseModel):
    price: float
    pnl:   float


class StrategyBuildRequest(BaseModel):
    strategy_name:    str
    symbol:           str
    expiry:           str
    underlying_price: float = Field(..., gt=0)


class StrategyPayoffRequest(BaseModel):
    legs:        list[StrategyLegIn] = Field(..., min_length=1)
    price_range: Optional[list[float]] = None


class StrategyResult(BaseModel):
    net_premium:   float
    max_profit:    Optional[float]
    max_loss:      Optional[float]
    break_evens:   list[float]
    risk_reward:   Optional[float]
    expected_move: float
    payoff_curve:  list[PayoffPoint]


class StrategyTemplate(BaseModel):
    name:        str
    description: str
