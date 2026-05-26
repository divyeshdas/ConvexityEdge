from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class StrategyDefinition(Base):
    __tablename__ = "strategy_definitions"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    legs = relationship("StrategyLeg", back_populates="strategy_def", lazy="select")


class StrategyLeg(Base):
    __tablename__ = "strategy_legs"

    id              = Column(Integer, primary_key=True)
    strategy_def_id = Column(Integer, ForeignKey("strategy_definitions.id", ondelete="SET NULL"), nullable=True)
    session_id      = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)
    option_type     = Column(String(1))
    strike          = Column(Numeric(12, 4))
    expiry          = Column(Date)
    action          = Column(String(4))
    quantity        = Column(Integer, default=1)
    premium         = Column(Numeric(12, 4))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    strategy_def = relationship("StrategyDefinition", back_populates="legs")
