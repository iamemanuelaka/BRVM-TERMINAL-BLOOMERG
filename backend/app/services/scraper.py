"""Scraper pour récupérer les news de RichBourse, Sika Finance, BRVM et BCEAO."""
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
import asyncio

from ..models import News, NewsTicker, Ticker
from ..services.sentiment import analyze_sentiment, extract_tickers


class NewsScraper:
    """Scrape les news depuis plusieurs sources."""
    
    def __init__(self, db):
        self.db = db
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        )
    
    async def close(self):
        await self.client.aclose()
    
    async def scrape_all(self) -> int:
        """Scrape toutes les sources et retourne le nombre de news ajoutées."""
        total = 0
        
        # Sources à scraper
        scrapers = [
            ('RichBourse', self.scrape_richbourse),
            ('Sika Finance', self.scrape_sika_finance),
            ('BRVM', self.scrape_brvm),
            ('BCEAO', self.scrape_bceao),
        ]
        
        for source_name, scraper in scrapers:
            try:
                print(f"[Scraper] Scraping {source_name}...")
                count = await scraper()
                total += count
                print(f"[Scraper] ✓ {source_name}: {count} news ajoutées")
            except Exception as e:
                print(f"[Scraper] ✗ {source_name}: {e}")
        
        return total
    
    # ═══════════════════════════════════════════════════════
    # RICHBOURSE
    # ═══════════════════════════════════════════════════════
    async def scrape_richbourse(self) -> int:
        """Scrape RichBourse (richbourse.com)."""
        try:
            response = await self.client.get('https://richbourse.com/actualites/')
            if response.status_code != 200:
                print(f"[RichBourse] HTTP {response.status_code}")
                return 0
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver les articles (structure typique WordPress)
            articles = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'post|article|entry'))
            
            if not articles:
                # Fallback: chercher les liens avec titres
                articles = soup.find_all('h2', class_=re.compile(r'entry-title|post-title'))
            
            count = 0
            known_tickers = [t.symbol for t in self.db.query(Ticker).all()]
            
            for article in articles[:15]:  # Limiter à 15 articles
                try:
                    # Extraire le titre
                    title_tag = article.find(['h2', 'h3', 'a'], class_=re.compile(r'title|heading')) or article.find('a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # Extraire le lien
                    link_tag = title_tag if title_tag.name == 'a' else title_tag.find('a')
                    source_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''
                    
                    # Extraire le contenu/résumé
                    content_tag = article.find(['p', 'div'], class_=re.compile(r'excerpt|summary|content'))
                    content = content_tag.get_text(strip=True) if content_tag else ''
                    
                    # Extraire la date
                    date_tag = article.find(['time', 'span'], class_=re.compile(r'date|time|published'))
                    published_at = self.parse_date(date_tag.get_text(strip=True) if date_tag else '')
                    
                    # Vérifier si déjà existant
                    existing = self.db.query(News).filter(
                        News.title == title,
                        News.source == 'richbourse'
                    ).first()
                    if existing:
                        continue
                    
                    # Analyse de sentiment
                    full_text = title + ' ' + content
                    sentiment, score, keywords = analyze_sentiment(full_text)
                    
                    # Extraction des tickers
                    mentioned_tickers = extract_tickers(full_text, known_tickers)
                    
                    # Créer la news
                    news = News(
                        title=title,
                        content=content,
                        summary=content[:200] + '...' if len(content) > 200 else content,
                        source='richbourse',
                        source_url=source_url,
                        published_at=published_at,
                        sentiment=sentiment,
                        sentiment_score=score,
                        keywords=keywords
                    )
                    self.db.add(news)
                    self.db.flush()
                    
                    # Associer les tickers
                    for ticker in mentioned_tickers:
                        nt = NewsTicker(news_id=news.id, symbol=ticker, relevance=1.0)
                        self.db.add(nt)
                    
                    count += 1
                    
                except Exception as e:
                    print(f"[RichBourse] Erreur article: {e}")
                    continue
            
            if count > 0:
                self.db.commit()
            
            return count
            
        except Exception as e:
            print(f"[RichBourse] Erreur globale: {e}")
            return 0
    
    # ═══════════════════════════════════════════════════════
    # SIKA FINANCE
    # ═══════════════════════════════════════════════════════
    async def scrape_sika_finance(self) -> int:
        """Scrape Sika Finance (sika.finance)."""
        try:
            response = await self.client.get('https://sika.finance/actualites')
            if response.status_code != 200:
                print(f"[Sika Finance] HTTP {response.status_code}")
                return 0
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les articles
            articles = soup.find_all('div', class_=re.compile(r'news-item|article|post'))
            
            if not articles:
                articles = soup.find_all('article')
            
            count = 0
            known_tickers = [t.symbol for t in self.db.query(Ticker).all()]
            
            for article in articles[:15]:
                try:
                    # Titre
                    title_tag = article.find(['h2', 'h3', 'h4', 'a'])
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # Lien
                    link_tag = title_tag if title_tag.name == 'a' else title_tag.find('a')
                    source_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''
                    
                    # Contenu
                    content_tag = article.find(['p', 'div'], class_=re.compile(r'excerpt|summary|description'))
                    content = content_tag.get_text(strip=True) if content_tag else ''
                    
                    # Date
                    date_tag = article.find(['time', 'span'], class_=re.compile(r'date|time'))
                    published_at = self.parse_date(date_tag.get_text(strip=True) if date_tag else '')
                    
                    # Vérifier existence
                    existing = self.db.query(News).filter(
                        News.title == title,
                        News.source == 'sika_finance'
                    ).first()
                    if existing:
                        continue
                    
                    # Analyse
                    full_text = title + ' ' + content
                    sentiment, score, keywords = analyze_sentiment(full_text)
                    mentioned_tickers = extract_tickers(full_text, known_tickers)
                    
                    # Créer
                    news = News(
                        title=title,
                        content=content,
                        summary=content[:200] + '...' if len(content) > 200 else content,
                        source='sika_finance',
                        source_url=source_url,
                        published_at=published_at,
                        sentiment=sentiment,
                        sentiment_score=score,
                        keywords=keywords
                    )
                    self.db.add(news)
                    self.db.flush()
                    
                    for ticker in mentioned_tickers:
                        nt = NewsTicker(news_id=news.id, symbol=ticker, relevance=1.0)
                        self.db.add(nt)
                    
                    count += 1
                    
                except Exception as e:
                    print(f"[Sika Finance] Erreur article: {e}")
                    continue
            
            if count > 0:
                self.db.commit()
            
            return count
            
        except Exception as e:
            print(f"[Sika Finance] Erreur globale: {e}")
            return 0
    
    # ═══════════════════════════════════════════════════════
    # BRVM
    # ═══════════════════════════════════════════════════════
    async def scrape_brvm(self) -> int:
        """Scrape BRVM (brvm.org)."""
        try:
            response = await self.client.get('https://www.brvm.org/fr/actualites')
            if response.status_code != 200:
                print(f"[BRVM] HTTP {response.status_code}")
                return 0
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les actualités
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'news|article|item'))
            
            if not articles:
                articles = soup.find_all('h3') or soup.find_all('h4')
            
            count = 0
            known_tickers = [t.symbol for t in self.db.query(Ticker).all()]
            
            for article in articles[:15]:
                try:
                    # Titre
                    title_tag = article.find(['h2', 'h3', 'h4', 'a']) or article
                    title = title_tag.get_text(strip=True)
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Lien
                    link_tag = article.find('a')
                    source_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''
                    if source_url and not source_url.startswith('http'):
                        source_url = 'https://www.brvm.org' + source_url
                    
                    # Contenu
                    content_tag = article.find(['p', 'div'], class_=re.compile(r'content|excerpt|summary'))
                    content = content_tag.get_text(strip=True) if content_tag else title
                    
                    # Date
                    date_tag = article.find(['time', 'span'], class_=re.compile(r'date'))
                    published_at = self.parse_date(date_tag.get_text(strip=True) if date_tag else '')
                    
                    # Vérifier existence
                    existing = self.db.query(News).filter(
                        News.title == title,
                        News.source == 'brvm'
                    ).first()
                    if existing:
                        continue
                    
                    # Analyse
                    full_text = title + ' ' + content
                    sentiment, score, keywords = analyze_sentiment(full_text)
                    mentioned_tickers = extract_tickers(full_text, known_tickers)
                    
                    # Créer
                    news = News(
                        title=title,
                        content=content,
                        summary=content[:200] + '...' if len(content) > 200 else content,
                        source='brvm',
                        source_url=source_url,
                        published_at=published_at,
                        sentiment=sentiment,
                        sentiment_score=score,
                        keywords=keywords
                    )
                    self.db.add(news)
                    self.db.flush()
                    
                    for ticker in mentioned_tickers:
                        nt = NewsTicker(news_id=news.id, symbol=ticker, relevance=1.0)
                        self.db.add(nt)
                    
                    count += 1
                    
                except Exception as e:
                    print(f"[BRVM] Erreur article: {e}")
                    continue
            
            if count > 0:
                self.db.commit()
            
            return count
            
        except Exception as e:
            print(f"[BRVM] Erreur globale: {e}")
            return 0
    
    # ═══════════════════════════════════════════════════════
    # BCEAO
    # ═══════════════════════════════════════════════════════
    async def scrape_bceao(self) -> int:
        """Scrape BCEAO (bceao.int)."""
        try:
            response = await self.client.get('https://www.bceao.int/fr/actualites-et-publications/actualites')
            if response.status_code != 200:
                print(f"[BCEAO] HTTP {response.status_code}")
                return 0
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les actualités
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'news|article|item|publication'))
            
            if not articles:
                articles = soup.find_all('h3') or soup.find_all('h4')
            
            count = 0
            known_tickers = [t.symbol for t in self.db.query(Ticker).all()]
            
            for article in articles[:15]:
                try:
                    # Titre
                    title_tag = article.find(['h2', 'h3', 'h4', 'a']) or article
                    title = title_tag.get_text(strip=True)
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Lien
                    link_tag = article.find('a')
                    source_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''
                    if source_url and not source_url.startswith('http'):
                        source_url = 'https://www.bceao.int' + source_url
                    
                    # Contenu
                    content_tag = article.find(['p', 'div'], class_=re.compile(r'content|excerpt|summary'))
                    content = content_tag.get_text(strip=True) if content_tag else title
                    
                    # Date
                    date_tag = article.find(['time', 'span'], class_=re.compile(r'date'))
                    published_at = self.parse_date(date_tag.get_text(strip=True) if date_tag else '')
                    
                    # Vérifier existence
                    existing = self.db.query(News).filter(
                        News.title == title,
                        News.source == 'bceao'
                    ).first()
                    if existing:
                        continue
                    
                    # Analyse
                    full_text = title + ' ' + content
                    sentiment, score, keywords = analyze_sentiment(full_text)
                    mentioned_tickers = extract_tickers(full_text, known_tickers)
                    
                    # Créer
                    news = News(
                        title=title,
                        content=content,
                        summary=content[:200] + '...' if len(content) > 200 else content,
                        source='bceao',
                        source_url=source_url,
                        published_at=published_at,
                        sentiment=sentiment,
                        sentiment_score=score,
                        keywords=keywords
                    )
                    self.db.add(news)
                    self.db.flush()
                    
                    for ticker in mentioned_tickers:
                        nt = NewsTicker(news_id=news.id, symbol=ticker, relevance=1.0)
                        self.db.add(nt)
                    
                    count += 1
                    
                except Exception as e:
                    print(f"[BCEAO] Erreur article: {e}")
                    continue
            
            if count > 0:
                self.db.commit()
            
            return count
            
        except Exception as e:
            print(f"[BCEAO] Erreur globale: {e}")
            return 0
    
    # ═══════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════
    def parse_date(self, date_str: str) -> datetime:
        """Parse une date depuis différents formats."""
        if not date_str:
            return datetime.now(timezone.utc)
        
        # Nettoyer la chaîne
        date_str = date_str.strip()
        
        # Formats courants
        formats = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # Si aucun format ne match, retourner maintenant
        return datetime.now(timezone.utc)
