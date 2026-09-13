"""Authentication endpoints with JWT."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import os

from ..database import get_db
from ..models import User, Profile, APIKey
from ..schemas import (
    UserCreate, UserLogin, UserOut, Token, TokenData,
    ProfileOut, ProfileUpdate, APIKeyCreate, APIKeyOut
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ═══════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Récupère l'utilisateur courant via JWT ou API Key."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Essayer avec JWT Bearer
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            raise credentials_exception
        return user

    # 2. Essayer avec API Key
    if x_api_key:
        api_key = db.query(APIKey).filter(
            APIKey.key == x_api_key,
            APIKey.is_active == True
        ).first()
        if api_key is None:
            raise credentials_exception
        
        # Mettre à jour last_used_at
        api_key.last_used_at = datetime.utcnow()
        db.commit()
        
        user = db.query(User).filter(User.id == api_key.user_id).first()
        if user is None or not user.is_active:
            raise credentials_exception
        return user

    raise credentials_exception


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Récupère l'utilisateur courant si authentifié, sinon None."""
    try:
        return await get_current_user(token, x_api_key, db)
    except HTTPException:
        return None


# ═══════════════════════════════════════════════════════
# ENDPOINTS AUTH
# ═══════════════════════════════════════════════════════
@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Inscription d'un nouvel utilisateur."""
    # Vérifier username unique
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "Ce nom d'utilisateur est déjà pris")
    
    # Vérifier email unique
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Cet email est déjà utilisé")

    # Créer l'utilisateur
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Créer le profil public
    profile = Profile(
        user_id=user.id,
        display_name=payload.username,
        is_public=True
    )
    db.add(profile)
    db.commit()

    # Générer le token
    token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": token,
        "user": UserOut.model_validate(user)
    }


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Connexion et obtention d'un JWT."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides"
        )
    
    if not user.is_active:
        raise HTTPException(400, "Compte désactivé")

    token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": token,
        "user": UserOut.model_validate(user)
    }


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Récupère l'utilisateur courant."""
    return current_user


@router.get("/me/profile", response_model=ProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Récupère le profil de l'utilisateur courant."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        # Créer un profil par défaut
        profile = Profile(user_id=current_user.id, display_name=current_user.username)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    result = ProfileOut.model_validate(profile)
    result.username = current_user.username
    return result


@router.put("/me/profile", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour le profil de l'utilisateur courant."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.is_public is not None:
        profile.is_public = payload.is_public
    
    db.commit()
    db.refresh(profile)
    
    result = ProfileOut.model_validate(profile)
    result.username = current_user.username
    return result


# ═══════════════════════════════════════════════════════
# API KEYS (pour les bots)
# ═══════════════════════════════════════════════════════
@router.post("/api-keys", response_model=APIKeyOut, status_code=201)
def create_api_key(
    payload: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée une nouvelle API key pour l'utilisateur."""
    # Limiter à 5 clés par utilisateur
    count = db.query(APIKey).filter(APIKey.user_id == current_user.id).count()
    if count >= 5:
        raise HTTPException(400, "Maximum 5 clés API par utilisateur")
    
    api_key = APIKey(
        user_id=current_user.id,
        key=f"brvm_{secrets.token_urlsafe(32)}",
        name=payload.name
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


@router.get("/api-keys", response_model=list[APIKeyOut])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Liste les API keys de l'utilisateur."""
    return db.query(APIKey).filter(APIKey.user_id == current_user.id).all()


@router.delete("/api-keys/{key_id}")
def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime une API key."""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    if not api_key:
        raise HTTPException(404, "Clé API introuvable")
    
    db.delete(api_key)
    db.commit()
    return {"message": "Clé API supprimée"}


# ═══════════════════════════════════════════════════════
# PROFILS PUBLICS (pour le leaderboard)
# ═══════════════════════════════════════════════════════
@router.get("/profiles/{username}", response_model=ProfileOut)
def get_public_profile(username: str, db: Session = Depends(get_db)):
    """Récupère un profil public."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile or not profile.is_public:
        raise HTTPException(404, "Profil non trouvé ou privé")
    
    result = ProfileOut.model_validate(profile)
    result.username = user.username
    return result


@router.get("/leaderboard")
def get_leaderboard(
    period: str = "ALL",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Récupère le leaderboard des traders."""
    from ..models import Prediction
    from sqlalchemy import desc
    
    # Calculer les scores par utilisateur
    results = db.query(
        Profile.user_id,
        Profile.display_name,
        Profile.composite_score,
        Profile.total_predictions,
        Profile.hit_rate,
        User.username
    ).join(User).filter(
        Profile.is_public == True,
        Profile.total_predictions > 0
    ).order_by(desc(Profile.composite_score)).limit(limit).all()
    
    return [
        {
            "username": r.username,
            "display_name": r.display_name or r.username,
            "composite_score": r.composite_score or 0,
            "total_predictions": r.total_predictions or 0,
            "hit_rate": r.hit_rate or 0
        }
        for r in results
    ]
