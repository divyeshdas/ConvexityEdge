from sqlalchemy import Column, BigInteger, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class OptionChainSnapshot(Base):
    __tablename__ = "option_chain_snapshots"

    id               = Column(BigInteger, primary_key=True)
    contract_id      = Column(Integer, ForeignKey("option_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_time    = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    underlying_price = Column(Numeric(12, 4))
    bid              = Column(Numeric(12, 4))
    ask              = Column(Numeric(12, 4))
    last_price       = Column(Numeric(12, 4))
    volume           = Column(Integer, default=0)
    open_interest    = Column(Integer, default=0)
    implied_vol      = Column(Numeric(8, 6))
    delta            = Column(Numeric(8, 6))
    gamma            = Column(Numeric(10, 8))
    vega             = Column(Numeric(10, 6))
    theta            = Column(Numeric(10, 6))
    rho              = Column(Numeric(10, 6))
    iv_change_1d     = Column(Numeric(8, 6))

    contract = relationship("OptionContract", back_populates="snapshots")
