"""Endpoints pour les profils utilisateurs publics."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..models import User, Profile, Prediction
from ..schemas import ProfileOut, PredictionOut

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{username}/profile", response_model=ProfileOut)
def get_public_profile(username: str, db: Session = Depends(get_db)):
    """Récupère le profil public d'un utilisateur."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile or not profile.is_public:
        raise HTTPException(status_code=404, detail="Profil non trouvé ou privé")
    
    # Calculer les stats à la volée si nécessaire
    total_preds = db.query(Prediction).filter(
        Prediction.user_id == user.id,
        Prediction.status == 'scored'
    ).count()
    
    hit_preds = db.query(Prediction).filter(
        Prediction.user_id == user.id,
        Prediction.status == 'scored',
        Prediction.hit_target == True
    ).count()
    
    hit_rate = (hit_preds / total_preds * 100) if total_preds > 0 else 0.0
    
    # Mettre à jour le profil avec les dernières stats
    profile.total_predictions = total_preds
    profile.hit_rate = hit_rate
    db.commit()
    
    result = ProfileOut.model_validate(profile)
    result.username = user.username
    return result


@router.get("/{username}/predictions", response_model=List[PredictionOut])
def get_user_predictions(
    username: str,
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Récupère l'historique des prédictions d'un utilisateur."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    q = db.query(Prediction).filter(Prediction.user_id == user.id)
    if status:
        q = q.filter(Prediction.status == status)
    
    return q.order_by(desc(Prediction.created_at)).limit(limit).all()
