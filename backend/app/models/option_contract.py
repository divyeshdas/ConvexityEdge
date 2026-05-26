from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class OptionContract(Base):
    __tablename__ = "option_contracts"
    __table_args__ = (
        UniqueConstraint("symbol_id", "option_type", "strike", "expiry"),
    )

    id          = Column(Integer, primary_key=True)
    symbol_id   = Column(Integer, ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False, index=True)
    option_type = Column(String(1), nullable=False)
    strike      = Column(Numeric(12, 4), nullable=False)
    expiry      = Column(Date, nullable=False, index=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    symbol    = relationship("Symbol", back_populates="contracts")
    snapshots = relationship("OptionChainSnapshot", back_populates="contract", lazy="select")
