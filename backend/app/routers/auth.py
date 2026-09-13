"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, Token
import os

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"])
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@router.post("/register", response_model=Token)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "Username already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=pwd_context.hash(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=1)},
        SECRET,
        algorithm="HS256"
    )
    return {"access_token": token}


@router.post("/login", response_model=Token)
def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login and get JWT token."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=1)},
        SECRET,
        algorithm="HS256"
    )
    return {"access_token": token}
