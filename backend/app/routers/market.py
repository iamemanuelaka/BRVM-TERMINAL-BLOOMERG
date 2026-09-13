"""Market data endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import Ticker, OHLCV
from ..schemas import TickerWithQuote, OHLCVItem
from typing import List

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/tickers", response_model=List[TickerWithQuote])
def list_tickers(db: Session = Depends(get_db)):
    """List all BRVM tickers with their latest quotes."""
    tickers = db.query(Ticker).filter(Ticker.is_active == True).all()
    result = []

    for t in tickers:
        last_2 = db.query(OHLCV).filter(OHLCV.symbol == t.symbol)\
            .order_by(desc(OHLCV.date)).limit(2).all()

        price = last_2[0].close if last_2 else None
        change = None
        if len(last_2) == 2 and last_2[1].close:
            change = ((last_2[0].close - last_2[1].close) / last_2[1].close) * 100

        result.append(TickerWithQuote(
            symbol=t.symbol,
            name=t.name,
            sector=t.sector,
            country=t.country,
            price=price,
            change_pct=round(change, 2) if change else None,
            volume=last_2[0].volume if last_2 else None
        ))

    return result


@router.get("/{symbol}/ohlcv", response_model=List[OHLCVItem])
def get_ohlcv(
    symbol: str,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get OHLCV data for a specific ticker (for Lightweight Charts)."""
    rows = db.query(OHLCV).filter(OHLCV.symbol == symbol.upper())\
        .order_by(OHLCV.date.desc()).limit(limit).all()

    return [
        OHLCVItem(
            time=r.date.strftime("%Y-%m-%d"),
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            volume=r.volume or 0
        ) for r in reversed(rows)
    ]


@router.get("/search")
def search_tickers(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search tickers by symbol or name."""
    q = q.upper()
    results = db.query(Ticker).filter(
        (Ticker.symbol.ilike(f"%{q}%")) | (Ticker.name.ilike(f"%{q}%"))
    ).limit(10).all()

    return [{"symbol": t.symbol, "name": t.name} for t in results]
