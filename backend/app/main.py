"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, market, predictions

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BRVM Terminal API",
    version="1.0.0",
    description="Backend API for BRVM Terminal - Bloomberg-like platform for BRVM market",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(market.router)
app.include_router(predictions.router)


@app.get("/")
def root():
    """Root endpoint - API information."""
    return {
        "service": "BRVM Terminal API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
