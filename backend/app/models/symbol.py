from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Symbol(Base):
    __tablename__ = "symbols"

    id         = Column(Integer, primary_key=True)
    ticker     = Column(String(20), unique=True, nullable=False, index=True)
    name       = Column(String(200))
    exchange   = Column(String(20))
    asset_type = Column(String(20), default="equity")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contracts = relationship("OptionContract", back_populates="symbol", lazy="select")
