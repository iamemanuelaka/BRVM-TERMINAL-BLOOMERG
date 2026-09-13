"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, market, predictions
from .routers import auth, market, predictions, news  # ← ajout

from .routers import auth, market, predictions, news, users # <-- Ajout de users


# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BRVM Terminal API",
    version="2.0.0",
    description="Backend API pour BRVM Terminal avec authentification",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production : restreindre
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(market.router)
app.include_router(predictions.router)
app.include_router(news.router)  
app.include_router(users.router) # <-- Ajout de l'inclusion

@app.get("/")
def root():
    return {
        "service": "BRVM Terminal API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
