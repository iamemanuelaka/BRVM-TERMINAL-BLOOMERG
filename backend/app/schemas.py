"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from uuid import UUID


# ═══════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    user_id: Optional[str] = None


# ═══════════════════════════════════════════════════════
# PROFILE SCHEMAS
# ═══════════════════════════════════════════════════════
class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    is_public: Optional[bool] = None


class ProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    is_public: bool
    composite_score: float
    total_predictions: int
    hit_rate: float
    username: Optional[str] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════
# API KEY SCHEMAS
# ═══════════════════════════════════════════════════════
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyOut(BaseModel):
    id: UUID
    key: str
    name: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


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


class OHLCVItem(BaseModel):
    time: str
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
    user_id: UUID
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
