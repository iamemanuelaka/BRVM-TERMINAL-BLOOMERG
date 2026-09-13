"""
Service unifié de récupération de données financières.
Sources : BRVM (officiel), Yahoo Finance (global/entraînement), Investing.com (fallback).
"""
import httpx
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from ..models import Ticker, OHLCV
from ..database import SessionLocal

# Mapping des valeurs BRVM vers leurs équivalents Yahoo Finance (pour l'entraînement)
# Cela permet aux étudiants d'avoir plus d'historique et de comparer avec des proxies régionaux
YAHOO_BRVM_MAPPING = {
    'SNTS': 'SNMMF.PA',       # Sonatel (proxy Euronext Paris)
    'ETIT': 'EBK.JO',          # Ecobank (Johannesburg Stock Exchange)
    'SIBC': 'SBK.JO',          # Standard Bank (proxy banque CI)
    'BOAB': 'ABG.JO',          # Absa Group (proxy BOA)
    'PALC': 'TCP.JO',          # Tongaat Hulett (proxy agro)
    'ORAC': 'ORAN.PA',         # Orange (Euronext Paris)
    'TTLC': 'FP.PA',           # TotalEnergies (Euronext Paris)
}

class DataFetcher:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*'
            }
        )

    async def close(self):
        await self.client.aclose()

    # ═══════════════════════════════════════════════════════
    # 1. DONNÉES BRVM (Scraping officiel)
    # ═══════════════════════════════════════════════════════
    async def fetch_brvm_tickers(self) -> List[Dict]:
        """Scrape la liste des valeurs et cours du jour depuis brvm.org"""
        try:
            # Note: L'URL peut changer, adapter le sélecteur si besoin
            response = await self.client.get('https://www.brvm.org/fr/cours-actions')
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            tickers = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    try:
                        symbol = cols[0].get_text(strip=True)
                        name = cols[1].get_text(strip=True)
                        # Nettoyage des nombres (ex: "17 500" -> 17500.0)
                        price_str = cols[2].get_text(strip=True).replace(' ', '').replace(',', '.')
                        var_str = cols[3].get_text(strip=True).replace(' ', '').replace(',', '.').replace('%', '')
                        vol_str = cols[4].get_text(strip=True).replace(' ', '')
                        
                        tickers.append({
                            'symbol': symbol,
                            'name': name,
                            'price': float(price_str) if price_str else 0.0,
                            'change_pct': float(var_str) if var_str else 0.0,
                            'volume': int(vol_str) if vol_str else 0,
                            'source': 'brvm'
                        })
                    except (ValueError, IndexError):
                        continue
            
            return tickers
        except Exception as e:
            print(f"[DataFetcher] Erreur BRVM: {e}")
            return []

    # ═══════════════════════════════════════════════════════
    # 2. YAHOO FINANCE (Idéal pour l'entraînement / Backtest)
    # ═══════════════════════════════════════════════════════
    def fetch_yahoo_ohlcv(self, symbol: str, period: str = "1y") -> List[Dict]:
        """Récupère l'historique OHLCV depuis Yahoo Finance."""
        try:
            # Utiliser le mapping BRVM si disponible, sinon le symbole tel quel
            yahoo_symbol = YAHOO_BRVM_MAPPING.get(symbol.upper(), symbol.upper())
            
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return []
            
            # Formater pour Lightweight Charts (YYYY-MM-DD)
            data = []
            for index, row in hist.iterrows():
                data.append({
                    'time': index.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            return data
        except Exception as e:
            print(f"[DataFetcher] Erreur Yahoo Finance ({symbol}): {e}")
            return []

    def fetch_yahoo_info(self, symbol: str) -> Optional[Dict]:
        """Récupère les fondamentaux d'une action (PER, Market Cap, etc.)"""
        try:
            yahoo_symbol = YAHOO_BRVM_MAPPING.get(symbol.upper(), symbol.upper())
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'sector': info.get('sector', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'trailing_pe': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 1.0),
                'source': 'yahoo'
            }
        except Exception as e:
            print(f"[DataFetcher] Erreur Yahoo Info ({symbol}): {e}")
            return None

    # ═══════════════════════════════════════════════════════
    # 3. INVESTING.COM (Fallback pour certaines actions africaines)
    # ═══════════════════════════════════════════════════════
    async def fetch_investing_ohlcv(self, symbol: str, days: int = 365) -> List[Dict]:
        """
        Scraping Investing.com (attention au Cloudflare, utiliser avec modération).
        Alternative recommandée : passer par yfinance avec le bon suffixe (.JO, .PA, etc.)
        """
        # Pour l'instant, on redirige vers Yahoo qui est plus stable pour l'entraînement
        # Si tu veux vraiment Investing.com, il faut utiliser la librairie `investpy` 
        # ou un scraper headless (Playwright) à cause de Cloudflare.
        return self.fetch_yahoo_ohlcv(symbol, period=f"{days}d")

    # ═══════════════════════════════════════════════════════
    # 4. ROUTEUR UNIFIÉ
    # ═══════════════════════════════════════════════════════
    async def get_ohlcv(self, symbol: str, days: int = 365) -> List[Dict]:
        """
        Récupère les données OHLCV en essayant plusieurs sources.
        Priorité : Base de données locale > Yahoo Finance > BRVM Scraper
        """
        db = SessionLocal()
        try:
            # 1. Essayer de récupérer depuis la base de données (si déjà scrapé)
            # (Code de requête SQLAlchemy à ajouter ici si tu utilises TimescaleDB)
            
            # 2. Fallback sur Yahoo Finance (le plus fiable pour l'entraînement)
            data = self.fetch_yahoo_ohlcv(symbol, period=f"{days}d")
            if data:
                return data
            
            # 3. Fallback sur Investing.com
            data = await self.fetch_investing_ohlcv(symbol, days)
            if data:
                return data
                
            return []
        finally:
            db.close()

    async def get_ticker_info(self, symbol: str) -> Dict:
        """Récupère les infos d'un ticker (nom, secteur, PER, etc.)"""
        info = self.fetch_yahoo_info(symbol)
        if info:
            return info
        
        # Fallback sur les données BRVM si Yahoo échoue
        brvm_tickers = await self.fetch_brvm_tickers()
        for t in brvm_tickers:
            if t['symbol'] == symbol.upper():
                return {
                    'symbol': t['symbol'],
                    'name': t['name'],
                    'price': t['price'],
                    'change_pct': t['change_pct'],
                    'volume': t['volume'],
                    'source': 'brvm'
                }
        
        return {'symbol': symbol, 'name': symbol, 'source': 'unknown'}
