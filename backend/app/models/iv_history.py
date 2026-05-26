from sqlalchemy import Column, BigInteger, Integer, String, Numeric, Date, DateTime, ForeignKey, func
from app.core.database import Base


class IVHistory(Base):
    __tablename__ = "iv_history"

    id               = Column(BigInteger, primary_key=True)
    symbol_id        = Column(Integer, ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False, index=True)
    expiry           = Column(Date, nullable=False)
    strike           = Column(Numeric(12, 4), nullable=False)
    option_type      = Column(String(1), nullable=False)
    recorded_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    implied_vol      = Column(Numeric(8, 6))
    underlying_price = Column(Numeric(12, 4))
