"""SQLAlchemy models for BRVM Terminal."""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from .database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="trader")  # trader, quant, admin
    api_key = Column(String(100), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    predictions = relationship("Prediction", back_populates="user")


class Ticker(Base):
    """BRVM ticker/stock model."""
    __tablename__ = "tickers"

    symbol = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    sector = Column(String(100))
    country = Column(String(50))  # CI, SN, BF, ML, etc.
    currency = Column(String(10), default="XOF")
    is_active = Column(Boolean, default=True)

    predictions = relationship("Prediction", back_populates="ticker_obj")


class OHLCV(Base):
    """OHLCV (Open, High, Low, Close, Volume) data model."""
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("tickers.symbol"), index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)


class Prediction(Base):
    """Trader/quant prediction model."""
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author_name = Column(String(100), nullable=False)
    symbol = Column(String(20), ForeignKey("tickers.symbol"), nullable=False)
    direction = Column(String(10), nullable=False)  # LONG / SHORT / NEUTRE
    current_price = Column(Float)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    confidence = Column(Integer)  # 0-100
    horizon_days = Column(Integer, nullable=False)
    thesis = Column(Text)
    tags = Column(ARRAY(String), default=[])
    status = Column(String(20), default="active")  # active, scored, cancelled

    # Scoring fields (filled automatically at expiration)
    actual_price = Column(Float)
    pct_error = Column(Float)
    hit_target = Column(Boolean)
    pnl_pct = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    scored_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="predictions")
    ticker_obj = relationship("Ticker")
