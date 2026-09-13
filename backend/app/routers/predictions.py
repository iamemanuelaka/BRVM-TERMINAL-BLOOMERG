"""Predictions endpoints with auth."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional

from ..database import get_db
from ..models import Prediction, Ticker, User, Profile
from ..schemas import PredictionCreate, PredictionOut
from ..routers.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


@router.post("/", response_model=PredictionOut, status_code=201)
def create_prediction(
    payload: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Crée une prédiction (authentification optionnelle pour MVP)."""
    # Vérifier que le ticker existe
    ticker = db.query(Ticker).filter(Ticker.symbol == payload.symbol.upper()).first()
    if not ticker:
        raise HTTPException(404, f"Ticker {payload.symbol} introuvable")

    expires_at = datetime.utcnow() + timedelta(days=payload.horizon_days)

    # Si utilisateur connecté, utiliser son ID ; sinon ID anonyme
    user_id = current_user.id if current_user else None

    pred = Prediction(
        user_id=user_id,
        author_name=payload.author_name,
        symbol=payload.symbol.upper(),
        direction=payload.direction,
        current_price=payload.current_price,
        target_price=payload.target_price,
        stop_loss=payload.stop_loss,
        confidence=payload.confidence,
        horizon_days=payload.horizon_days,
        thesis=payload.thesis,
        tags=payload.tags,
        expires_at=expires_at,
    )
    db.add(pred)
    
    # Mettre à jour le compteur du profil si utilisateur connecté
    if current_user:
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
        if profile:
            profile.total_predictions = (profile.total_predictions or 0) + 1
            db.commit()
    
    db.commit()
    db.refresh(pred)
    return pred


@router.get("/", response_model=List[PredictionOut])
def list_predictions(
    status: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Liste les prédictions avec filtres."""
    q = db.query(Prediction)
    if status:
        q = q.filter(Prediction.status == status)
    if symbol:
        q = q.filter(Prediction.symbol == symbol.upper())
    if author:
        q = q.filter(Prediction.author_name.ilike(f"%{author}%"))
    return q.order_by(desc(Prediction.created_at)).limit(limit).all()


@router.get("/stats")
def prediction_stats(db: Session = Depends(get_db)):
    """Statistiques globales des prédictions."""
    total = db.query(Prediction).count()
    active = db.query(Prediction).filter(Prediction.status == "active").count()
    scored = db.query(Prediction).filter(Prediction.status == "scored").all()

    hits = sum(1 for p in scored if p.hit_target)
    hit_rate = (hits / len(scored) * 100) if scored else 0

    return {
        "total": total,
        "active": active,
        "scored": len(scored),
        "hit_rate_pct": round(hit_rate, 2),
    }
