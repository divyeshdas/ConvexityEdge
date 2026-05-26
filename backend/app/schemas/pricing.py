from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional


class GreeksOut(BaseModel):
    delta: float
    gamma: float
    vega:  float
    theta: float
    rho:   float


class BSPricingRequest(BaseModel):
    S:           float = Field(..., gt=0, description="Underlying spot price")
    K:           float = Field(..., gt=0, description="Strike price")
    T:           float = Field(..., gt=0, description="Time to expiry in years")
    r:           float = Field(..., description="Risk-free rate (e.g. 0.05)")
    q:           float = Field(0.0, description="Continuous dividend yield")
    sigma:       float = Field(..., gt=0, le=10.0, description="Volatility (e.g. 0.30)")
    option_type: Literal["C", "P"]

    @field_validator("option_type")
    @classmethod
    def upper_type(cls, v):
        return v.upper()


class BSPricingResult(BaseModel):
    price:           float
    intrinsic_value: float
    time_value:      float
    d1:              float
    d2:              float
    greeks:          GreeksOut


class BatchPricingRequest(BaseModel):
    contracts: list[BSPricingRequest] = Field(..., min_length=1, max_length=50000)


class BatchPricingResult(BaseModel):
    prices: list[float]
    count:  int
    elapsed_ms: float


class IVSolveRequest(BaseModel):
    market_price: float = Field(..., gt=0)
    S:            float = Field(..., gt=0)
    K:            float = Field(..., gt=0)
    T:            float = Field(..., gt=0)
    r:            float
    q:            float = 0.0
    option_type:  Literal["C", "P"]

    @field_validator("option_type")
    @classmethod
    def upper_type(cls, v):
        return v.upper()


class IVSolveResult(BaseModel):
    iv:         Optional[float]
    converged:  bool
    iterations: int
    method:     str
    error:      Optional[str] = None
