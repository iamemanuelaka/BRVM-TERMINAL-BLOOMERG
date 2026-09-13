"""News endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..models import News, NewsTicker, NewsAlert, User
from ..schemas import NewsOut, NewsAlertCreate, NewsAlertOut
from ..routers.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("/", response_model=List[NewsOut])
def list_news(
    source: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Liste les news avec filtres."""
    q = db.query(News).options(joinedload(News.tickers))
    
    if source:
        q = q.filter(News.source == source)
    if sentiment:
        q = q.filter(News.sentiment == sentiment)
    if ticker:
        q = q.join(NewsTicker).filter(NewsTicker.symbol == ticker.upper())
    
    q = q.order_by(desc(News.published_at))
    news = q.offset(offset).limit(limit).all()
    
    # Convertir en schéma
    result = []
    for n in news:
        result.append(NewsOut(
            id=n.id,
            title=n.title,
            content=n.content,
            summary=n.summary,
            source=n.source,
            source_url=n.source_url,
            published_at=n.published_at,
            sentiment=n.sentiment,
            sentiment_score=n.sentiment_score,
            keywords=n.keywords,
            tickers=[t.symbol for t in n.tickers]
        ))
    
    return result


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    """Liste les sources disponibles."""
    sources = db.query(News.source).distinct().all()
    return [{'source': s[0], 'count': db.query(News).filter(News.source == s[0]).count()} for s in sources]


@router.get("/stats")
def news_stats(db: Session = Depends(get_db)):
    """Statistiques globales des news."""
    total = db.query(News).count()
    positive = db.query(News).filter(News.sentiment == 'positive').count()
    negative = db.query(News).filter(News.sentiment == 'negative').count()
    neutral = db.query(News).filter(News.sentiment == 'neutral').count()
    
    # News des dernières 24h
    last_24h = db.query(News).filter(
        News.published_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    return {
        'total': total,
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
        'last_24h': last_24h,
        'sentiment_ratio': {
            'positive': round(positive / total * 100, 1) if total > 0 else 0,
            'negative': round(negative / total * 100, 1) if total > 0 else 0,
            'neutral': round(neutral / total * 100, 1) if total > 0 else 0,
        }
    }


@router.get("/ticker/{symbol}")
def news_by_ticker(
    symbol: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """News spécifiques à un ticker."""
    news = db.query(News).join(NewsTicker).filter(
        NewsTicker.symbol == symbol.upper()
    ).order_by(desc(News.published_at)).limit(limit).all()
    
    return [
        {
            'id': str(n.id),
            'title': n.title,
            'summary': n.summary,
            'source': n.source,
            'published_at': n.published_at.isoformat(),
            'sentiment': n.sentiment,
            'sentiment_score': n.sentiment_score
        }
        for n in news
    ]


@router.post("/scrape")
async def trigger_scrape(db: Session = Depends(get_db)):
    """Déclenche manuellement un scraping."""
    from ..services.scraper import NewsScraper
    
    scraper = NewsScraper(db)
    try:
        count = await scraper.scrape_all()
        return {'message': f'{count} nouvelles news ajoutées'}
    finally:
        await scraper.close()


# ═══════════════════════════════════════════════════════
# ALERTES
# ═══════════════════════════════════════════════════════
@router.post("/alerts", response_model=NewsAlertOut, status_code=201)
def create_alert(
    payload: NewsAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée une alerte news."""
    alert = NewsAlert(
        user_id=current_user.id,
        ticker=payload.ticker,
        keyword=payload.keyword,
        sentiment_filter=payload.sentiment_filter,
        is_active=True
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/alerts", response_model=List[NewsAlertOut])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Liste les alertes de l'utilisateur."""
    return db.query(NewsAlert).filter(
        NewsAlert.user_id == current_user.id
    ).all()


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime une alerte."""
    alert = db.query(NewsAlert).filter(
        NewsAlert.id == alert_id,
        NewsAlert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(404, "Alerte introuvable")
    db.delete(alert)
    db.commit()
    return {'message': 'Alerte supprimée'}
