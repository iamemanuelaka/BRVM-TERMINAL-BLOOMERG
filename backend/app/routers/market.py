from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..services.data_fetcher import DataFetcher

router = APIRouter(prefix="/api/v1/market", tags=["market"])

# Instance unique du fetcher
fetcher = DataFetcher()

@router.on_event("shutdown")
async def shutdown_event():
    await fetcher.close()

@router.get("/tickers")
async def list_tickers():
    """Récupère la liste des tickers (BRVM en priorité, avec fallback)."""
    # 1. Essayer de scraper la BRVM en direct
    brvm_data = await fetcher.fetch_brvm_tickers()
    if brvm_data:
        return brvm_data
    
    # 2. Fallback sur une liste statique enrichie via Yahoo
    fallback_symbols = ['SNTS', 'ETIT', 'SIBC', 'BOAB', 'PALC', 'ORAC', 'TTLC', 'AAPL', '^GSPC', 'EURUSD=X']
    results = []
    for sym in fallback_symbols:
        info = await fetcher.get_ticker_info(sym)
        if info:
            results.append(info)
    return results

@router.get("/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    days: int = Query(365, ge=1, le=3650, description="Nombre de jours d'historique")
):
    """
    Récupère l'historique OHLCV pour un symbole.
    Utilise Yahoo Finance pour l'entraînement (données riches) ou la BRVM.
    """
    data = await fetcher.get_ohlcv(symbol.upper(), days=days)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour {symbol}")
    
    return data

@router.get("/{symbol}/info")
async def get_ticker_info(symbol: str):
    """Récupère les fondamentaux d'une valeur (PER, Market Cap, Secteur, etc.)."""
    info = await fetcher.get_ticker_info(symbol.upper())
    if info.get('source') == 'unknown':
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} introuvable")
    return info
