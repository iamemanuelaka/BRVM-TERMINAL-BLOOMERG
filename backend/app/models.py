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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """Public profile for traders."""
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    display_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(500))
    is_public = Column(Boolean, default=True)
    composite_score = Column(Float, default=0.0)
    total_predictions = Column(Integer, default=0)
    hit_rate = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class APIKey(Base):
    """API keys for bot traders."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="api_keys")


class Ticker(Base):
    """BRVM ticker/stock model."""
    __tablename__ = "tickers"

    symbol = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    sector = Column(String(100))
    country = Column(String(50))
    currency = Column(String(10), default="XOF")
    is_active = Column(Boolean, default=True)

    predictions = relationship("Prediction", back_populates="ticker_obj")


class OHLCV(Base):
    """OHLCV data model."""
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
    """Trader prediction model."""
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    author_name = Column(String(100), nullable=False)
    symbol = Column(String(20), ForeignKey("tickers.symbol"), nullable=False)
    direction = Column(String(10), nullable=False)
    current_price = Column(Float)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    confidence = Column(Integer)
    horizon_days = Column(Integer, nullable=False)
    thesis = Column(Text)
    tags = Column(ARRAY(String), default=[])
    status = Column(String(20), default="active")

    # Scoring fields
    actual_price = Column(Float)
    pct_error = Column(Float)
    hit_target = Column(Boolean)
    pnl_pct = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    scored_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="predictions")
    ticker_obj = relationship("Ticker")


class Trade(Base):
    """User trade journal entry."""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    side = Column(String(5), nullable=False)  # BUY / SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0)
    strategy = Column(String(100))
    emotion = Column(String(50))
    notes = Column(Text)
    traded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="trades")
