"""Tâches Celery pour le scraping automatisé."""
from .celery_app import celery_app
from .services.scraper import NewsScraper
from .services.data_fetcher import DataFetcher
from .database import SessionLocal
import asyncio

@celery_app.task
def scrape_news_task():
    """Scrape les news toutes les 2 heures."""
    async def run():
        db = SessionLocal()
        scraper = NewsScraper(db)
        try:
            count = await scraper.scrape_all()
            return f"Scraped {count} news items"
        finally:
            await scraper.close()
            db.close()
    return asyncio.run(run())

@celery_app.task
def update_brvm_daily_task():
    """Met à jour les cours BRVM tous les jours à 18h."""
    async def run():
        db = SessionLocal()
        fetcher = DataFetcher()
        try:
            tickers = await fetcher.fetch_brvm_tickers()
            # Ici, tu pourrais ajouter la logique pour sauvegarder 'tickers' dans la DB OHLCV
            return f"Updated {len(tickers)} BRVM tickers"
        finally:
            await fetcher.close()
            db.close()
    return asyncio.run(run())
