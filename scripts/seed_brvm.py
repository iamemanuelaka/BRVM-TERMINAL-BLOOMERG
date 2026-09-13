"""Seed script to populate the database with BRVM tickers and sample OHLCV data."""
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import Ticker, OHLCV

# Database URL (override with environment variable if needed)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://brvm:brvm@localhost:5432/brvm_terminal")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# BRVM tickers to seed
BRVM_TICKERS = [
    {"symbol": "SNTS", "name": "SONATEL SENEGAL", "sector": "Télécom", "country": "SN", "price": 17500},
    {"symbol": "ETIT", "name": "ECOBANK TRANS. INC.", "sector": "Banque", "country": "TG", "price": 19},
    {"symbol": "SIBC", "name": "SOCIETE IVOIRIENNE DE BANQUE", "sector": "Banque", "country": "CI", "price": 5400},
    {"symbol": "BOAB", "name": "BANK OF AFRICA BF", "sector": "Banque", "country": "BF", "price": 7100},
    {"symbol": "PALC", "name": "PALM CI", "sector": "Agro-industrie", "country": "CI", "price": 6800},
    {"symbol": "SAFC", "name": "SAFCA CI", "sector": "Finance", "country": "CI", "price": 215},
    {"symbol": "SGBC", "name": "SG CI", "sector": "Banque", "country": "CI", "price": 18500},
    {"symbol": "ORAC", "name": "ORANGE CI", "sector": "Télécom", "country": "CI", "price": 2500},
    {"symbol": "TTLC", "name": "TOTAL CI", "sector": "Distribution", "country": "CI", "price": 2400},
    {"symbol": "SLBC", "name": "SOLEIL CI", "sector": "Agro-industrie", "country": "CI", "price": 850},
    {"symbol": "NSBC", "name": "NESTLE CI", "sector": "Agro-industrie", "country": "CI", "price": 4200},
    {"symbol": "CIEC", "name": "CIE CI", "sector": "Utilities", "country": "CI", "price": 225},
]


def generate_ohlcv(base_price, days=365):
    """Generate realistic OHLCV data."""
    data = []
    price = base_price * 0.85
    now = datetime.now()

    for i in range(days, 0, -1):
        date = now - timedelta(days=i)
        # Skip weekends
        if date.weekday() >= 5:
            continue

        volatility = price * 0.018
        drift = (random.random() - 0.48) * volatility

        open_p = price
        close_p = open_p + drift
        high_p = max(open_p, close_p) + random.random() * volatility * 0.6
        low_p = min(open_p, close_p) - random.random() * volatility * 0.6
        volume = random.randint(5000, 20000)

        data.append({
            "date": date.replace(hour=0, minute=0, second=0, microsecond=0),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume
        })

        price = close_p

    return data


def seed_database():
    """Seed the database with BRVM tickers and OHLCV data."""
    print("🌱 Seeding database...")

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Seed tickers
        print(f"  → Inserting {len(BRVM_TICKERS)} tickers...")
        for t in BRVM_TICKERS:
            existing = db.query(Ticker).filter(Ticker.symbol == t["symbol"]).first()
            if not existing:
                ticker = Ticker(**t)
                db.add(ticker)

        db.commit()
        print(f"  ✓ Tickers inserted")

        # Seed OHLCV data
        print(f"  → Generating OHLCV data for each ticker...")
        for t in BRVM_TICKERS:
            symbol = t["symbol"]
            base_price = t["price"]

            # Check if data already exists
            existing_count = db.query(OHLCV).filter(OHLCV.symbol == symbol).count()
            if existing_count > 0:
                print(f"    ⚠ {symbol}: Data already exists, skipping")
                continue

            ohlcv_data = generate_ohlcv(base_price, days=365)
            for row in ohlcv_data:
                ohlcv = OHLCV(symbol=symbol, **row)
                db.add(ohlcv)

            print(f"    ✓ {symbol}: {len(ohlcv_data)} rows inserted")

        db.commit()
        print("\n✅ Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
