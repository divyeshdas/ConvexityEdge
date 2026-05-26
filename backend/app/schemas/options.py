from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.pricing import GreeksOut


class OptionLegOut(BaseModel):
    option_type:   str
    strike:        float
    expiry:        str
    bid:           float
    ask:           float
    last:          float
    volume:        int
    open_interest: int
    implied_vol:   Optional[float]
    iv_change_1d:  Optional[float]
    greeks:        GreeksOut
    in_the_money:  bool


class ChainStrikeOut(BaseModel):
    strike:  float
    call:    Optional[OptionLegOut]
    put:     Optional[OptionLegOut]
    is_atm:  bool


class ChainStatsOut(BaseModel):
    atm_iv:          Optional[float]
    hist_vol_30d:    Optional[float]
    pcr_volume:      float
    pcr_oi:          float
    total_call_vol:  int
    total_put_vol:   int
    total_call_oi:   int
    total_put_oi:    int
    iv_change_avg:   Optional[float]


class OptionChainOut(BaseModel):
    symbol:     str
    expiry:     str
    dte:        int
    underlying: float
    strikes:    list[ChainStrikeOut]
    stats:      ChainStatsOut
    fetched_at: str


class ExpiryOut(BaseModel):
    date:  str
    dte:   int
    label: str
