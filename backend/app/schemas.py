"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


# ═══════════════════════════════════════════════════════
# TICKER SCHEMAS
# ═══════════════════════════════════════════════════════
class TickerBase(BaseModel):
    symbol: str
    name: str
    sector: Optional[str] = None
    country: Optional[str] = None


class TickerWithQuote(TickerBase):
    price: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    cap_mrds: Optional[float] = None


# ═══════════════════════════════════════════════════════
# OHLCV SCHEMAS
# ═══════════════════════════════════════════════════════
class OHLCVItem(BaseModel):
    time: str  # Format YYYY-MM-DD for Lightweight Charts
    open: float
    high: float
    low: float
    close: float
    volume: int


# ═══════════════════════════════════════════════════════
# PREDICTION SCHEMAS
# ═══════════════════════════════════════════════════════
class PredictionCreate(BaseModel):
    author_name: str = Field(..., min_length=2, max_length=100)
    symbol: str
    direction: str = Field(..., pattern="^(LONG|SHORT|NEUTRE)$")
    current_price: Optional[float] = None
    target_price: float
    stop_loss: Optional[float] = None
    confidence: int = Field(..., ge=0, le=100)
    horizon_days: int = Field(..., ge=1, le=365)
    thesis: Optional[str] = None
    tags: List[str] = []


class PredictionOut(BaseModel):
    id: UUID
    author_name: str
    symbol: str
    direction: str
    current_price: Optional[float]
    target_price: float
    stop_loss: Optional[float]
    confidence: int
    horizon_days: int
    thesis: Optional[str]
    tags: List[str]
    status: str
    actual_price: Optional[float]
    pct_error: Optional[float]
    hit_target: Optional[bool]
    pnl_pct: Optional[float]
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
